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
import logging

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

            # Extract relevant metrics
            stats = {
                "measurement": "github_repo_stats",
                "time": datetime.utcnow().isoformat() + "Z",

                # Tags (dimensions)
                "repo": repo,
                "owner": data.get("owner", {}).get("login", "unknown"),
                "language": data.get("language", "unknown"),
                "is_fork": data.get("fork", False),
                "is_archived": data.get("archived", False),

                # Fields (metrics)
                "stars": data.get("stargazers_count", 0),
                "watchers": data.get("watchers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": open_issues_count,
                "open_prs": open_prs_count,
                "total_issues": data.get("open_issues_count", 0),
                "subscribers": data.get("subscribers_count", 0),
                "size_kb": data.get("size", 0),
                "network_count": data.get("network_count", 0),

                # Additional metadata
                "default_branch": data.get("default_branch", "main"),
                "has_issues": data.get("has_issues", False),
                "has_wiki": data.get("has_wiki", False),
                "has_pages": data.get("has_pages", False),
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
    repos_str = os.getenv("GITHUB_REPOS", "basekick-labs/arc-core")
    repos = [r.strip() for r in repos_str.split(",") if r.strip()]

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
