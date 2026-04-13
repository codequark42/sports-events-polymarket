# Sports Events Polymarket Calendar

This project serves an auto-updating `.ics` calendar that combines:

- Polymarket sports events filtered to your interests
- Formula 1 race sessions from the provided ECAL feed
- Result updates for finished Polymarket events when the underlying market resolves

All event times are emitted in the `Europe/Rome` timezone.

## What It Includes

Polymarket filters are tuned for:

- Football: matches sourced from Polymarket league and cup `games` pages for EPL, La Liga, Serie A, Bundesliga, Ligue 1, UCL, UEL, FA Cup, Coppa Italia, DFB Pokal, and Copa del Rey, including future league weeks, then narrowed to stronger big-match fixtures
- UFC: main card fights
- Chess: Hikaru, Magnus Carlsen, and world championship matches
- Tennis: Grand Slam semi-finals/finals involving Djokovic, Sinner, or Alcaraz
- Valorant: VCT and higher-tier matches
- Cricket: matches involving India, RCB, or Delhi Capitals

F1 is sourced from:

- `https://ics.ecal.com/ecal-sub/69c26447d1780a00029628bd/Formula%201.ics`

The F1 import keeps race and sprint sessions and skips practice/qualifying sessions.

## Run It

Serve a subscribable calendar URL locally:

```bash
python3 -m sports_calendar serve --host 0.0.0.0 --port 8000
```

Then:

- open `http://YOUR_HOST:8000/` for a small control page with a `Refresh Now` button
- subscribe your calendar app to:

```text
http://YOUR_HOST:8000/calendar.ics
```

Generate a static file instead:

```bash
python3 -m sports_calendar generate --output dist/calendar.ics
```

## GitHub Actions Hosting

This repo now includes a GitHub Actions workflow at [`/.github/workflows/publish-calendar.yml`](.github/workflows/publish-calendar.yml) that:

- runs every hour
- can also be triggered manually with `workflow_dispatch`
- rebuilds `calendar.ics` plus the pre/post-filter dumps
- publishes the generated files to GitHub Pages

To use it:

1. Push this repo to GitHub.
2. In GitHub, open `Settings -> Pages`.
3. Set the source to `GitHub Actions`.
4. Run the `Publish Calendar` workflow once manually from the `Actions` tab.

After the first successful deploy, the public URLs will be:

```text
https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/calendar.ics
https://YOUR_GITHUB_USERNAME.github.io/YOUR_REPO_NAME/
```

The root page links to:

- `calendar.ics`
- `polymarket_pre_filter.tsv`
- `polymarket_post_filter.tsv`
- `polymarket_pre_filter.json`

GitHub scheduled workflows are not exact to the minute, so "hourly" means roughly once per hour rather than precisely every 60 minutes.

## Useful Options

```bash
python3 -m sports_calendar serve --days-forward 240 --days-back 30 --cache-ttl 600
python3 -m sports_calendar generate --output dist/calendar.ics --max-polymarket-pages 8
```

## Notes

- The server caches the generated calendar in memory for a short TTL to avoid hammering Polymarket.
- The control page at `/` can force an immediate refresh without waiting for the cache TTL.
- Result updates depend on Polymarket market resolution data. For some markets, a result may appear slightly after the event ends.
- The calendar now pulls from Polymarket's sport-specific listing pages instead of the broad global sports feed, which yields much better football/UFC/chess coverage.
- The football and Valorant definitions of "big vs big" are heuristic and easy to extend in `sports_calendar/filtering.py` and `sports_calendar/polymarket_pages.py`.

## Tests

```bash
python3 -m unittest discover -s tests
```
