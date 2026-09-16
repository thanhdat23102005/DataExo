"""
DataExodus Pi application.

Receives telemetry from the browser extension, enriches it with owner and
country attribution the extension cannot do on its own, records DNS blocks
reported by the sinkhole, and serves the dashboard.

    uvicorn app:app --host 0.0.0.0 --port 5000
"""

from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from classify import ADEQUATE_COUNTRIES, HostClassifier
from store import Store

BASE_DIR = Path(__file__).parent

state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["store"] = Store()
    state["classifier"] = HostClassifier.load()
    print(f"[pi] reference data: {state['classifier'].ready}")
    yield
    state["store"].close()


app = FastAPI(title="DataExodus Pi", lifespan=lifespan)


@app.post("/api/telemetry")
async def telemetry(request: Request):
    """
    Payload shape sent by extension v3.3:

        {
          "telemetry": {
            "tabData_7": {
              "domain": "abc.net.au", "baseDomain": "abc.net.au",
              "riskScore": 42, "piiLeaked": true,
              "newPiiDetails": [ {type, scope, destination, company} ],
              "requests": { "doubleclick.net": {count, isThirdParty, tracker, ...} }
            }
          },
          "timestamp": 1730000000000,
          "delta": true
        }

    Only destinations that changed since the extension's last successful
    delivery are present, and request_count is a running total, so writes
    are idempotent replaces.
    """
    payload = await request.json()
    tabs = payload.get("telemetry") or {}
    store: Store = state["store"]
    classifier: HostClassifier = state["classifier"]

    observations = 0
    pii = 0

    for tab_key, tab in tabs.items():
        if not isinstance(tab, dict):
            continue
        page_domain = tab.get("domain")
        risk_score = int(tab.get("riskScore") or 0)

        for destination, info in (tab.get("requests") or {}).items():
            if not isinstance(info, dict):
                continue
            verdict = classifier.classify(destination)
            tracker_hint = info.get("tracker") or {}
            # GeoIP needs the name to resolve; when it does not, the
            # extension's bundled country is the fallback. Offshore has to be
            # derived from whichever country is finally used, or a row ends up
            # saying "United States" and "not offshore" at the same time.
            country = verdict["country"] or tracker_hint.get("country")
            store.upsert_observation({
                "tab_key": tab_key,
                "page_domain": page_domain,
                "destination": destination,
                "request_count": int(info.get("count") or 0),
                "is_third_party": bool(info.get("isThirdParty")),
                # The extension only knows its own bundled list; the Pi also
                # has EasyPrivacy, so either source is enough to call it one.
                "is_tracker": bool(verdict["is_tracker"] or tracker_hint),
                "owner": verdict["owner"] or tracker_hint.get("company"),
                "category": verdict["category"] or tracker_hint.get("category"),
                "country": country,
                "offshore": bool(country) and country not in ADEQUATE_COUNTRIES,
                "risk_score": risk_score,
            })
            observations += 1

        for detail in (tab.get("newPiiDetails") or []):
            if not isinstance(detail, dict):
                continue
            if store.insert_pii_event({
                "page_domain": page_domain,
                "destination": detail.get("destination"),
                "company": detail.get("company"),
                "hash_type": detail.get("type"),
                "scope": detail.get("scope") or "covert",
            }):
                pii += 1

    return {"ok": True, "observations": observations, "pii_events": pii}


@app.post("/api/dns-block")
async def dns_block(request: Request):
    """Reported by dns_sinkhole.py, which cannot write to DuckDB itself."""
    payload = await request.json()
    hostname = (payload.get("hostname") or "").lower()
    if not hostname:
        return JSONResponse({"ok": False, "error": "hostname required"}, status_code=400)

    owner, category = state["classifier"].owner_of(hostname)
    state["store"].insert_dns_block(hostname, payload.get("client_ip") or "", owner, category)
    return {"ok": True}


@app.get("/api/summary")
async def summary():
    store: Store = state["store"]
    return {
        "totals": store.summary(),
        "top_owners": store.top_owners(),
        "countries": store.countries(),
        "riskiest_pages": store.riskiest_pages(),
        "recent_pii": store.recent_pii(),
        "recent_dns_blocks": store.recent_dns_blocks(),
        "reference_data": state["classifier"].ready,
    }


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "dashboard.html")


def main():
    parser = argparse.ArgumentParser(description="DataExodus Pi application")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
