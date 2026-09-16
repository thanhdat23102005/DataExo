"""
Hostname classification for the Raspberry Pi application.

Given a hostname, answer the three questions the Pi cares about:
is this a tracker, who owns it, and what country does it resolve to.

This is deliberately separate from research/pipeline/classify.py. That
module classifies full requests from the 50-site study (resource types,
initiators, request-level fields). The Pi only ever sees hostnames - from
extension telemetry and from DNS queries - and has to be copyable to a Pi
on its own, so it carries its own small loader for the same two public
data sources.
"""

from __future__ import annotations

import json
import re
import socket
from functools import lru_cache
from pathlib import Path

import geoip2.database
import geoip2.errors

# Countries with privacy frameworks Australia's APP 8 treats as broadly
# comparable. Anything outside this set is reported as an offshore transfer
# to a jurisdiction without equivalent protection. This is a simplification
# of a legal question, not a legal opinion.
ADEQUATE_COUNTRIES = {
    "AU", "NZ", "GB", "IE", "DE", "FR", "NL", "BE", "AT", "ES", "IT",
    "SE", "NO", "DK", "FI", "CH", "PT", "LU", "IS", "LI", "PL", "CZ",
    "CA", "JP", "KR", "IL", "UY", "AR",
}

DATA_DIR = Path(__file__).parent / "data" / "blocklists"

# "Is this a tracker?" and "should DNS black-hole this?" are different
# questions and need different sources.
#
# EasyPrivacy answers the first. It is a request-level list: rules carry
# paths and resource types ("||google-analytics.com^$script,third-party"),
# because a browser extension can act on those and DNS cannot. Only rules
# covering a whole domain are read; "||wikipedia.org/beacon/" says wikipedia
# serves a beacon at one path, not that wikipedia is a tracker, and treating
# it as one would be wrong in the dashboard and catastrophic at the DNS
# layer, where it takes the site off the air for every device on the network.
_RULE = re.compile(r"^\|\|([a-z0-9.\-]+)\^?(?:\$[^/]*)?$")
_DOMAIN = re.compile(r"^[a-z0-9\-]+(?:\.[a-z0-9\-]+)*\.[a-z]{2,}$")

# The second question is answered by a hosts-format list, which is written
# for DNS in the first place: one line, one domain, block it entirely.
_HOSTS = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1)\s+([a-z0-9.\-]+)")


def parse_easyprivacy(text: str) -> set[str]:
    domains: set[str] = set()
    for line in text.splitlines():
        line = line.strip().lower()
        if not line or line[0] in "!#[" or line.startswith("@@"):
            continue
        if "##" in line or "#@#" in line or "#?#" in line:
            continue
        match = _RULE.match(line)
        if match and _DOMAIN.match(match.group(1)):
            domains.add(match.group(1))
    return domains


def parse_hosts(text: str) -> set[str]:
    domains: set[str] = set()
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if not line:
            continue
        match = _HOSTS.match(line)
        if match and _DOMAIN.match(match.group(1)):
            domains.add(match.group(1))
    domains.discard("localhost")
    return domains


class HostClassifier:
    def __init__(self, tracker_domains: set[str], blocked_domains: set[str],
                 owners: dict[str, dict], geoip=None):
        self.tracker_domains = tracker_domains
        self.blocked_domains = blocked_domains
        self.owners = owners
        self.geoip = geoip

    @classmethod
    def load(cls, data_dir: Path | str = DATA_DIR) -> "HostClassifier":
        data_dir = Path(data_dir)

        tracker_domains: set[str] = set()
        easyprivacy = data_dir / "easyprivacy.txt"
        if easyprivacy.exists():
            tracker_domains = parse_easyprivacy(easyprivacy.read_text(encoding="utf-8", errors="ignore"))

        blocked_domains: set[str] = set()
        hosts = data_dir / "hosts_blocklist.txt"
        if hosts.exists():
            blocked_domains = parse_hosts(hosts.read_text(encoding="utf-8", errors="ignore"))

        owners: dict[str, dict] = {}
        radar = data_dir / "tracker_radar.json"
        if radar.exists():
            raw = json.loads(radar.read_text(encoding="utf-8"))
            owners = {k.lower(): v for k, v in raw.items() if isinstance(v, dict)}

        geoip = None
        mmdb = data_dir / "GeoLite2-Country.mmdb"
        if mmdb.exists():
            geoip = geoip2.database.Reader(str(mmdb))

        return cls(tracker_domains, blocked_domains, owners, geoip)

    @property
    def ready(self) -> dict:
        return {
            "tracker_domains": len(self.tracker_domains),
            "blocked_domains": len(self.blocked_domains),
            "owner_entries": len(self.owners),
            "geoip": self.geoip is not None,
        }

    @staticmethod
    def _matches(host: str, domains: set[str]) -> bool:
        if not host:
            return False
        if host in domains:
            return True
        # An entry for "doubleclick.net" must also catch
        # "stats.g.doubleclick.net", so walk up the label chain.
        parts = host.split(".")
        for i in range(1, len(parts) - 1):
            if ".".join(parts[i:]) in domains:
                return True
        return False

    def is_tracker(self, hostname: str) -> bool:
        """Labelling only - used for the dashboard, never for blocking."""
        return self._matches((hostname or "").lower().strip("."), self.tracker_domains)

    def should_block(self, hostname: str) -> bool:
        """DNS decision. Separate list, because a wrong answer here breaks
        the site for every device on the network."""
        return self._matches((hostname or "").lower().strip("."), self.blocked_domains)

    def owner_of(self, hostname: str) -> tuple[str | None, str | None]:
        host = (hostname or "").lower().strip(".")
        parts = host.split(".")
        for i in range(len(parts) - 1):
            entry = self.owners.get(".".join(parts[i:]))
            if entry:
                return entry.get("owner"), entry.get("category")
        return None, None

    @lru_cache(maxsize=4096)
    def country_of(self, hostname: str) -> str | None:
        if not self.geoip or not hostname:
            return None
        try:
            ip = socket.gethostbyname(hostname)
            return self.geoip.country(ip).country.iso_code
        except (socket.gaierror, socket.herror, geoip2.errors.AddressNotFoundError, ValueError, OSError):
            return None

    def classify(self, hostname: str, resolve_country: bool = True) -> dict:
        host = (hostname or "").lower().strip(".")
        owner, category = self.owner_of(host)
        country = self.country_of(host) if resolve_country else None
        return {
            "hostname": host,
            "is_tracker": self.is_tracker(host),
            "owner": owner,
            "category": category,
            "country": country,
            "offshore": bool(country) and country not in ADEQUATE_COUNTRIES,
        }
