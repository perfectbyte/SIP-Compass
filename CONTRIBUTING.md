# Contributing

Thanks for helping. SIP Compass is maintained by [Perfectbyte](https://github.com/Perfectbyte). SIP Compass is used by people planning real money, so correctness and clarity matter more than features.

## Ground rules
- **Privacy is fixed.** Nothing a user types may leave their browser: no analytics, no accounts, no remote AI. New network calls are allowed only for public market data, and need a reason in the pull request.
- **One file.** The app stays a single `SIP-Compass.html` that works when double-clicked. No build step, no framework.
- **Explain, don't advise.** Wording should describe what the numbers mean, not tell people what to buy.
- **No silent maths changes.** If a change alters any figure, say which figure and why in the pull request, and add a self-test that locks the new behaviour.

## Before you open a pull request
1. Open the app → **The Rules** → **Run self-test**: it must show **0 failed**. Or, headlessly:
   ```sh
   npm i -D playwright && npx playwright install chromium
   node scripts/run-selftest.mjs
   ```
2. Updater changes: `python -m unittest discover -s tests` must pass.
3. Check the layout at phone width (390 px) and desktop width (1280 px), in light and dark themes.
4. Don't commit your own regenerated `data.js`, `sip-cache.sqlite3` or `update-report.json`. To stop git from picking up your local `data.js`, run: `git update-index --skip-worktree data.js`

## Good first contributions
- Clearer wording anywhere a first-time investor might get stuck.
- Translations of the interface text.
- Better matching for funds the updater currently leaves without TER or AUM.
- Bug reports with the self-test output and your browser name.
