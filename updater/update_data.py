"""SIP Compass local updater. Python 3.10+, standard library only.

NAV history: MFapi (a third-party distributor of AMFI NAVs).
Daily NAV, Direct total TER and scheme AUM: AMFI's public disclosures.
No account, holding, goal or browser data is read or transmitted.
"""
from __future__ import annotations
import argparse, concurrent.futures, contextlib, datetime as dt, hashlib, json
import math, os, re, sqlite3, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AMFI = 'https://www.amfiindia.com'
TER_URL = AMFI + '/api/populate-te-rdata-revised'
AUM_URL = AMFI + '/gateway/pollingsebi/api/amfi/'
NAV_URL = 'https://portal.amfiindia.com/spages/NAVAll.txt'
HISTORY_URL = 'https://api.mfapi.in/mf'
PREFIX = 'window.SIP_LOCAL_DATA = '
SCHEMA = 1

def today():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()

def iso(value):
    if not isinstance(value, str):
        raise ValueError('Missing date')
    for fmt in ('%Y-%m-%d', '%d-%b-%Y', '%d-%m-%Y'):
        try:
            d = dt.datetime.strptime(value[:10] if fmt == '%Y-%m-%d' else value, fmt).date()
            if d > today() or d.year < 1990:
                raise ValueError('Out-of-range date')
            return d.isoformat()
        except ValueError:
            pass
    raise ValueError('Invalid or future date: ' + value)

def number(value, *, maximum=None, positive=False):
    if value is None or isinstance(value, bool) or str(value).strip() in ('', '-', '--', 'NA', 'N/A'):
        raise ValueError('Missing number')
    n = float(str(value).replace(',', ''))
    if not math.isfinite(n) or n < 0 or (positive and n == 0) or (maximum is not None and n > maximum):
        raise ValueError('Invalid number')
    return n

def request(url, body=None, *, method=None, raw=False):
    headers = {'User-Agent': 'Mozilla/5.0 (SIP-Compass local research updater)',
               'Accept': 'application/json,text/plain,*/*', 'Referer': AMFI + '/polling/amfi/fund-performance',
               'Origin': AMFI}
    data = None if body is None else json.dumps(body).encode('utf-8')
    if data is not None:
        headers['Content-Type'] = 'application/json'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=35) as response:
                content = response.read(50_000_001)
                if len(content) > 50_000_000:
                    raise ValueError('Response too large')
            text = content.decode('utf-8-sig')
            return text if raw else json.loads(text)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.6 * (attempt + 1))

def atomic_text(path, text):
    path = Path(path)
    temp = path.with_name(path.name + '.tmp')
    try:
        with temp.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def norm(name):
    """Exact normalized name, never fuzzy or substring matching."""
    name = str(name).lower().replace('&', ' and ')
    name = re.sub(r'\((?:formerly|erstwhile|existing|the scheme has)[^)]*\)', '', name)
    name = re.sub(r'\b(?:direct|plan b\s*\(direct\)).*$', '', name)
    name = re.sub(r'\b(?:growth)(?:\s+option)?\s*$', '', name)
    return re.sub(r'[^a-z0-9]', '', name)

def candidate(row, rules):
    name = row.get('schemeName', '')
    if not re.search('direct', name, re.I) or not re.search('growth', name, re.I):
        return False
    if re.search(r'idcw|dividend|bonus|payout|reinvest|fmp|series|interval|fixed term|closed|unclaimed|retail plan|institutional', name, re.I):
        return False
    if re.search('segregat', name, re.I) and not re.search('existing|the scheme has|number of', name, re.I):
        return False
    return any(re.search(c['include'], name, re.I) and not re.search(c['exclude'], name, re.I) for c in rules['categories'])

