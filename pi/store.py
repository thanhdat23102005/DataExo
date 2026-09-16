"""
DuckDB storage for the Pi application.

DuckDB allows a single writing process per database file, so every write
goes through this module and this module is only ever used by app.py. The
DNS sinkhole is a separate process and therefore reports its blocks to
app.py over HTTP rather than opening the database itself.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "data" / "dataexodus.duckdb"

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    tab_key      VARCHAR,
    page_domain  VARCHAR,
    destination  VARCHAR,
    request_count INTEGER,
    is_third_party BOOLEAN,
    is_tracker   BOOLEAN,
    owner        VARCHAR,
    category     VARCHAR,
    country      VARCHAR,
    offshore     BOOLEAN,
    risk_score   INTEGER,
    first_seen   TIMESTAMP,
    last_seen    TIMESTAMP,
    PRIMARY KEY (tab_key, destination)
);

CREATE TABLE IF NOT EXISTS pii_events (
    ts           TIMESTAMP,
    page_domain  VARCHAR,
    destination  VARCHAR,
    company      VARCHAR,
    hash_type    VARCHAR,
    scope        VARCHAR
);

CREATE TABLE IF NOT EXISTS dns_blocks (
    ts           TIMESTAMP,
    hostname     VARCHAR,
    client_ip    VARCHAR,
    owner        VARCHAR,
    category     VARCHAR
);
"""


class Store:
    def __init__(self, db_path: Path | str = DB_PATH):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(db_path))
        self.conn.execute(SCHEMA)
        # DuckDB connections are not thread-safe and FastAPI serves requests
        # from a thread pool, so every statement is serialised here.
        self.lock = threading.Lock()

    def close(self):
        with self.lock:
            self.conn.close()

    def upsert_observation(self, row: dict):
        """
        The extension sends only destinations that changed since its last
        successful delivery, and repeats them if a delivery failed, so a
        destination can arrive more than once. request_count is the
        extension's running total for that destination, which makes this an
        idempotent replace rather than an increment.
        """
        now = datetime.now(timezone.utc)
        with self.lock:
            self.conn.execute(
                """
                INSERT INTO observations AS o (
                    tab_key, page_domain, destination, request_count,
                    is_third_party, is_tracker, owner, category, country,
                    offshore, risk_score, first_seen, last_seen
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT (tab_key, destination) DO UPDATE SET
                    request_count = excluded.request_count,
                    risk_score    = excluded.risk_score,
                    is_tracker    = excluded.is_tracker,
                    owner         = COALESCE(excluded.owner, o.owner),
                    category      = COALESCE(excluded.category, o.category),
                    country       = COALESCE(excluded.country, o.country),
                    offshore      = excluded.offshore,
                    last_seen     = excluded.last_seen
                """,
                [
                    row["tab_key"], row["page_domain"], row["destination"],
                    row["request_count"], row["is_third_party"], row["is_tracker"],
                    row["owner"], row["category"], row["country"],
                    row["offshore"], row["risk_score"], now, now,
                ],
            )

    # A delivery the extension had to retry replays its unsent PII details,
    # and nothing in the payload distinguishes a retry from the identifier
    # genuinely leaking again. Identical events arriving inside this window
    # are treated as the same event; a real repeat later still counts.
    PII_DEDUPE_SECONDS = 60

    def insert_pii_event(self, row: dict) -> bool:
        now = datetime.now(timezone.utc)
        with self.lock:
            duplicate = self.conn.execute(
                """
                SELECT 1 FROM pii_events
                WHERE page_domain IS NOT DISTINCT FROM ?
                  AND destination IS NOT DISTINCT FROM ?
                  AND hash_type   IS NOT DISTINCT FROM ?
                  AND scope       IS NOT DISTINCT FROM ?
                  AND ts > ? - INTERVAL 1 SECOND * ?
                LIMIT 1
                """,
                [row["page_domain"], row["destination"], row["hash_type"],
                 row["scope"], now, self.PII_DEDUPE_SECONDS],
            ).fetchone()
            if duplicate:
                return False
            self.conn.execute(
                "INSERT INTO pii_events VALUES (?,?,?,?,?,?)",
                [now, row["page_domain"], row["destination"],
                 row["company"], row["hash_type"], row["scope"]],
            )
            return True

    def insert_dns_block(self, hostname: str, client_ip: str, owner: str | None, category: str | None):
        with self.lock:
            self.conn.execute(
                "INSERT INTO dns_blocks VALUES (?,?,?,?,?)",
                [datetime.now(timezone.utc), hostname, client_ip, owner, category],
            )

    def _fetch(self, sql: str, params: list | None = None) -> list[dict]:
        with self.lock:
            cur = self.conn.execute(sql, params or [])
            columns = [d[0] for d in cur.description]
            return [dict(zip(columns, r)) for r in cur.fetchall()]

    def summary(self) -> dict:
        totals = self._fetch("""
            SELECT
                COALESCE(SUM(request_count), 0)                                  AS requests,
                COUNT(DISTINCT destination)                                      AS destinations,
                COUNT(DISTINCT CASE WHEN is_tracker THEN destination END)        AS trackers,
                COUNT(DISTINCT CASE WHEN offshore   THEN destination END)        AS offshore_destinations,
                COUNT(DISTINCT CASE WHEN offshore   THEN country END)            AS offshore_countries
            FROM observations
        """)[0]
        totals["pii_events"] = self._fetch(
            "SELECT COUNT(*) AS n FROM pii_events WHERE scope = 'covert'")[0]["n"]
        totals["dns_blocks"] = self._fetch("SELECT COUNT(*) AS n FROM dns_blocks")[0]["n"]
        return totals

    def top_owners(self, limit: int = 10) -> list[dict]:
        return self._fetch("""
            SELECT owner,
                   SUM(request_count)          AS requests,
                   COUNT(DISTINCT destination) AS destinations,
                   MAX(country)                AS country
            FROM observations
            WHERE owner IS NOT NULL
            GROUP BY owner
            ORDER BY requests DESC
            LIMIT ?
        """, [limit])

    def countries(self) -> list[dict]:
        return self._fetch("""
            SELECT country,
                   ANY_VALUE(offshore)         AS offshore,
                   SUM(request_count)          AS requests,
                   COUNT(DISTINCT destination) AS destinations
            FROM observations
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY requests DESC
        """)

    def recent_pii(self, limit: int = 20) -> list[dict]:
        return self._fetch("""
            SELECT ts, page_domain, destination, company, hash_type, scope
            FROM pii_events ORDER BY ts DESC LIMIT ?
        """, [limit])

    def recent_dns_blocks(self, limit: int = 20) -> list[dict]:
        return self._fetch("""
            SELECT ts, hostname, client_ip, owner
            FROM dns_blocks ORDER BY ts DESC LIMIT ?
        """, [limit])

    def riskiest_pages(self, limit: int = 10) -> list[dict]:
        return self._fetch("""
            SELECT page_domain,
                   MAX(risk_score)                                           AS risk_score,
                   COUNT(DISTINCT destination)                               AS destinations,
                   COUNT(DISTINCT CASE WHEN is_tracker THEN destination END) AS trackers
            FROM observations
            WHERE page_domain IS NOT NULL
            GROUP BY page_domain
            ORDER BY risk_score DESC, trackers DESC
            LIMIT ?
        """, [limit])
