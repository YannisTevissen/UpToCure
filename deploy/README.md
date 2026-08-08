# Server setup: self-updating reports

The site generates its own reports on the EC2 host via a systemd timer
(`uptocure-refresh.timer`). Content lives **outside** the git checkout so the
`git reset --hard` deploy never touches it.

## One-time migration (run on the EC2 host)

```bash
# 1. Content directories, seeded from the repo copies
sudo mkdir -p /var/lib/uptocure
sudo cp -r /home/ubuntu/UpToCure/UpToCure/reports /var/lib/uptocure/reports
sudo mkdir -p /var/lib/uptocure/disease_requests
# Preserve any pending user requests
sudo cp /home/ubuntu/UpToCure/UpToCure/disease_requests/*.json /var/lib/uptocure/disease_requests/ 2>/dev/null || true
sudo chown -R ubuntu:ubuntu /var/lib/uptocure

# 2. Point the web app at the new content dir (drop-in for the gunicorn unit)
sudo systemctl edit uptocure
# add:
#   [Service]
#   Environment=UPTOCURE_REPORTS_DIR=/var/lib/uptocure/reports
#   Environment=UPTOCURE_REQUESTS_DIR=/var/lib/uptocure/disease_requests
sudo systemctl restart uptocure

# 3. Refresh job credentials + knobs
sudo mkdir -p /etc/uptocure
sudo cp /home/ubuntu/UpToCure/deploy/refresh.env.example /etc/uptocure/refresh.env
sudo chmod 600 /etc/uptocure/refresh.env
sudo vim /etc/uptocure/refresh.env   # set OPENAI_API_KEY

# 4. Generator dependencies
cd /home/ubuntu/UpToCure/reports_generator && pdm install --prod

# 5. Units (the deploy workflow re-installs these on every push to main)
sudo cp /home/ubuntu/UpToCure/deploy/uptocure-refresh.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now uptocure-refresh.timer
```

## Operating it

```bash
systemctl list-timers uptocure-refresh.timer      # next run
sudo systemctl start uptocure-refresh.service     # run now
journalctl -u uptocure-refresh -f                 # logs
curl -s localhost:8000/api/status | jq            # last run + month spend
cat /var/lib/uptocure/reports/.state/cost-ledger.json | jq '."'"$(date +%Y-%m)"'".total_usd'
```

The refresh job stops generating as soon as the month's ledger reaches
`MONTHLY_BUDGET_USD`. State (ledger, last run, accepted user requests) lives in
`/var/lib/uptocure/reports/.state/`.

## Backup (optional but recommended)

Content is no longer in git, so add a nightly backup, e.g. in `crontab -e`:

```
15 5 * * * tar czf /home/ubuntu/backups/uptocure-reports-$(date +\%u).tar.gz -C /var/lib/uptocure reports
```

(rotates over 7 days) or `aws s3 sync /var/lib/uptocure/reports s3://<bucket>/reports`.
