#!/usr/bin/env python3
"""
Download the reference data the Pi classifies against.

    python fetch_reference_data.py                       # blocklists only
    python fetch_reference_data.py --geoip-key YOUR_KEY  # adds country lookup

GeoIP is optional: without it the Pi still identifies trackers and owners,
it just cannot say which country a destination sits in.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

import requests

OUT = Path(__file__).parent / "data" / "blocklists"


def easyprivacy():
    out = OUT / "easyprivacy.txt"
    if out.exists():
        print(f"[skip] {out.name}")
        return
    print("[down] EasyPrivacy ...")
    r = requests.get("https://easylist.to/easylist/easyprivacy.txt", timeout=60)
    r.raise_for_status()
    out.write_text(r.text, encoding="utf-8")
    print(f"[done] {out.name} ({len(r.text):,} chars)")


def hosts_blocklist():
    """
    The DNS sinkhole needs a list written for DNS. EasyPrivacy is not one:
    its rules carry paths and resource types that only a browser can honour,
    so converting it to DNS blocks both over-blocks and under-blocks. This
    consolidated hosts file is purpose-built for name-level blocking.
    """
    out = OUT / "hosts_blocklist.txt"
    if out.exists():
        print(f"[skip] {out.name}")
        return
    print("[down] hosts blocklist (StevenBlack, unified) ...")
    r = requests.get(
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        timeout=120,
    )
    r.raise_for_status()
    out.write_text(r.text, encoding="utf-8")
    print(f"[done] {out.name} ({len(r.text):,} chars)")


def tracker_radar():
    """
    Tracker Radar is ~50k per-domain JSON files, not one file. A sparse
    clone pulls only domains/, which is then flattened to the single
    {domain: {owner, category}} map classify.py reads.
    """
    out = OUT / "tracker_radar.json"
    if out.exists():
        print(f"[skip] {out.name}")
        return
    print("[down] Tracker Radar (sparse clone) ...")
    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                 "https://github.com/duckduckgo/tracker-radar.git", tmp],
                check=True, capture_output=True, text=True,
            )
            subprocess.run(
                ["git", "-C", tmp, "sparse-checkout", "set", "domains"],
                check=True, capture_output=True, text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            print(f"[warn] clone failed ({exc}); owner attribution will be limited")
            return

        flat: dict[str, dict] = {}
        for path in Path(tmp, "domains").rglob("*.json"):
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            domain = entry.get("domain")
            if not domain:
                continue
            categories = entry.get("categories") or []
            flat[domain.lower()] = {
                "owner": (entry.get("owner") or {}).get("displayName"),
                "category": categories[0] if categories else None,
            }

    out.write_text(json.dumps(flat), encoding="utf-8")
    print(f"[done] {out.name} ({len(flat):,} domains)")


def geolite2(key: str | None):
    out = OUT / "GeoLite2-Country.mmdb"
    if out.exists():
        print(f"[skip] {out.name}")
        return
    if not key:
        print("[skip] GeoLite2 - no --geoip-key given, country lookup disabled")
        print("       free key: https://www.maxmind.com/en/geolite2/signup")
        return
    print("[down] GeoLite2-Country ...")
    url = (
        "https://download.maxmind.com/app/geoip_download?"
        f"edition_id=GeoLite2-Country&license_key={key}&suffix=tar.gz"
    )
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.name.endswith(".mmdb"):
                extracted = tar.extractfile(member)
                if extracted:
                    out.write_bytes(extracted.read())
                break
    print(f"[done] {out.name}")


def main():
    parser = argparse.ArgumentParser(description="Download Pi reference data")
    parser.add_argument("--geoip-key", default=None, help="MaxMind GeoLite2 license key")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    easyprivacy()
    hosts_blocklist()
    tracker_radar()
    geolite2(args.geoip_key)
    print("\n[ok] reference data ready")


if __name__ == "__main__":
    main()
