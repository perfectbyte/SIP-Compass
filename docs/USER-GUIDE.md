# SIP Compass: user guide

No coding knowledge needed. Read the first two sections, then come back to the rest when you need it.

## 1. First run

1. Extract the folder somewhere you can write to, such as `Documents\SIP-Compass`. Don't run it from inside the ZIP.
2. Double-click **Open SIP Compass.cmd** (macOS/Linux: `sh open-sip-compass.sh`). It opens the app at `http://localhost:8765`, an address only your own computer can reach. Keep the small minimised window open while you use it. Double-clicking **SIP-Compass.html** also works, but then Ask AI can't connect.
3. Wait for the status pill (top right) to show a NAV date. The first visit of the day fetches public NAV data. Later visits that day are instant.
4. Optional: run **Update SIP Compass.cmd** (Windows) or `sh update.sh` (macOS/Linux) once to keep full fund history in this folder. See the [README](../README.md#optional-build-the-local-data-bundle).

**Always open it the same way, in the same browser.** Saved data belongs to that browser and that address. The launcher address and the plain file each keep their own copy. To move data, use **About → Save my data to a file**, then **Load from a file** in the other one.

## 2. The order to use it in

**Your budget and horizon → My Plan → Goal Guard for each dated goal → Top Funds or Debt Desk to choose funds → Check My SIP once a year.** You then invest through your own app or the fund house's website. SIP Compass never touches your money.

## 3. The tabs

### My Plan
Answer four questions: your monthly SIP, when you need the money, your age, and what you'd do if ₹1 lakh became ₹65,000 in a bad year. It also checks whether you have six months of emergency savings. You get a mix of 3 to 5 funds and a range of outcomes in weak, middle and strong markets, plus what waiting one more year to start would cost. The range is the point: no one can promise the middle number.

### Goal Guard
For money needed on a date: school fees, a house down-payment, a wedding, or the first years of retirement. Open **"New here? How Goal Guard works"** for the four-step explanation. In short:

- **Equity** grows faster but can fall 30–50%. **Safe money** (debt funds, liquid funds, FDs) grows slowly but doesn't crash.
- From 5 years before the date, the plan moves the goal's money step by step from equity to safe money, so that by 1 year before, the whole amount is safe. Your SIP is used first; equity is sold only for the rest.
- Your goal is judged on the **"markets are slow"** future. If that falls short, Goal Guard lists what would close the gap.

What you see, from top to bottom:

| Section | Meaning |
| --- | --- |
| **The short answer** | What the goal will cost on the date, and whether the safe money will be there. |
| **What to do this month** | Where this month's SIP goes, and how much equity to move, if any. |
| **Ways to close the gap** | Shown only when you're short. Any one option is enough. |
| **Where you stand today** | Your safe money, your equity share against the plan's target, and what a crash tomorrow would do. |
| **Three possible futures** | Safe money on the date if markets do OK, if they are slow, or slow plus a crash now. Green means covered; red means short. |
| **Chart 1 · the money** | Green (safe) and gold (equity) money over time. The goal is safe when green reaches the dashed "needed" line. |
| **Chart 2 · the mix** | The plan's target equity share (dashed) against your path if you follow the moves (blue). The shaded band is the shift period. |

Every assumption (inflation, returns, crash size, when the shift starts and ends) is under **Assumptions you can change**, each with a one-line explanation. Reopen the page each month: it re-plans from what you actually hold.

### Top Funds
The top 10 Direct–Growth funds in each official AMFI category, scored 0–100 against their own category (50 = average). Click a fund for its score breakdown, worst stretch and crash behaviour. **Index and gold funds** are effectively tied, so pick the cheapest (lowest TER). Start from the category My Plan chose, not from the highest score on the page.

### Debt Desk
For money needed within a few years, or the safe part of a goal. Enter the amount and when you need it. It suggests suitable debt categories and checks each fund's history for credit accidents (defaults, side-pockets, suspiciously high yields).

### Time Machine
Pick a real fund, a start month and a monthly amount to see what the SIP would be worth today and its real XIRR. A **panic rule** shows what pausing after a 15–20% fall would have cost you.

### Check My SIP
Pick a fund you hold. The verdict uses the time horizon from My Plan. You get **Keep**, **Watch**, **Investigate** or **Replace**, with the reason. A higher score on another fund is not, by itself, a reason to switch. The **XIRR check** works out your true yearly return from three numbers: your monthly SIP, the months invested, and the value today. "Replace" appears only for a clear mismatch, such as equity money needed within 3 years, or a credit-risk fund for safe money. Treat it as a strong prompt to review, then decide yourself.

**Money leaks** (bottom of the tab) covers two quiet costs:
- **Regular plan or Direct plan?** shows what a Regular plan's yearly commission costs over your SIP's life, and how to switch new SIPs.
- **Your ₹1.25 lakh tax-free gain** works out how much long-term equity gain to book (and reinvest) before 31 March, and the future tax it avoids.

### Ask AI (optional)
1. Install [Ollama](https://ollama.com) and any chat model: `ollama pull gpt-oss:20b` if you have 16 GB+ of memory, or `ollama pull qwen2.5:7b` for 8 GB laptops.
2. Start the Ollama app, and open SIP Compass with **Open SIP Compass.cmd**.
3. Open Ask AI. It connects by itself and picks the largest chat model you have (embedding models are skipped). Choose another from the list any time; your choice is remembered.

If it can't connect, the tab says which of three things is wrong (Ollama not running, no model installed, or the page opened as a file) and how to fix it. If you had been opening the plain file, use **Open AI-ready copy with my data** to bring your goals across in one click. The model runs on your own computer, and your plan is never sent to a cloud service. Skip this tab if you don't want it.

### The Rules
The ten rules the tool is built on, how scores are calculated, a tax table, and **Run self-test**. It should report **0 failed**.

## 4. Everyday use

- **Monthly:** open Goal Guard and make that month's moves.
- **Yearly:** run Check My SIP on each fund and review My Plan.
- **Data:** refreshes itself on the first visit each day. If you use the updater, run it whenever you like, or enable the nightly task.

## 5. Troubleshooting

| Problem | Fix |
| --- | --- |
| Ask AI says the page was opened as a file | Open SIP Compass with **Open SIP Compass.cmd** instead. Ollama only answers `localhost` pages. |
| The launcher says port 8765 is busy | Another copy is probably already running. Look for its minimised window, or restart the PC. |
| Status shows **failed** or **held back** | Some data couldn't be fetched. Check your internet connection and reload. A held-back category is hidden on purpose rather than shown half-complete. |
| My goals disappeared | You opened the file from a different folder or browser, or cleared site data. Go back to the original location and browser. |
| Updater says **Python not found** | Install Python 3.10+ from python.org and tick "Add python.exe to PATH". |
| Updater says the folder can't be written to | You ran it inside the ZIP or a protected folder. Extract to Documents and run again. |
| Updater exit code **2** | It finished, but some sources were unavailable. Usable data was kept; see `update-report.json`. |
| `updater.lock` left behind | Only delete it if no updater window is open. |
| Self-test shows a failure | You may have an edited or partial copy. Download the release again. |

## 6. Glossary

- **SIP:** a fixed monthly investment into a fund. A way of paying in, not a product.
- **NAV:** a fund's price per unit on a given day.
- **XIRR:** your actual yearly return, accounting for when each SIP instalment went in.
- **Direct plan:** bought straight from the fund house with no distributor commission. It is usually 0.5–1% a year cheaper than the Regular plan.
- **TER:** total expense ratio, the yearly fee a fund charges, already deducted from the NAV.
- **AUM:** assets under management, the fund's size.
- **Down capture:** how much a fund falls when the index falls. Below 100 means it falls less.
- **STP:** systematic transfer plan, a scheduled move between two funds of the same fund house. Each transfer is a sale for tax purposes.