def parse_daily(text):
    header = None
    out = {}
    for line in text.splitlines():
        cells = [x.strip() for x in line.split(';')]
        if cells and cells[0] == 'Scheme Code':
            header = {name: i for i, name in enumerate(cells)}
            for key in ('Scheme Code', 'Scheme Name', 'Net Asset Value', 'Date'):
                if key not in header:
                    raise ValueError('AMFI NAV header changed: ' + key)
            continue
        if not cells or not cells[0].isdigit():
            continue
        if not header:
            raise ValueError('NAV rows without header')
        try:
            code = str(int(cells[header['Scheme Code']]))
            point = [iso(cells[header['Date']]), number(cells[header['Net Asset Value']], positive=True)]
            row = {'point': point, 'name': cells[header['Scheme Name']]}
            if code in out and out[code] != row:
                raise ValueError('Conflicting NAV code')
            out[code] = row
        except (IndexError, ValueError) as exc:
            # Missing NAV disclosures can occur; never manufacture a price.
            if isinstance(exc, IndexError) or 'Conflicting' in str(exc):
                raise
    if not header or not out:
        raise ValueError('No valid daily NAV rows')
    return out

def parse_history(j, code):
    if not isinstance(j, dict) or not isinstance(j.get('meta'), dict) or not isinstance(j.get('data'), list):
        raise ValueError('History schema changed')
    meta = j['meta']
    if str(meta.get('scheme_code')) != str(code):
        raise ValueError('History scheme code mismatch')
    if not meta.get('scheme_name') or not meta.get('scheme_category'):
        raise ValueError('History metadata missing')
    points = {}
    rejected = 0
    for row in j['data']:
        date = iso(row['date'])
        try:
            nav = number(row['nav'], positive=True)
        except ValueError:
            rejected += 1
            continue
        if date in points and points[date] != nav:
            raise ValueError('Conflicting historical NAV')
        points[date] = nav
    if not points:
        raise ValueError('Empty history')
    return {'meta': {**meta, 'sip_rejected_nav_rows': rejected}, 'points': sorted(points.items())}

def merge_history(old, new):
    if not old:
        return new
    a = dict(old['points'])
    a.update(dict(new['points']))
    return {'meta': new['meta'], 'points': sorted(a.items())}

def get_ter(month, mf_id='All'):
    rows, seen = [], set()
    page, count, total = 1, None, None
    while count is None or page <= count:
        url = TER_URL + '?' + urllib.parse.urlencode({'MF_ID': mf_id, 'Month': month, 'strCat': '-1', 'strType': '-1', 'page': page, 'pageSize': 100})
        j = request(url)
        if not isinstance(j, dict) or not isinstance(j.get('data'), list) or not isinstance(j.get('meta'), dict):
            raise ValueError('TER schema changed')
        meta = j['meta']
        new_count, new_total = int(meta['pageCount']), int(meta['total'])
        if int(meta['page']) != page or new_count > 2000 or (count is not None and (new_count != count or new_total != total)):
            raise ValueError('TER pagination changed during download; retry later')
        count, total = new_count, new_total
        digest = hashlib.sha256(json.dumps(j['data'], sort_keys=True).encode()).hexdigest()
        if j['data'] and digest in seen:
            raise ValueError('TER repeated page')
        seen.add(digest)
        rows.extend(j['data'])
        if page % 25 == 0:
            print(f'  TER pages {page}/{count}', flush=True)
        page += 1
    if len(rows) != total:
        raise ValueError('Incomplete TER download')
    return rows

def get_ter_with_fallback(db):
    rows = get_ter(today().strftime('%m-%Y'))
    ids = {str(r.get('MF_ID')) for r in rows}
    houses = {norm(json.loads(payload)['meta'].get('fund_house', '')) for (payload,) in db.execute('SELECT payload FROM histories')}
    page = request(AMFI + '/ter-of-mf-schemes', raw=True).replace('\\"', '"')
    mappings = dict(re.findall(r'"mfId":"(\d+)","mfName":"([^"]+)"', page))
    if not mappings:
        raise ValueError('AMFI fund-house list changed; cannot verify TER coverage')
    previous = (today().replace(day=1) - dt.timedelta(days=1)).strftime('%m-%Y')
    for mf_id, name in mappings.items():
        if norm(name) in houses and mf_id not in ids:
            print(f'  No current-month TER for {name}; checking {previous}.', flush=True)
            rows.extend(get_ter(previous, mf_id))
    return rows

