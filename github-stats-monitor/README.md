# GitHub Repository Stats Monitor

Monitor GitHub repository statistics and store them in Arc for time-series analysis.

## Overview

This project demonstrates Arc's capabilities by collecting real-world GitHub repository metrics:

- ⭐ **Stars** - Repository popularity
- 👀 **Watchers** - Active followers
- 🍴 **Forks** - Community engagement
- 🐛 **Issues** - Open issues count
- 🔀 **Pull Requests** - Active PRs
- 📊 **Size** - Repository size in KB
- 🌐 **Network** - Subscribers and network count

Data is collected every 10 minutes (configurable) and sent to Arc using the high-performance **MessagePack protocol** with gzip compression.

## Features

- ✅ **High Performance**: Uses MessagePack for 7.9× faster writes than Line Protocol
- ✅ **Efficient Compression**: Gzip compression reduces network bandwidth
- ✅ **Multi-Repo**: Monitor multiple repositories simultaneously
- ✅ **Rate Limit Friendly**: Includes delays between API calls
- ✅ **Multi-Database**: Write to specific Arc database for isolation
- ✅ **Detailed Metrics**: Tracks 13+ different repository statistics
- ✅ **Continuous Monitoring**: Runs forever with configurable intervals

## Installation

### Prerequisites

- Python 3.8+
- Arc instance running (local or remote)
- Arc API token
- GitHub personal access token (optional, for higher rate limits)

### Setup

1. **Clone and navigate to project:**
   ```bash
   cd github-stats-monitor
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Create Arc API token:**
   ```bash
   # If Arc is running locally
   cd /path/to/arc-core
   DB_PATH="./data/arc.db" python3 -c "
   from api.auth import AuthManager
   auth = AuthManager(db_path='./data/arc.db')
   token = auth.create_token('github-monitor', description='GitHub stats monitor')
   print(f'Token: {token}')
   "
   ```

## Configuration

Edit `.env` file with your settings:

```bash
# Arc Configuration
ARC_URL=http://localhost:8000
ARC_TOKEN=your-arc-api-token-here
ARC_DATABASE=github_stats         # Optional: Use dedicated database

# GitHub Configuration
GITHUB_REPOS=basekick-labs/arc-core,basekick-labs/arc-superset-dialect
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx   # Optional: Higher rate limits

# Monitoring Configuration
INTERVAL_SECONDS=600               # Collect every 10 minutes
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ARC_URL` | Arc API endpoint | `http://localhost:8000` | Yes |
| `ARC_TOKEN` | Arc API token | - | **Yes** |
| `ARC_DATABASE` | Target database namespace | `default` | No |
| `GITHUB_REPOS` | Comma-separated list of repos | `basekick-labs/arc-core` | Yes |
| `GITHUB_TOKEN` | GitHub PAT for higher limits | - | No |
| `INTERVAL_SECONDS` | Collection interval | `600` (10 min) | No |

## Usage

### Run Once

Collect stats once and exit:

```bash
python3 monitor.py
# Or with custom environment
ARC_TOKEN=your-token GITHUB_REPOS=owner/repo python3 monitor.py
```

### Continuous Monitoring

Run forever with automatic collection:

```bash
python3 monitor.py
```

Press `Ctrl+C` to stop.

### Run as Background Service

Using `screen`:
```bash
screen -S github-monitor
python3 monitor.py
# Detach: Ctrl+A, D
# Reattach: screen -r github-monitor
```

Using `systemd` (Linux):
```ini
# /etc/systemd/system/github-monitor.service
[Unit]
Description=GitHub Stats Monitor for Arc
After=network.target

[Service]
Type=simple
User=arc
WorkingDirectory=/path/to/github-stats-monitor
EnvironmentFile=/path/to/github-stats-monitor/.env
ExecStart=/usr/bin/python3 /path/to/github-stats-monitor/monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable github-monitor
sudo systemctl start github-monitor
sudo systemctl status github-monitor
```

