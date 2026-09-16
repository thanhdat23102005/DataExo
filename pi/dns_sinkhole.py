"""
Network-wide tracker blocking by DNS.

Every device on the Wi-Fi is pointed at the Pi for DNS. A query for a
tracker domain is answered with 0.0.0.0 (and :: for AAAA) so the
connection never leaves the device; anything else is forwarded upstream
unchanged. This covers phones, TVs and apps - everything the browser
extension cannot reach.

Blocks are reported to app.py over HTTP rather than written directly,
because DuckDB permits one writing process and app.py already holds it.

    sudo python dns_sinkhole.py                 # port 53, needs root
    python dns_sinkhole.py --port 5353          # unprivileged, for testing
"""

from __future__ import annotations

import argparse
import socket
import socketserver
import threading
from queue import Empty, Queue

import requests
from dnslib import QTYPE, RR, A, AAAA, DNSRecord

from classify import HostClassifier

UPSTREAM_TIMEOUT = 4.0
BLOCK_TTL = 300


class BlockReporter(threading.Thread):
    """
    Reports blocks to app.py on a background thread. A DNS reply must not
    wait on an HTTP call to another process - if the app is down, queries
    still have to be answered.
    """

    def __init__(self, endpoint: str):
        super().__init__(daemon=True)
        self.endpoint = endpoint
        self.queue: Queue = Queue(maxsize=1000)
        self.failed = False

    def report(self, hostname: str, client_ip: str):
        try:
            self.queue.put_nowait({"hostname": hostname, "client_ip": client_ip})
        except Exception:
            pass  # queue full: drop the log line, never the DNS reply

    def run(self):
        while True:
            try:
                item = self.queue.get(timeout=1.0)
            except Empty:
                continue
            try:
                requests.post(self.endpoint, json=item, timeout=2.0)
                if self.failed:
                    print("[dns] reporting to app restored")
                    self.failed = False
            except requests.RequestException as exc:
                if not self.failed:
                    print(f"[dns] cannot report blocks to {self.endpoint}: {exc}")
                    self.failed = True


class Resolver:
    def __init__(self, classifier: HostClassifier, upstream: str, reporter: BlockReporter):
        self.classifier = classifier
        self.upstream = upstream
        self.reporter = reporter
        self.blocked = 0
        self.forwarded = 0

    def handle(self, data: bytes, client_ip: str) -> bytes | None:
        try:
            request = DNSRecord.parse(data)
        except Exception:
            return None

        qname = str(request.q.qname).rstrip(".")
        qtype = QTYPE[request.q.qtype]

        if self.classifier.should_block(qname):
            self.blocked += 1
            self.reporter.report(qname, client_ip)
            return self._sinkhole(request, qtype)

        self.forwarded += 1
        return self._forward(data)

    def _sinkhole(self, request: DNSRecord, qtype: str) -> bytes:
        reply = request.reply()
        if qtype == "AAAA":
            reply.add_answer(RR(request.q.qname, QTYPE.AAAA, rdata=AAAA("::"), ttl=BLOCK_TTL))
        elif qtype == "A":
            reply.add_answer(RR(request.q.qname, QTYPE.A, rdata=A("0.0.0.0"), ttl=BLOCK_TTL))
        # Other record types get an empty NOERROR, which resolvers treat as
        # "exists but nothing here" - enough to stop the connection.
        return reply.pack()

    def _forward(self, data: bytes) -> bytes | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.settimeout(UPSTREAM_TIMEOUT)
                sock.sendto(data, (self.upstream, 53))
                response, _ = sock.recvfrom(4096)
                return response
        except (socket.timeout, OSError):
            return None


class Handler(socketserver.BaseRequestHandler):
    resolver: Resolver

    def handle(self):
        data, sock = self.request
        response = self.resolver.handle(data, self.client_address[0])
        if response:
            sock.sendto(response, self.client_address)


class Server(socketserver.ThreadingUDPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description="DataExodus DNS sinkhole")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=53)
    parser.add_argument("--upstream", default="1.1.1.1", help="Upstream resolver")
    parser.add_argument("--report-to", default="http://127.0.0.1:5000/api/dns-block")
    args = parser.parse_args()

    classifier = HostClassifier.load()
    if not classifier.blocked_domains:
        raise SystemExit(
            "No blocklist loaded. Run ./setup_pi.sh first - without it this "
            "would forward everything and block nothing."
        )

    reporter = BlockReporter(args.report_to)
    reporter.start()

    Handler.resolver = Resolver(classifier, args.upstream, reporter)
    server = Server((args.host, args.port), Handler)
    print(
        f"[dns] listening on {args.host}:{args.port}, upstream {args.upstream}, "
        f"{len(classifier.blocked_domains):,} domains blocked"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[dns] blocked {Handler.resolver.blocked}, forwarded {Handler.resolver.forwarded}")
        server.shutdown()


if __name__ == "__main__":
    main()
