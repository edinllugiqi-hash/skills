# Running the Pipeline Automatically

## Cron (own server / Raspberry Pi / VPS)

Run every weekday at 08:30, keeping secrets in an env file:

```cron
30 8 * * 1-5  cd /opt/akquise && set -a && . ./.env && set +a && python3 skills/client-acquisition/scripts/acquire.py run --send >> akquise.log 2>&1
0 10 * * 1-5  cd /opt/akquise && set -a && . ./.env && set +a && python3 skills/client-acquisition/scripts/acquire.py call --dial --limit 10 >> akquise.log 2>&1
```

## GitHub Actions

Store `GOOGLE_PLACES_API_KEY`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SENDER_EMAIL` (and optionally the ElevenLabs IDs) as repository secrets in a **private** repository, commit `acquisition.json`, and add `.github/workflows/akquise.yml`. The workflow commits the updated `leads.csv` back so state is kept between runs.

```yaml
name: Kundenakquise
on:
  schedule:
    - cron: "30 6 * * 1-5"   # 08:30 German summer time (UTC+2)
  workflow_dispatch:

permissions:
  contents: write

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Find, audit, email
        env:
          GOOGLE_PLACES_API_KEY: ${{ secrets.GOOGLE_PLACES_API_KEY }}
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: "465"
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
        run: python client-acquisition/scripts/acquire.py run --send --limit 20
      - name: Save lead state
        run: |
          git config user.name "akquise-bot"
          git config user.email "akquise-bot@users.noreply.github.com"
          git add leads.csv
          git diff --cached --quiet || git commit -m "Update leads $(date +%F)"
          git push
```

## Ramp-up

Start a new sending mailbox at about 10 emails per day and increase by 5 per week up to 40-50. Check `report` weekly: if fewer than 1 in 20 emails gets a reply, change the niche, the offer or the first two lines of the template before sending more.