## Data Schema

### Measurement: `github_repo_stats`

Data is sent to Arc using the MessagePack format with the following structure:

**Arc MessagePack Format:**
```python
{
    "batch": [                          # Wrap records in "batch" array
        {
            "m": "github_repo_stats",   # Required: measurement name
            "t": 1728481200000,          # Required: Unix timestamp in milliseconds

            # Tags (dimensions) - nested in "tags" dict
            "tags": {
                "repo": "basekick-labs/arc",
                "owner": "basekick-labs",
                "language": "python",
                "default_branch": "main"
            },

            # Fields (metrics) - nested in "fields" dict, all numeric
            "fields": {
                "stars": 245.0,
                "watchers": 20.0,
                "forks": 18.0,
                "open_issues": 3.0,
                "open_prs": 2.0,
                "total_issues": 5.0,
                "subscribers": 15.0,
                "size_kb": 1024.0,
                "network_count": 25.0,
                "is_fork": 0.0,         # 0=false, 1=true
                "is_archived": 0.0,
                "has_issues": 1.0,
                "has_wiki": 1.0,
                "has_pages": 0.0
            }
        }
    ]
}
```

**Tags (Dimensions - Strings):**
- `repo` - Repository name (e.g., "basekick-labs/arc")
- `owner` - Repository owner
- `language` - Primary language (or "none")
- `default_branch` - Default branch name

**Fields (Metrics - Numbers):**
- `stars` - Stargazers count
- `watchers` - Watchers count
- `forks` - Forks count
- `open_issues` - Open issues count (excluding PRs)
- `open_prs` - Open pull requests count
- `total_issues` - Total open issues (includes PRs)
- `subscribers` - Subscribers count
- `size_kb` - Repository size in KB
- `network_count` - Network count
- `is_fork` - Whether repo is a fork (0=false, 1=true)
- `is_archived` - Whether repo is archived (0=false, 1=true)
- `has_issues` - Issues enabled (0=false, 1=true)
- `has_wiki` - Wiki enabled (0=false, 1=true)
- `has_pages` - GitHub Pages enabled (0=false, 1=true)

## Querying Data

Once data is in Arc, query it with SQL:

### Recent Stats

```sql
SELECT
  time,
  repo,
  stars,
  forks,
  open_issues
FROM github_repo_stats
WHERE time > now() - INTERVAL '24 hours'
ORDER BY time DESC
LIMIT 100;
```

### Stars Growth

```sql
SELECT
  time_bucket(INTERVAL '1 hour', time) as hour,
  repo,
  MAX(stars) - MIN(stars) as stars_growth
FROM github_repo_stats
WHERE time > now() - INTERVAL '7 days'
GROUP BY hour, repo
ORDER BY hour DESC;
```

### Compare Repositories

```sql
SELECT
  repo,
  MAX(stars) as current_stars,
  MAX(forks) as current_forks,
  MAX(open_issues) as current_issues
FROM github_repo_stats
WHERE time > now() - INTERVAL '1 hour'
GROUP BY repo
ORDER BY current_stars DESC;
```

### Activity Trends

```sql
SELECT
  date_trunc('day', time) as day,
  repo,
  AVG(stars) as avg_stars,
  AVG(open_issues) as avg_issues,
  AVG(open_prs) as avg_prs
FROM github_repo_stats
WHERE time > now() - INTERVAL '30 days'
GROUP BY day, repo
ORDER BY day DESC;
```

## Visualizing with Superset

1. **Connect to Arc:**
   ```
   arc://your-token@localhost:8000/github_stats
   ```

2. **Create Dataset:**
   - Table: `github_repo_stats`
   - Time column: `time`

3. **Build Dashboards:**
   - Line chart: Stars over time
   - Bar chart: Compare repos by stars/forks
   - Table: Latest stats for all repos

## Performance

### Throughput

Using MessagePack protocol with gzip compression:

