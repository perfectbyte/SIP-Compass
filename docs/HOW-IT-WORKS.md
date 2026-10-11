# How SIP Compass works

This page explains the methods behind the numbers. The **The Rules** tab inside the app is the authoritative short version, and its self-test locks the key rules in place.

## Data

- **NAVs:** AMFI daily NAVs, via [mfapi.in](https://www.mfapi.in) or the local `data.js` bundle built by the updater. Only **Direct – Growth** plans with at least 5 years of history are scored.
- **Categories:** 29 official AMFI/SEBI categories (10 equity, index and gold; 19 debt). Funds are matched to a category by its exact official name, never by guesswork.
- **Expense ratio (TER) and fund size (AUM):** AMFI public disclosures, matched by exact normalized scheme name. Each figure carries its disclosure date. Older or ambiguous figures are labelled or left blank. TER and AUM are context only: they never change a score or a verdict. NAV returns already have expenses deducted, so TER is not subtracted twice.

## Cleaning

- **Glitches:** a one-day NAV jump that snaps straight back is deleted only if it exceeds 8% (equity, index, gold) or 2% (debt). Real crash-and-bounce days are kept.
- **Face-value or split changes** are rescaled separately, so a unit split doesn't look like a crash.
- **Common end date:** every fund in a category is measured up to the same NAV date. A category is held back, not shown half-complete, if fewer than 90% of its funds have current data.

## Scores

Each fund is compared only with funds in its own category, then turned into a 0–100 score where 50 is the category average. The ingredients:

- **Rolling returns:** every 3-year window over the last 5 years, starting each week. Both the typical window and the worst window count.
- **Crash behaviour:** down capture against Nifty 50 (below 100 means the fund falls less).
- **Debt safety:** −15 for a sharp one-day fall in the last 10 years, −10 for a side-pocket, −8 for a yield well above peers.

Index and gold funds are effectively tied: choose on cost. Liquid and arbitrage funds stay ranked, but small gaps deserve little weight.

**What the scores are not:** forecasts. The **Do the historical rankings help?** research in The Rules tab ([results](research/ranking-research-results.json)) found the top-5 beat the category median in 11 of 20 usable comparisons. That is not evidence of skill. Use scores to avoid weak or risky funds, not to chase winners.

## Goal Guard

All figures come from **one monthly schedule**, so the advice, the three futures and both charts always agree.

1. **Cost on the date.** An amount in today's rupees is grown by inflation from the month you entered it. The amount never quietly shrinks as months pass. For retirement, the safe bucket is the years of expenses you chose, grown by inflation.
2. **What should be safe now.** The amount needed is discounted to today at the debt return. A glide path sets the equity share of that amount: it holds your chosen pre-protection share (80% by default) until *Start protecting* (5 years before), then falls in a straight line to 0% at *Fully protected by* (1 year before). For retirement, the safe amount is whichever is larger: the bucket (filled step by step over the same window) or your normal safe share. The rest stays invested.
3. **Each month:** the SIP fills any gap in safe money first. Only what's still missing is sold from equity, spread over up to 12 months and never past the *fully protected* deadline. Nothing is sold before the protection window. Then the month's returns are applied.
4. **Three futures:** markets do OK (your middle equity return), markets are slow (your conservative equity return), and slow plus a crash of your chosen size today. **The goal is judged on the slow case.**
5. **If short:** it finds the smallest extra SIP, the earliest later date and the largest smaller goal that would each close the gap in the slow case. Each option is re-checked against the form's limits.

All figures are before tax, exit loads and costs. Safe funds reduce swings; they don't guarantee the amount.

## Testing

- **App self-test:** 106 checks (XIRR, the data cleaner, the emergency-fund rule, the 5-fund cap, the debt loss gate, ties, Goal Guard's schedule and limits, header layout, and more). Run it under The Rules → **Run self-test**, or headlessly with `node scripts/run-selftest.mjs`.
- **Updater tests:** 28 unit tests (`python -m unittest discover -s tests`), covering matching, gap backfills, failure retention, locking and atomic publication.
- [verification.json](research/verification.json) records the checks run on the bundled data snapshot.
