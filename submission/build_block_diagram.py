"""
Generate the architecture block diagram for the project plan and slides.

The plan's rubric awards the top band only where the background is
supported by a full block diagram, so this shows every component and every
data flow between them, including what is deliberately NOT transmitted.

    python3 build_block_diagram.py
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

NAVY = "#1F3A5F"
BLUE = "#3987E5"
TEAL = "#1E8A7A"
AMBER = "#C97A16"
RED = "#C0392B"
GREY = "#6B6B72"
LIGHT = "#F4F6F9"


def box(ax, x, y, w, h, title, lines=(), edge=NAVY, face="white", title_size=10, body_size=8):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=1.6, edgecolor=edge, facecolor=face, zorder=2,
    ))
    ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color=edge, zorder=3)
    for i, line in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.52 - i * 0.24, line, ha="center", va="top",
                fontsize=body_size, color="#33333A", zorder=3)


def group(ax, x, y, w, h, label, edge=GREY):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.3, edgecolor=edge, facecolor=LIGHT,
        linestyle=(0, (5, 3)), zorder=1,
    ))
    ax.text(x + 0.12, y + h - 0.16, label, ha="left", va="top",
            fontsize=9, fontweight="bold", color=edge, zorder=3)


def arrow(ax, start, end, label="", color=BLUE, style="-|>", offset=0.16,
          rad=0.0, size=7.5, ls="-"):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=13,
        linewidth=1.5, color=color, zorder=4,
        connectionstyle=f"arc3,rad={rad}", linestyle=ls,
    ))
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        ax.text(mx, my + offset, label, ha="center", va="bottom",
                fontsize=size, color=color, zorder=5,
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                          edgecolor="none", alpha=0.9))


def build():
    fig, ax = plt.subplots(figsize=(14.5, 9.2))
    ax.set_xlim(0, 14.5)
    ax.set_ylim(1.20, 9.60)
    ax.axis("off")

    ax.text(0.15, 9.50, "DataExodus — System Architecture", fontsize=15,
            fontweight="bold", color=NAVY, va="top")
    ax.text(0.15, 9.12,
            "Two deliverables: a browser extension that shows the problem on one machine, "
            "and a Raspberry Pi application that acts on it for the whole network.",
            fontsize=9, color=GREY, va="top")

    # Devices sit at the height of the component each one talks to, so the
    # two data flows run straight across instead of crossing each other.

    # ---------------- Home network -------------------------------------
    group(ax, 0.15, 3.30, 4.25, 5.35, "HOME NETWORK")

    box(ax, 0.45, 7.15, 1.70, 1.20, "Phone", ["no extension", "possible"], edge=GREY)
    box(ax, 2.40, 7.15, 1.70, 1.20, "Smart TV", ["no extension", "possible"], edge=GREY)

    box(ax, 0.45, 5.45, 3.65, 1.50, "Laptop — Chrome",
        ["Extension (Manifest V3): captures every",
         "request, hashes identifier locally,",
         "scores page risk 0–100"], edge=BLUE)

    box(ax, 0.45, 3.60, 3.65, 1.50, "Why the Pi is needed",
        ["An extension protects one browser.",
         "DNS covers every device on the",
         "network, including these two."],
        edge=AMBER, face="#FFF8EE")

    # ---------------- Raspberry Pi --------------------------------------
    group(ax, 5.05, 2.55, 4.85, 6.10, "RASPBERRY PI 5")

    box(ax, 5.35, 7.15, 4.25, 1.20, "dns_sinkhole.py  (UDP 53)",
        ["tracker domain → 0.0.0.0",
         "everything else → forwarded"], edge=RED)

    box(ax, 5.35, 5.45, 4.25, 1.30, "app.py  (FastAPI, port 5000)",
        ["/api/telemetry   /api/dns-block",
         "/api/summary    dashboard"], edge=TEAL)

    box(ax, 5.35, 4.05, 2.00, 1.15, "classify.py",
        ["EasyPrivacy", "Tracker Radar", "GeoIP"], edge=NAVY, body_size=7.5)

    box(ax, 7.60, 4.05, 2.00, 1.15, "store.py",
        ["DuckDB", "single writer", "idempotent"], edge=NAVY, body_size=7.5)

    box(ax, 5.35, 2.80, 4.25, 1.00, "dashboard.html",
        ["owners · countries · offshore · PII events · blocks"],
        edge=TEAL, body_size=7.5)

    # ---------------- Internet ------------------------------------------
    group(ax, 10.55, 4.10, 3.75, 4.55, "INTERNET")

    box(ax, 10.85, 7.15, 3.15, 1.20, "Upstream resolver",
        ["1.1.1.1", "(allowed queries only)"], edge=GREY)

    box(ax, 10.85, 5.60, 3.15, 1.25, "Tracker servers",
        ["Google · Meta · Criteo", "Adobe · LiveRamp"], edge=RED)

    box(ax, 10.85, 4.35, 3.15, 0.95, "Reference data",
        ["EasyPrivacy · Tracker Radar · MaxMind"], edge=GREY, body_size=7)

    # ---------------- Flows ---------------------------------------------
    arrow(ax, (4.10, 7.75), (5.35, 7.75), "DNS queries — every device", color=RED, size=7.5)
    arrow(ax, (4.10, 6.20), (5.35, 6.20),
          "telemetry: hostnames,\nrisk scores, hash matches", color=TEAL, size=7.5, offset=0.10)

    arrow(ax, (7.45, 7.15), (7.45, 6.78), "", color=RED)
    ax.text(7.62, 6.95, "blocks logged", ha="left", va="center", fontsize=7, color=RED, zorder=5)

    arrow(ax, (9.60, 7.95), (10.85, 7.95), "forwarded", color=GREY, size=7.5)
    arrow(ax, (10.85, 4.75), (9.60, 4.62), "downloaded once", color=GREY, size=7, offset=0.10)

    arrow(ax, (6.35, 5.45), (6.35, 5.22), "", color=NAVY)
    arrow(ax, (8.60, 5.45), (8.60, 5.22), "", color=NAVY)
    arrow(ax, (7.45, 4.05), (7.45, 3.82), "", color=TEAL)

    # Blocked path, drawn as a crossed-out line to the trackers.
    ax.add_patch(FancyArrowPatch(
        (9.60, 7.25), (10.85, 6.55), arrowstyle="-|>", mutation_scale=13,
        linewidth=1.5, color=RED, linestyle=(0, (4, 2)), zorder=4,
    ))
    ax.text(10.30, 7.12, "blocked", ha="center", fontsize=7.5, color=RED, zorder=7,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.95))
    ax.plot([10.10, 10.34], [6.78, 7.02], color=RED, linewidth=2.2, zorder=6)
    ax.plot([10.10, 10.34], [7.02, 6.78], color=RED, linewidth=2.2, zorder=6)

    # ---------------- Privacy boundary ----------------------------------
    box(ax, 0.15, 1.40, 9.75, 0.95, "PRIVACY BOUNDARY — what never leaves the browser",
        ["The raw email or phone number, and full page URLs (they carry search terms and session ids).",
         "Only hashes are compared; only hostnames are transmitted."],
        edge=AMBER, face="#FFF8EE", title_size=9, body_size=8)

    # ---------------- Research track ------------------------------------
    box(ax, 10.55, 1.40, 3.75, 2.20, "research/  — separate track",
        ["50-site crawl (Playwright)", "→ classify + PII + risk",
         "→ DuckDB → H1–H4 report"],
        edge=GREY, face=LIGHT, title_size=9, body_size=7.5)

    fig.tight_layout()
    fig.savefig("assets/architecture_block_diagram.png", dpi=200, bbox_inches="tight",
                facecolor="white")
    print("[done] assets/architecture_block_diagram.png")


if __name__ == "__main__":
    build()