- **Write Speed**: ~1.89M records/sec (Arc's maximum)
- **Network Efficiency**: 70-80% compression with gzip
- **Latency**: <50ms per write request
- **Storage**: ~100 bytes per record (compressed Parquet)

### Cost Estimation

For monitoring 10 repositories every 10 minutes:

- **Records/day**: 10 repos × 6 collections/hour × 24 hours = 1,440 records
- **Records/month**: ~43,200 records
- **Storage/month**: ~4.3 MB (compressed Parquet)

Minimal overhead - Arc is designed for billions of records!

## Rate Limits

### GitHub API Limits

- **Without token**: 60 requests/hour
- **With token**: 5,000 requests/hour

This monitor uses:
- 2 API calls per repository (main stats + issues)
- With 10 repos every 10 minutes = 20 calls/hour

Well within limits even without a token! But GitHub token is recommended.

### Arc Limits

No practical limits for this use case. Arc can handle:
- 1.89M records/sec (MessagePack)
- Billions of records in storage

## Troubleshooting

### "ARC_TOKEN environment variable is required"

You need to create an Arc API token:

```bash
cd /path/to/arc-core
DB_PATH="./data/arc.db" python3 -c "
from api.auth import AuthManager
auth = AuthManager(db_path='./data/arc.db')
token = auth.create_token('github-monitor', description='Monitor token')
print(f'Token: {token}')
"
```

### "Rate limit exceeded"

If you see 403 errors from GitHub:

1. Add a GitHub personal access token to `.env`
2. Increase `INTERVAL_SECONDS` to reduce frequency
3. Check GitHub rate limits: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit`

### "Connection refused to Arc"

Make sure Arc is running:

```bash
# Check if Arc is running
curl http://localhost:8000/health

# Start Arc if needed
cd /path/to/arc-core
./start.sh native
```

## Architecture

```
┌─────────────────┐
│  GitHub API     │
│  (REST)         │
└────────┬────────┘
         │ HTTP GET (every 10 min)
         ▼
┌─────────────────┐
│  Monitor        │
│  (Python)       │
└────────┬────────┘
         │ MessagePack + gzip
         ▼
┌─────────────────┐
│  Arc            │
│  (Time-Series)  │
└────────┬────────┘
         │ SQL Queries
         ▼
┌─────────────────┐
│  Superset       │
│  (Dashboards)   │
└─────────────────┘
```

## Example Output

```
2025-10-09 10:00:00 - __main__ - INFO - Initialized monitor for 2 repositories
2025-10-09 10:00:00 - __main__ - INFO - Arc URL: http://localhost:8000, Database: github_stats
2025-10-09 10:00:00 - __main__ - INFO - Starting collection cycle for 2 repositories
2025-10-09 10:00:01 - __main__ - INFO - Fetched stats for basekick-labs/arc-core: 245 ⭐, 18 🍴, 3 issues, 2 PRs
2025-10-09 10:00:03 - __main__ - INFO - Fetched stats for basekick-labs/arc-superset-dialect: 12 ⭐, 2 🍴, 0 issues, 1 PRs
2025-10-09 10:00:03 - __main__ - INFO - Successfully wrote 2 records to Arc (compressed: 458 bytes)
2025-10-09 10:00:03 - __main__ - INFO - Collection cycle complete: 2/2 successful
2025-10-09 10:00:03 - __main__ - INFO - Sleeping for 600 seconds...
```

## License

MIT

## Contributing

This is a showcase project for Arc. Feel free to:
- Add more metrics
- Support additional Git hosting platforms (GitLab, Bitbucket)
- Create visualization templates
- Improve error handling
- Add alerting capabilities

## Related Projects

- [Arc Core](https://github.com/basekick-labs/arc-core) - Time-series database
- [Arc Superset Dialect](https://github.com/basekick-labs/arc-superset-dialect) - Visualization integration
- [Awesome Arc](https://github.com/basekick-labs/awesome-arc) - More showcase projects

---

**Built with ❤️ using Arc - The High-Performance Time-Series Database**
