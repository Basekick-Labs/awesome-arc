# Awesome Arc

A curated collection of projects showcasing [Arc](https://github.com/basekick-labs/arc)'s capabilities as a high-performance time-series database.

## About Arc

Arc is a modern time-series data warehouse optimized for high-throughput ingestion and fast analytical queries. It combines:

- **11.8M records/sec** ingestion via MessagePack
- **DuckDB query engine** for OLAP analytics
- **Parquet storage** on S3-compatible backends
- **Multi-database architecture** for data isolation
- **Automatic compaction** for query optimization
- **Write-Ahead Log (WAL)** for zero data loss

## Why This Repository?

This repository demonstrates Arc's real-world applications through practical examples. Each project shows:

1. **How to integrate** with Arc's APIs
2. **Best practices** for data ingestion
3. **Query patterns** for time-series analysis
4. **Visualization** options with tools like Superset

Whether you're evaluating Arc for your use case or learning time-series database patterns, these projects provide working code you can run immediately.

## Projects

| Project | Description | Metrics | Interval | Status |
|---------|-------------|---------|----------|--------|
| **[GitHub Stats Monitor](./github-stats-monitor/)** | Track repository statistics (stars, forks, issues, PRs) | 13+ metrics | 10 minutes | Ready |
| **[Kubernetes Monitoring](./kubernetes-monitoring/)** | Monitor K8s clusters with Telegraf and Grafana | CPU, memory, disk, pods | 10 seconds | Ready |
| **System Monitor** | Monitor server resources (CPU, memory, disk, network) | TBD | 1 minute | Coming Soon |
| **API Monitor** | Track HTTP endpoint health, latency, and errors | TBD | 30 seconds | Coming Soon |
| **Social Media Tracker** | Monitor social media metrics and engagement | TBD | 15 minutes | Coming Soon |
| **Website Analytics** | Track website visitors and page performance | TBD | Real-time | Coming Soon |
| **IoT Sensor Data** | Collect and analyze IoT device telemetry | TBD | 5 seconds | Coming Soon |

## Quick Start

### Prerequisites

- **Arc Core** running (local or remote)
  ```bash
  git clone https://github.com/basekick-labs/arc
  cd arc
  ./start.sh native
  ```

- **Python 3.8+** for running examples

- **Arc API Token**
  ```bash
  DB_PATH="./data/arc.db" python3 -c "
  from api.auth import AuthManager
  auth = AuthManager(db_path='./data/arc.db')
  token = auth.create_token('showcase', description='Showcase projects')
  print(f'Token: {token}')
  "
  ```

### Run a Project

Each project is self-contained with its own README:

```bash
# Example: GitHub Stats Monitor
cd github-stats-monitor
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python3 monitor.py
```

## Technology Stack

### Data Ingestion
- **MessagePack Protocol**: 11.8M records/sec sustained throughput
- **Gzip Compression**: 70-80% bandwidth reduction
- **Batch Processing**: Efficient bulk writes

### Storage & Query
- **Parquet Files**: Columnar storage with excellent compression
- **DuckDB Engine**: Fast analytical queries with partition pruning
- **S3-Compatible**: MinIO, AWS S3, GCS, Ceph support

### Visualization
- **Apache Superset**: Business intelligence dashboards
- **Grafana**: Real-time monitoring (via Line Protocol)
- **Jupyter**: Ad-hoc analysis with SQL

## Key Concepts Demonstrated

### 1. Multi-Database Architecture
Projects can write to isolated databases for data separation:

```python
headers = {
    "x-api-key": token,
    "x-arc-database": "github_stats"  # Dedicated database
}
```

### 2. High-Performance Ingestion
Using MessagePack for maximum throughput:

```python
packed_data = msgpack.packb(records)
compressed_data = gzip.compress(packed_data)

response = requests.post(
    f"{arc_url}/write/v2/msgpack",
    headers={"Content-Type": "application/msgpack", "Content-Encoding": "gzip"},
    data=compressed_data
)
```

### 3. Time-Series Analysis
Query data with standard SQL:

```sql
-- Recent trends
SELECT
  time_bucket(INTERVAL '1 hour', time) as hour,
  measurement,
  AVG(value) as avg_value
FROM metrics
WHERE time > now() - INTERVAL '7 days'
GROUP BY hour, measurement
ORDER BY hour DESC;
```

### 4. Schema Evolution
Arc automatically handles schema changes:

```python
# Day 1: Basic metrics
{"measurement": "cpu", "time": ..., "usage": 50.0}

# Day 2: Add new field (no migration needed!)
{"measurement": "cpu", "time": ..., "usage": 50.0, "temperature": 65.0}
```

## Performance Benchmarks

Arc's performance makes it ideal for high-volume time-series data:

| Metric | Performance |
|--------|-------------|
| **Write Throughput** | 11.8M records/sec (MessagePack) |
| **Compression** | 85% with ZSTD (after compaction) |
| **Query Speed** | Sub-second for 100M+ rows |
| **Latency** | <50ms per write request |
| **Storage Efficiency** | ~100 bytes/record (Parquet) |

*Benchmarks: Apple M3 Max, 14 cores, 36GB RAM*

## Project Structure

```
awesome-arc/
├── README.md                    # This file
├── github-stats-monitor/        # GitHub repository statistics
│   ├── monitor.py              # Python monitoring script
│   ├── README.md               # Project documentation
│   ├── requirements.txt        # Dependencies
│   └── .env.example            # Configuration template
├── system-monitor/             # Coming soon
├── api-monitor/                # Coming soon
└── ...
```

## Use Cases

These projects demonstrate Arc's versatility for:

### DevOps & Infrastructure
- System resource monitoring
- Application performance metrics
- Log aggregation and analysis
- Container orchestration metrics

### Product Analytics
- User behavior tracking
- Feature usage analytics
- A/B testing results
- Conversion funnel analysis

### IoT & Sensors
- Industrial equipment telemetry
- Smart home device data
- Environmental sensor networks
- Fleet tracking and telematics

### Business Metrics
- Sales and revenue tracking
- Marketing campaign performance
- Customer engagement metrics
- Social media analytics

### Financial Services
- Trading data and market feeds
- Transaction monitoring
- Risk analytics
- Portfolio performance

## Contributing

We welcome contributions! Here's how you can help:

### Add a New Project
1. Create a new directory with a descriptive name
2. Include a comprehensive README.md
3. Add example queries and visualizations
4. Update this main README with project details

### Improve Existing Projects
- Optimize performance
- Add error handling
- Include more metrics
- Create visualization templates
- Add alerting capabilities

### Share Your Experience
- Write blog posts about your use case
- Create video tutorials
- Share dashboard templates
- Report issues or suggest features

## Resources

### Documentation
- [Arc Core Documentation](https://github.com/basekick-labs/arc)
- [Arc Superset Dialect](https://github.com/basekick-labs/arc-superset-dialect)
- [Architecture Overview](https://github.com/basekick-labs/arc/blob/main/docs/ARCHITECTURE.md)
- [WAL Documentation](https://github.com/basekick-labs/arc/blob/main/docs/WAL.md)
- [Compaction Guide](https://github.com/basekick-labs/arc/blob/main/docs/COMPACTION.md)

### Community
- [GitHub Issues](https://github.com/basekick-labs/arc/issues)
- [GitHub Discussions](https://github.com/basekick-labs/arc/discussions)

### Getting Help
- Check project README files
- Review Arc Core documentation
- Open an issue on GitHub
- Join community discussions

## Roadmap

Upcoming showcase projects:

- [ ] **System Monitor** - Server resource monitoring
- [ ] **API Monitor** - HTTP endpoint health checks
- [ ] **Social Media Tracker** - Track engagement metrics
- [ ] **Website Analytics** - Real-time visitor tracking
- [ ] **IoT Sensor Network** - Device telemetry collection
- [ ] **Financial Data Feed** - Stock market data ingestion
- [ ] **Log Aggregator** - Centralized application logs
- [ ] **Kubernetes Metrics** - Container orchestration monitoring

Have an idea? [Open an issue](https://github.com/basekick-labs/awesome-arc/issues) or submit a PR!

## Performance Tips

### Write Optimization
1. **Use MessagePack**: 11.8M records/sec vs Line Protocol
2. **Enable compression**: gzip reduces bandwidth 70-80%
3. **Batch records**: Send multiple records per request
4. **Use dedicated database**: Isolate workloads for better performance

### Query Optimization
1. **Include time filter**: `WHERE time > now() - INTERVAL '1 hour'`
2. **Leverage compaction**: Merges small files for faster queries
3. **Use specific measurements**: Avoid `FROM *` queries
4. **Add LIMIT clause**: Control result size

### Storage Optimization
1. **Enable compaction**: Automatic file merging (85% reduction)
2. **Configure buffer sizes**: Balance latency vs throughput
3. **Use WAL for durability**: Optional zero data loss mode
4. **Set lifecycle policies**: Archive old data to cheaper storage

## License

MIT License - See individual project directories for specific licenses.

## Acknowledgments

These projects are built with:
- [Arc Core](https://github.com/basekick-labs/arc) - High-performance time-series database
- [DuckDB](https://duckdb.org/) - Analytical query engine
- [Apache Parquet](https://parquet.apache.org/) - Columnar storage format
- [MessagePack](https://msgpack.org/) - Binary serialization format

## Support

- **Star** this repo if you find it useful
- **Report issues** on GitHub
- **Share ideas** in Discussions
- **Contribute** with new projects or improvements

---

**Built with Arc - The High-Performance Time-Series Database**

*Last updated: January 2026*
