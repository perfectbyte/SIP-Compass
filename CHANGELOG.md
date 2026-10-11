# Changelog

## v1.5.0: first public release (October 2026)
- **Goal Guard, explained:**
  - a plain-language short answer comes first;
  - a "how it works in four steps" guide;
  - this month's actions, then ways to close a gap;
  - outcome tiles renamed to *markets do OK / slow / slow plus a crash*;
  - two charts (the money, and the mix), each with a how-to-read note;
  - every assumption has a one-line hint.
  - The maths is unchanged.
- **Ask AI connects reliably:**
  - a new launcher (`Open SIP Compass.cmd` / `open-sip-compass.sh`) serves the app at `http://localhost:8765`, which Ollama accepts by default (pages opened as a file send origin `null`, which Ollama rejects);
  - the largest chat model is selected automatically, embedding models are skipped, and the choice is remembered;
  - plain-language diagnosis: Ollama not running, no model, or opened as a file;
  - reasoning models such as gpt-oss show progress while thinking;
  - one-click carry of saved data to the launcher copy.
- **Money leaks (Check My SIP):**
  - Regular-vs-Direct commission cost;
  - booking the yearly ₹1.25 lakh tax-free equity gain.
- **My Plan:** the cost of waiting a year to start.
- **Backup:** save and load your goals and plan as a file (About panel).
- **About panel:** what the tool is, what it isn't, where your data goes, and data credits.
- **Expense ratios (TER) and fund sizes (AUM)** from AMFI disclosures, with dates (built with ChatGPT/Codex).
- **Local updater:** NAV history, TER and AUM in `data.js`. Python standard library only, with a SQLite cache, gap backfills and atomic publication.
- **Ranking research:** a point-in-time historical comparison of top-5 picks against the category median.
- Repository layout, README, user guide, method notes, MIT license and CI.

## v1.4.3
- The header tabs get their own row, with arrows, edge fades and mouse-wheel scrolling, so hidden tabs can be found at every width.

## v1.4.2
- Goal Guard audit fixes:
  - separate price months for each cost;
  - invalid drafts are never saved;
  - shortfall options stay within form limits.

## v1.4.1
- Goal Guard fixes:
  - one schedule drives the advice and the projections;
  - deadlines are enforced;
  - input validation;
  - shortfall options for retirement goals.

## v1.4
- **Goal Guard:** capital protection for dated and retirement goals.

## v1.3 and earlier
- My Plan, Top Funds (29 categories, strict AMFI matching, cleaned NAVs), Debt Desk, Time Machine, Check My SIP, local Ask AI, The Rules with a built-in self-test.