def ter_index(rows):
    by_id = {}
    conflicts = set()
    for row in rows:
        try:
            key = str(row['NSDLSchemeCode']).strip()
            if not key or key == 'None':
                continue
            date = iso(row['TER_Date'])
            value = number(row['D_TER'], maximum=10)
            entry = {'value': value, 'date': date, 'name': row['Scheme_Name'], 'id': key,
                     'category': row.get('SchemeCat_Desc', ''), 'source': AMFI + '/ter-of-mf-schemes'}
        except (KeyError, ValueError):
            continue
        old = by_id.get(key)
        if not old or date > old['date']:
            by_id[key] = entry
            conflicts.discard(key)
        elif date == old['date'] and (value != old['value'] or norm(entry['name']) != norm(old['name'])):
            conflicts.add(key)
    result = {}
    for key, row in by_id.items():
        if key not in conflicts:
            result.setdefault(norm(row['name']), []).append(row)
    return result

def amfi_post(path, payload=None):
    j = request(AUM_URL + path, payload, method='POST')
    if not isinstance(j, dict) or j.get('validationStatus') != 'SUCCESS':
        raise ValueError('AUM endpoint rejected request')
    return j['data']

def get_aum():
    filters = amfi_post('fundperformancefilters')
    report = filters['reportDate']
    date = iso(report)
    rows = []
    for cat in filters['investmentTypeList']:
        subs = amfi_post('getsubcategory', {'category': cat['id']})
        for sub in subs:
            data = amfi_post('fundperformance', {'maturityType': 1, 'category': cat['id'],
                'subCategory': sub['id'], 'mfid': 0, 'reportDate': report})
            if not isinstance(data, list):
                raise ValueError('AUM table changed')
            for row in data:
                rows.append({**row, '_reportDate': date, '_category': sub['name']})
        print(f"  AUM: {cat['name']} checked", flush=True)
    if not rows:
        raise ValueError('Empty AUM download')
    return rows

def aum_index(rows):
    result = {}
    for row in rows:
        try:
            entry = {'value': number(row['dailyAUM'], positive=True), 'date': iso(row['_reportDate']),
                'name': row['schemeName'], 'category': row['_category'],
                'qualification': str(row.get('specialCharAum') or ''),
                'source': AMFI + '/otherdata/fund-performance'}
        except (KeyError, ValueError):
            continue
        result.setdefault(norm(entry['name']), []).append(entry)
    return result

def match_facts(catalog, ter, aum):
    out = {}
    keys = {}
    for row in catalog:
        keys.setdefault(norm(row['schemeName']), set()).add(str(row['schemeCode']))
    for row in catalog:
        code, key = str(row['schemeCode']), norm(row['schemeName'])
        rec = {'name': row['schemeName'], 'match': 'exact normalized name; unique in both datasets', 'ter': None, 'aum': None}
        if len(keys[key]) != 1:
            rec['match'] = 'ambiguous NAV scheme name; withheld'
        else:
            for kind, index in [('ter', ter), ('aum', aum)]:
                matches = index.get(key, [])
                if len(matches) == 1:
                    rec[kind] = matches[0]
        out[code] = rec
    return out

def connect(path):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE IF NOT EXISTS histories (code TEXT PRIMARY KEY, payload TEXT NOT NULL, checked TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, payload TEXT NOT NULL)')
    return db

def state_get(db, key, default=None):
    row = db.execute('SELECT payload FROM state WHERE key=?', (key,)).fetchone()
    return json.loads(row[0]) if row else default

def state_set(db, key, value):
    db.execute('INSERT OR REPLACE INTO state VALUES (?,?)', (key, json.dumps(value, ensure_ascii=False, allow_nan=False)))
    db.commit()

