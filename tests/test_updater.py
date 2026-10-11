import contextlib, datetime as dt, importlib.util, io, json, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('updater',Path(__file__).resolve().parent.parent/'updater'/'update_data.py')
u=importlib.util.module_from_spec(spec);spec.loader.exec_module(u)

class UpdaterTests(unittest.TestCase):
 def setUp(self):
  self.clock=patch.object(u,'today',return_value=dt.date(2026,10,9));self.clock.start();self.addCleanup(self.clock.stop)
 def ter(self,**kwargs):
  return dict(NSDLSchemeCode='alpha-1',Scheme_Name='Alpha Small Cap Fund',TER_Date='2026-10-08T00:00:00.000Z',D_TER='0.40',D_BER='0.20',R_TER='1.80',**kwargs)
 def test_total_direct_ter_not_base_or_regular(self):
  self.assertEqual(u.ter_index([self.ter()])['alphasmallcapfund'][0]['value'],.4)
 def test_zero_ter_retained(self):
  r=self.ter();r['D_TER']='0';self.assertEqual(u.ter_index([r])['alphasmallcapfund'][0]['value'],0)
 def test_missing_ter_not_zero(self):
  r=self.ter();r['D_TER']=None;self.assertEqual(u.ter_index([r]),{})
 def test_latest_date_not_last_row_wins(self):
  a=self.ter();b={**a,'TER_Date':'2026-10-01','D_TER':.9}
  self.assertEqual(u.ter_index([a,b])['alphasmallcapfund'][0]['value'],.4)
 def test_conflicting_same_day_withheld(self):
  a=self.ter();self.assertEqual(u.ter_index([a,{**a,'D_TER':.9}]),{})
 def test_future_disclosure_ignored(self):
  a=self.ter();a['TER_Date']='2026-10-10';self.assertEqual(u.ter_index([a]),{})
 def test_duplicate_nsdl_name_ambiguous(self):
  a=self.ter();idx=u.ter_index([a,{**a,'NSDLSchemeCode':'other'}]);cat=[{'schemeCode':123,'schemeName':'Alpha Small Cap Fund - Direct Growth'}]
  self.assertIsNone(u.match_facts(cat,idx,{})['123']['ter'])
 def test_two_nav_codes_same_name_withheld(self):
  cat=[{'schemeCode':x,'schemeName':'Alpha Small Cap Fund - Direct Growth'} for x in [123,124]]
  self.assertTrue(all(x['ter'] is None for x in u.match_facts(cat,u.ter_index([self.ter()]),{}).values()))
 def test_near_match_never_fuzzy(self):
  cat=[{'schemeCode':123,'schemeName':'Alpha Small Cap Opportunities Fund - Direct Growth'}]
  self.assertIsNone(u.match_facts(cat,u.ter_index([self.ter()]),{})['123']['ter'])
 def test_exact_match_preserves_source_and_date(self):
  cat=[{'schemeCode':123,'schemeName':'Alpha Small Cap Fund - Direct Plan - Growth'}]
  row=u.match_facts(cat,u.ter_index([self.ter()]),{})['123']['ter']
  self.assertEqual(row['date'],'2026-10-08');self.assertIn('amfiindia.com',row['source'])
 def test_aum_qualification_preserved(self):
  rows=[dict(dailyAUM=123.45,schemeName='Alpha Fund',_reportDate='2026-10-07',_category='Small Cap',specialCharAum='^')]
  self.assertEqual(u.aum_index(rows)['alphafund'][0]['qualification'],'^')
 def test_bad_numbers(self):
  for val in [True,None,'',float('nan'),float('inf'),-1]:
   with self.assertRaises(ValueError):u.number(val)
 def test_six_column_nav(self):
  text='Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date\n123;x;;Alpha Direct Growth;10.5;08-Oct-2026'
  self.assertEqual(u.parse_daily(text)['123']['point'],['2026-10-08',10.5])
 def test_eight_column_nav(self):
  text='Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date\n123;x;;Alpha;Direct;Growth;10.5;08-Oct-2026'
  self.assertEqual(u.parse_daily(text)['123']['point'],['2026-10-08',10.5])
 def test_unknown_nav_schema_rejected(self):
  with self.assertRaises(ValueError):u.parse_daily('Scheme Code;Scheme Name;NAV;Date\n123;Alpha;10;08-Oct-2026')
 def test_conflicting_nav_code_rejected(self):
  text='Scheme Code;Scheme Name;Net Asset Value;Date\n123;Alpha;10;08-Oct-2026\n123;Alpha;11;08-Oct-2026'
  with self.assertRaises(ValueError):u.parse_daily(text)
 def test_history_identity(self):
  with self.assertRaises(ValueError):u.parse_history({'meta':{'scheme_code':124},'data':[]},123)
 def test_invalid_nav_rows_omitted_and_counted(self):
  h=u.parse_history({'meta':{'scheme_code':123,'scheme_name':'Alpha','scheme_category':'Equity'},'data':[{'date':'07-10-2026','nav':'0'},{'date':'08-10-2026','nav':'12'}]},123)
  self.assertEqual(h['meta']['sip_rejected_nav_rows'],1);self.assertEqual(h['points'],[('2026-10-08',12)])
 def test_all_zero_navs_remain_unavailable(self):
  with self.assertRaises(ValueError):u.parse_history({'meta':{'scheme_code':123,'scheme_name':'Alpha','scheme_category':'Equity'},'data':[{'date':'08-10-2026','nav':'0'}]},123)
 def test_missing_house_falls_back_to_previous_month(self):
  db=u.connect(':memory:');self.addCleanup(db.close)
  db.execute('INSERT INTO histories VALUES (?,?,?)',('123',json.dumps({'meta':{'fund_house':'HDFC Mutual Fund'},'points':[]}),'2026-10-09'))
  raw='"mfId":"9","mfName":"HDFC Mutual Fund"'
  with patch.object(u,'request',return_value=raw),patch.object(u,'get_ter',side_effect=[[],[self.ter()]]) as getter,contextlib.redirect_stdout(io.StringIO()):
   self.assertEqual(len(u.get_ter_with_fallback(db)),1);self.assertEqual(getter.call_args.args,('09-2026','9'))
 def test_merge_preserves_older_history_and_corrections(self):
  a={'meta':{},'points':[['2026-01-01',10],['2026-10-07',11]]};b={'meta':{'scheme_code':123},'points':[['2026-10-07',11.1],['2026-10-08',12]]}
  self.assertEqual(u.merge_history(a,b)['points'],[('2026-01-01',10),('2026-10-07',11.1),('2026-10-08',12)])
 def test_repeated_ter_page_rejected(self):
  def request(url):
   page=int(u.urllib.parse.parse_qs(u.urllib.parse.urlparse(url).query)['page'][0]);return {'data':[self.ter()],'meta':{'page':page,'total':2,'pageCount':2}}
  with patch.object(u,'request',side_effect=request):
   with self.assertRaises(ValueError):u.get_ter('10-2026')
 def test_incomplete_ter_page_rejected(self):
  with patch.object(u,'request',return_value={'data':[self.ter()],'meta':{'page':1,'total':2,'pageCount':1}}):
   with self.assertRaises(ValueError):u.get_ter('10-2026')
 def test_bundle_requires_benchmark(self):
  db=u.connect(':memory:');self.addCleanup(db.close)
  with self.assertRaises(ValueError):u.export_bundle(db,[],{},{},'unused',False)
 def test_bundle_json_roundtrip_and_no_personal_fields(self):
  db=u.connect(':memory:');self.addCleanup(db.close)
  payload={'meta':{'scheme_code':120716,'scheme_name':'</script>"x'},'points':[['2026-10-08',12]]}
  db.execute('INSERT INTO histories VALUES (?,?,?)',('120716',json.dumps(payload),'2026-10-09'))
  with patch.object(u,'atomic_text') as writer:
   u.export_bundle(db,[{'schemeCode':120716,'schemeName':'Alpha Direct Growth'}],{},{},'unused')
   text=writer.call_args.args[1];j=json.loads(text[len(u.PREFIX):-2]);self.assertEqual(j['histories']['120716'],payload)
   self.assertNotIn('goals',j);self.assertNotIn('holdings',j)

