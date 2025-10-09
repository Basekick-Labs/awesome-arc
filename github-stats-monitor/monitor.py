#!/usr/bin/env python3
"""
GitHub Repository Stats Monitor

Fetches repository statistics from GitHub API and writes them to Arc
using MessagePack protocol for high-performance ingestion.

Metrics collected:
- Stars, watchers, forks
- Open issues, pull requests
- Repository size
- Network stats (subscribers, etc.)
"""

import os
import time
import requests
import msgpack
import gzip
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load .env from the script's directory
    env_path = Path(__file__).parent / '.env'
    load_dotenv(dotenv_path=env_path)
    logger_init = logging.getLogger(__name__)
    if env_path.exists():
        logger_init.info(f"Loaded environment from {env_path}")
except ImportError:
    # dotenv not installed, will use system environment variables only
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GitHubStatsMonitor:
    """Monitor GitHub repository statistics and send to Arc"""

    def __init__(
        self,
        repos: List[str],
        arc_url: str,
        arc_token: str,
        github_token: Optional[str] = None,
        database: str = "default"
    ):
        """
        Initialize GitHub stats monitor

        Args:
            repos: List of repositories to monitor (format: "owner/repo")
            arc_url: Arc API URL (e.g., "http://localhost:8000")
            arc_token: Arc API token
            github_token: GitHub personal access token (optional, for higher rate limits)
            database: Arc database to write to
        """
        self.repos = repos
        self.arc_url = arc_url.rstrip('/')
        self.arc_token = arc_token
        self.database = database

        # GitHub API headers
        self.github_headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if github_token:
            self.github_headers["Authorization"] = f"Bearer {github_token}"

        logger.info(f"Initialized monitor for {len(repos)} repositories")
        logger.info(f"Arc URL: {self.arc_url}, Database: {self.database}")

    def fetch_repo_stats(self, repo: str) -> Optional[Dict]:
        """
        Fetch repository statistics from GitHub API

        Args:
            repo: Repository in format "owner/repo"

        Returns:
            Dictionary with repository stats or None if error
        """
        try:
            # Fetch main repo data
            url = f"https://api.github.com/repos/{repo}"
            response = requests.get(url, headers=self.github_headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Fetch additional stats (issues, PRs)
            issues_url = f"https://api.github.com/repos/{repo}/issues"
            issues_response = requests.get(
                issues_url,
                headers=self.github_headers,
                params={"state": "open"},
                timeout=10
            )

            open_issues_count = 0
            open_prs_count = 0

            if issues_response.status_code == 200:
                issues_data = issues_response.json()
                for item in issues_data:
                    if 'pull_request' in item:
                        open_prs_count += 1
                    else:
                        open_issues_count += 1

            # Extract relevant metrics (Arc MessagePack format)
            # Arc expects: m=measurement, t=timestamp, then tags/fields as flat keys
            stats = {
                "m": "github_repo_stats",                           # measurement
                "t": datetime.now(datetime.UTC).isoformat(),        # timestamp (timezone-aware)

                # Tags (dimensions) - string values
                "repo": str(repo),
                "owner": str(data.get("owner", {}).get("login", "unknown")),
                "language": str(data.get("language") or "none"),
                "default_branch": str(data.get("default_branch", "main")),

                # Fields (metrics) - ensure all are numeric (int or float)
                "stars": int(data.get("stargazers_count") or 0),
                "watchers": int(data.get("watchers_count") or 0),
                "forks": int(data.get("forks_count") or 0),
                "open_issues": int(open_issues_count),
                "open_prs": int(open_prs_count),
                "total_issues": int(data.get("open_issues_count") or 0),
                "subscribers": int(data.get("subscribers_count") or 0),
                "size_kb": int(data.get("size") or 0),
                "network_count": int(data.get("network_count") or 0),
                "is_fork": int(data.get("fork", False)),
                "is_archived": int(data.get("archived", False)),
                "has_issues": int(data.get("has_issues", False)),
                "has_wiki": int(data.get("has_wiki", False)),
                "has_pages": int(data.get("has_pages", False)),
            }

            logger.info(
                f"Fetched stats for {repo}: "
                f"{stats['stars']} ⭐, {stats['forks']} 🍴, "
                f"{stats['open_issues']} issues, {stats['open_prs']} PRs"
            )

            return stats

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error(f"Repository not found: {repo}")
            elif e.response.status_code == 403:
                logger.error(f"Rate limit exceeded or access denied for {repo}")
            else:
                logger.error(f"HTTP error fetching {repo}: {e}")
            return None

        except Exception as e:
            logger.error(f"Error fetching stats for {repo}: {e}")
            return None

    def write_to_arc(self, records: List[Dict]) -> bool:
        """
        Write records to Arc using MessagePack protocol

        Args:
            records: List of metric records

        Returns:
            True if successful, False otherwise
        """
        if not records:
            logger.warning("No records to write")
            return False

        try:
            # Serialize to MessagePack
            packed_data = msgpack.packb(records)

            # Compress with gzip
            compressed_data = gzip.compress(packed_data)

            # Send to Arc
            headers = {
                "x-api-key": self.arc_token,
                "Content-Type": "application/msgpack",
                "Content-Encoding": "gzip",
                "x-arc-database": self.database
            }

            response = requests.post(
                f"{self.arc_url}/write/v2/msgpack",
                headers=headers,
                data=compressed_data,
                timeout=30
            )

            response.raise_for_status()

            logger.info(
                f"Successfully wrote {len(records)} records to Arc "
                f"(compressed: {len(compressed_data)} bytes)"
            )

            return True

        except Exception as e:
            logger.error(f"Error writing to Arc: {e}")
            return False

    def run_once(self) -> int:
        """
        Run a single collection cycle

        Returns:
            Number of repositories successfully monitored
        """
        logger.info(f"Starting collection cycle for {len(self.repos)} repositories")

        records = []
        success_count = 0

        for repo in self.repos:
            stats = self.fetch_repo_stats(repo)
            if stats:
                records.append(stats)
                success_count += 1

            # Rate limiting: sleep between requests
            time.sleep(1)

        # Write to Arc
        if records:
            if self.write_to_arc(records):
                logger.info(f"Collection cycle complete: {success_count}/{len(self.repos)} successful")
            else:
                logger.error("Failed to write data to Arc")
        else:
            logger.warning("No data collected in this cycle")

        return success_count

    def run_forever(self, interval_seconds: int = 600):
        """
        Run monitoring loop forever

        Args:
            interval_seconds: Time between collection cycles (default: 600 = 10 minutes)
        """
        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

        while True:
            try:
                self.run_once()
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            logger.info(f"Sleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)


def main():
    """Main entry point"""
    # Configuration from environment variables
    repos_str = os.getenv("GITHUB_REPOS")
    if not repos_str:
        logger.error("GITHUB_REPOS environment variable is required")
        logger.error("Example: GITHUB_REPOS=owner/repo1,owner/repo2")
        return 1

    repos = [r.strip() for r in repos_str.split(",") if r.strip()]
    if not repos:
        logger.error("No valid repositories found in GITHUB_REPOS")
        return 1

    arc_url = os.getenv("ARC_URL", "http://localhost:8000")
    arc_token = os.getenv("ARC_TOKEN")
    github_token = os.getenv("GITHUB_TOKEN")
    database = os.getenv("ARC_DATABASE", "default")
    interval = int(os.getenv("INTERVAL_SECONDS", "600"))  # 10 minutes

    if not arc_token:
        logger.error("ARC_TOKEN environment variable is required")
        return 1

    # Create monitor
    monitor = GitHubStatsMonitor(
        repos=repos,
        arc_url=arc_url,
        arc_token=arc_token,
        github_token=github_token,
        database=database
    )

    # Run monitoring loop
    monitor.run_forever(interval_seconds=interval)

    return 0


if __name__ == "__main__":
    exit(main())