def export_bundle(db, catalog, facts, report, path, publish=True):
    wanted = {str(r['schemeCode']) for r in catalog}
    histories = {code: json.loads(payload) for code, payload in db.execute('SELECT code,payload FROM histories') if code in wanted}
    if '120716' not in histories:
        raise ValueError('Benchmark history unavailable; previous data.js retained')
    payload = {'schema': SCHEMA, 'built': dt.datetime.now(dt.timezone.utc).isoformat(),
        'catalog': catalog, 'histories': histories, 'facts': facts, 'report': report,
        'sources': {'history': HISTORY_URL, 'daily': NAV_URL, 'ter': TER_URL, 'aum': AUM_URL + 'fundperformance'}}
    serialized = json.dumps(payload, ensure_ascii=True, separators=(',', ':'), allow_nan=False)
    # Assignment only, with JSON escaping. Never evaluate downloaded source code.
    if publish:
        atomic_text(path, PREFIX + serialized + ';\n')
    return len(histories), len(serialized)

def run(args):
    root = Path(args.output).resolve()
    verify = getattr(args, 'verify_only', False)
    lock = None
    if not verify:
        root.mkdir(parents=True, exist_ok=True)
        lock = root / 'updater.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError('Another updater may be running. If it was interrupted, close it and remove updater.lock before retrying.')
        except OSError as exc:
            raise RuntimeError('Cannot create files in the data folder: ' + str(root) + '. The folder may be read-only in this launch context. Run Update SIP Compass.cmd from Windows File Explorer; the launcher will check for a writable location. Original error: ' + str(exc)) from exc
        os.close(fd)
    db = None
    try:
        db = connect(':memory:' if verify else root / 'sip-cache.sqlite3')
        rules = json.loads((ROOT / 'candidate-rules.json').read_text(encoding='utf-8'))
        warnings = []
        print('Reading scheme list and daily AMFI NAVs...', flush=True)
        try:
            all_schemes = request(HISTORY_URL)
            catalog = [r for r in all_schemes if candidate(r, rules) or r.get('schemeCode') == rules['benchmark']]
            if len(catalog) < 100 or len({r['schemeCode'] for r in catalog}) != len(catalog):
                raise ValueError('Unexpected scheme list')
            previous_catalog = state_get(db, 'catalog', [])
            if previous_catalog and len(catalog) < .9 * len(previous_catalog):
                raise ValueError('Scheme list shrank by over 10%; retaining the prior universe for review')
            state_set(db, 'catalog', catalog)
        except Exception as exc:
            catalog = state_get(db, 'catalog', [])
            warnings.append('Scheme list not refreshed: ' + str(exc))
            if not catalog:
                raise
        try:
            daily = parse_daily(request(NAV_URL, raw=True))
        except Exception as exc:
            daily = {}
            warnings.append('Daily AMFI NAV unavailable: ' + str(exc))
        cached = {code: (json.loads(p), checked) for code, p, checked in db.execute('SELECT * FROM histories')}
        failures = []
        def update_one(row):
            code = str(row['schemeCode'])
            old, checked = cached.get(code, (None, ''))
            current = daily.get(code)
            newest = old['points'][-1][0] if old else ''
            gap = (dt.date.fromisoformat(current['point'][0]) - dt.date.fromisoformat(newest)).days if current and newest else 999
            refresh_meta = not checked or (today() - dt.date.fromisoformat(checked)).days >= 30
            # Any multi-day gap is backfilled from history (including missed runs).
            needs_history = args.full_history or not old or gap > 1 or refresh_meta
            result, issue = old, None
            if needs_history:
                try:
                    result = merge_history(old, parse_history(request(HISTORY_URL + '/' + code), code))
                    checked = today().isoformat()
                except Exception as exc:
                    issue = str(exc)
                    # Do not append over a known gap: leave the old series intact.
                    return code, old, checked, issue
            if current and result:
                # When a gap existed, the history must bridge to the preceding day
                # or already include today's quote; otherwise keep old data.
                end = dt.date.fromisoformat(result['points'][-1][0])
                target = dt.date.fromisoformat(current['point'][0])
                if (target - end).days <= 1:
                    result = merge_history(result, {'meta': result['meta'], 'points': [current['point']]})
                elif target > end:
                    issue = 'History source has not backfilled the daily NAV gap'
            return code, result, checked, issue
        print(f'Updating {len(catalog)} histories (first run takes longer)...', flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for i, (code, result, checked, issue) in enumerate(pool.map(update_one, catalog), 1):
                if issue:
                    failures.append({'code': code, 'reason': issue})
                if result:
                    db.execute('INSERT OR REPLACE INTO histories VALUES (?,?,?)', (code, json.dumps(result, separators=(',', ':'), allow_nan=False), checked))
                    db.commit()
                if i % 100 == 0:
                    print(f'  Histories {i}/{len(catalog)}', flush=True)
        stamp = today().isoformat()
        for kind, loader in [('ter', lambda: get_ter_with_fallback(db)), ('aum', get_aum)]:
            old = state_get(db, kind, {'rows': [], 'checked': None})
            if args.facts_refresh or old['checked'] != stamp:
                print('Reading AMFI ' + kind.upper() + ' disclosures...', flush=True)
                try:
                    rows = loader()
                    if not rows:
                        raise ValueError('No disclosures returned')
                    # Retain earlier TER records across month boundaries; newest
                    # dated record wins. AUM is a complete current report snapshot.
                    if kind == 'ter':
                        rows = old['rows'] + rows
                        latest = ter_index(rows)
                        valid_ids = {r['id']: r['date'] for matches in latest.values() for r in matches}
                        unique = {}
                        for r in rows:
                            if r.get('NSDLSchemeCode') in valid_ids and str(r.get('TER_Date', ''))[:10] == valid_ids[r['NSDLSchemeCode']]:
                                unique[json.dumps(r, sort_keys=True)] = r
                        rows = list(unique.values())
                    state_set(db, kind, {'rows': rows, 'checked': stamp})
                except Exception as exc:
                    warnings.append(kind.upper() + ' not refreshed; previous dated disclosures retained: ' + str(exc))
        ter = ter_index(state_get(db, 'ter', {'rows': []})['rows'])
        aum = aum_index(state_get(db, 'aum', {'rows': []})['rows'])
        facts = match_facts(catalog, ter, aum)
        report = {'catalogCount': len(catalog), 'historyFailures': failures, 'warnings': warnings,
            'terMatched': sum(f['ter'] is not None for f in facts.values()),
            'aumMatched': sum(f['aum'] is not None for f in facts.values()),
            'terChecked': state_get(db, 'ter', {}).get('checked'), 'aumChecked': state_get(db, 'aum', {}).get('checked')}
        report['invalidNavRowsOmitted'] = sum(json.loads(p)['meta'].get('sip_rejected_nav_rows', 0) for (p,) in db.execute('SELECT payload FROM histories'))
        count, size = export_bundle(db, catalog, facts, report, root / 'data.js', publish=not verify)
        report.update({'historyCount': count, 'bundleBytes': size, 'completed': dt.datetime.now(dt.timezone.utc).isoformat()})
        if not verify:
            atomic_text(root / 'update-report.json', json.dumps(report, indent=2))
        print(f"Ready: {count} histories; TER {report['terMatched']}/{len(catalog)}; AUM {report['aumMatched']}/{len(catalog)}.", flush=True)
        if verify:
            print(f'{len(failures)} history warnings; {len(warnings)} source warnings. Verification finished in memory; no files written.', flush=True)
        else:
            print(f'{len(failures)} history warnings; {len(warnings)} source warnings. Reopen SIP-Compass.html. See update-report.json for details.', flush=True)
        return 2 if warnings or failures else 0
    finally:
        if db:
            db.close()
        if lock:
            lock.unlink(missing_ok=True)

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT.parent), help='Folder for cache and data.js (default: the folder that holds SIP-Compass.html)')
    parser.add_argument('--full-history', action='store_true', help='Recheck all history and merge corrections')
    parser.add_argument('--facts-refresh', action='store_true', help='Refresh disclosures even if checked today')
    parser.add_argument('--verify-only', action='store_true', help='Validate live downloads in memory without writing files')
    args = parser.parse_args()
    try:
        sys.exit(run(args))
    except Exception as exc:
        print('Update failed: ' + str(exc) + '\nPrevious data.js has not been cleared.', file=sys.stderr)
        sys.exit(1)