class ReplayTests(unittest.TestCase):
 def test_daily_append_gap_backfill_and_failed_source_preservation(self):
  class MemoryDB(sqlite3.Connection):
   def close(self):pass
  db=sqlite3.connect(':memory:',factory=MemoryDB)
  db.execute('CREATE TABLE histories (code TEXT PRIMARY KEY,payload TEXT,checked TEXT)');db.execute('CREATE TABLE state (key TEXT PRIMARY KEY,payload TEXT)')
  self.addCleanup(lambda:sqlite3.Connection.close(db))
  cat=[{'schemeCode':120716+i,'schemeName':f'Synthetic {i} Nifty 50 Index Direct Growth'} for i in range(100)]
  day=['2026-10-08'];history_end=['2026-10-08'];calls=[];failure=[False]
  def req(url,*args,**kw):
   if url==u.HISTORY_URL:return cat
   if url==u.NAV_URL:return 'Scheme Code;Scheme Name;Net Asset Value;Date\n'+'\n'.join(f"{r['schemeCode']};{r['schemeName']};12;{dt.date.fromisoformat(day[0]).strftime('%d-%b-%Y')}" for r in cat)
   code=int(url.rsplit('/',1)[1]);calls.append(code)
   if failure[0]:raise OSError('offline')
   return {'meta':{'scheme_code':code,'scheme_name':cat[code-120716]['schemeName'],'scheme_category':'Other Scheme - Index Fund'},'data':[{'date':'01-01-2020','nav':'10'},{'date':dt.date.fromisoformat(history_end[0]).strftime('%d-%m-%Y'),'nav':'12'}]}
  import argparse
  args=argparse.Namespace(output=str(Path(__file__).parent),verify_only=True,full_history=False,facts_refresh=False)
  with patch.object(u,'connect',return_value=db),patch.object(u,'request',side_effect=req),patch.object(u,'get_ter_with_fallback',return_value=[]),patch.object(u,'get_aum',return_value=[]),patch.object(u,'today',side_effect=lambda:dt.date.fromisoformat(day[0])),contextlib.redirect_stdout(io.StringIO()):
   u.run(args);self.assertEqual(len(calls),100)
   day[0]='2026-10-09';calls.clear();u.run(args);self.assertEqual(calls,[])
   last=lambda:json.loads(db.execute('SELECT payload FROM histories WHERE code="120716"').fetchone()[0])['points'][-1][0]
   self.assertEqual(last(),'2026-10-09')
   day[0]='2026-10-12';failure[0]=True;u.run(args);self.assertEqual(last(),'2026-10-09');self.assertEqual(len(calls),100)
   failure[0]=False;history_end[0]='2026-10-12';u.run(args);self.assertEqual(last(),'2026-10-12')

class DiskTests(unittest.TestCase):
 def setUp(self):
  # Check the environment independently of the updater before disk tests.
  # Some application sandboxes allow a temp file but deny files in new folders.
  folder=Path(tempfile.mkdtemp(prefix='sip_disk_preflight_'))
  reason=None
  try:
   probe=folder/'probe';probe.write_text('ok');probe.unlink()
  except OSError as exc:reason='Environment denies new-folder writes: '+str(exc)
  finally:
   try:folder.rmdir()
   except OSError:pass
  if reason:self.skipTest(reason)
 def test_actual_disk_database_publication_and_repeat_run(self):
  import argparse
  cat=[{'schemeCode':120716+i,'schemeName':f'Synthetic {i} Nifty 50 Index Direct Growth'} for i in range(100)]
  history_calls=[]
  def req(url,*args,**kwargs):
   if url==u.HISTORY_URL:return cat
   if url==u.NAV_URL:return 'Scheme Code;Scheme Name;Net Asset Value;Date\n'+'\n'.join(f"{r['schemeCode']};{r['schemeName']};12;08-Oct-2026" for r in cat)
   code=int(url.rsplit('/',1)[1]);history_calls.append(code)
   return {'meta':{'scheme_code':code,'scheme_name':cat[code-120716]['schemeName'],'scheme_category':'Other Scheme - Index Fund'},'data':[{'date':'01-01-2020','nav':'10'},{'date':'08-10-2026','nav':'12'}]}
  ter=[dict(NSDLSchemeCode='test',Scheme_Name='Synthetic 0 Nifty 50 Index',TER_Date='2026-10-08',D_TER='.1')]
  aum=[dict(schemeName='Synthetic 0 Nifty 50 Index',dailyAUM=100,_reportDate='2026-10-08',_category='Index Funds')]
  with tempfile.TemporaryDirectory(prefix='sip_disk_test_') as folder,patch.object(u,'request',side_effect=req),patch.object(u,'get_ter_with_fallback',return_value=ter),patch.object(u,'get_aum',return_value=aum),patch.object(u,'today',return_value=dt.date(2026,10,9)),contextlib.redirect_stdout(io.StringIO()):
   root=Path(folder);args=argparse.Namespace(output=folder,verify_only=False,full_history=False,facts_refresh=False)
   self.assertEqual(u.run(args),0)
   self.assertTrue((root/'sip-cache.sqlite3').is_file());self.assertTrue((root/'update-report.json').is_file());self.assertFalse((root/'updater.lock').exists())
   text=(root/'data.js').read_text(encoding='utf-8');data=json.loads(text[len(u.PREFIX):-2]);self.assertEqual(len(data['histories']),100)
   history_calls.clear();self.assertEqual(u.run(args),0);self.assertEqual(history_calls,[])
   with sqlite3.connect(root/'sip-cache.sqlite3') as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM histories').fetchone()[0],100)
 def test_failed_atomic_replace_retains_existing_bundle(self):
  with tempfile.TemporaryDirectory(prefix='sip_atomic_test_') as folder:
   path=Path(folder)/'data.js';u.atomic_text(path,'last known good')
   with patch.object(u.os,'replace',side_effect=PermissionError('simulated file lock')):
    with self.assertRaises(PermissionError):u.atomic_text(path,'new data')
   self.assertEqual(path.read_text(),'last known good');self.assertFalse(path.with_name('data.js.tmp').exists())

if __name__=='__main__':unittest.main(verbosity=2)
