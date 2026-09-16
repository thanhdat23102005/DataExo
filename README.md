# DataExodus

Most websites send data about you to companies you have never heard of,
in countries you did not choose. DataExodus makes that visible, and then
blocks it.

It is two things that work together:

| | What it does | Where it runs |
|---|---|---|
| **`extension/`** | Watches every request your browser makes. Names the company behind each destination, scores the page's privacy risk 0–100, and detects your email or phone leaving as a **hash** | Chrome, on your laptop |
| **`pi/`** | Collects what the extension sees, adds owner and country attribution, and blocks tracker domains **for every device on the network** by DNS | Raspberry Pi |

The extension shows you the problem on one machine. The Pi does something
about it for the phones, TVs and apps a browser extension can never reach.

`research/` holds the separate 50-site measurement study this project grew
out of — see [research/README.md](research/README.md).

---

## Why hashes matter

A tracker rarely sends `you@example.com` across the wire. It sends
`973dfe463ec857…`, the SHA-256 of it, and calls that anonymised.

It is not. The same email always produces the same hash, so that value is
a stable name for you that follows you between sites. The extension proves
this: it hashes your identifier locally, every way a tracker's pipeline
would normalise it first, then watches for those hashes in outbound
traffic.

Your raw identifier never leaves the browser. Only hashes are ever
compared, and the Pi is never sent the identifier at all.

---

## 1. The extension

**Install**

1. `chrome://extensions`
2. Turn on **Developer mode**
3. **Load unpacked** → select the `extension/` folder
4. Click the shield icon and enter the email or phone you want watched

**What you get**

- Which companies collect from the page you are on, and what country they sit in
- A 0–100 risk score for the page
- A loud alert when your identifier reaches a **third party** — the covert
  case. Sending it to the site you are actually using is recorded but not
  treated as a leak, because you chose to do that
- Known malware and phishing domains redirected to a warning page

**Identifier handling.** Entering `0412 345 678` hashes the digits-only
form, the `+61` form and the `61` form as well, across MD5, SHA-1, SHA-256
and SHA-512 — a tracker hashes what its own pipeline normalised, not what
you typed. Gmail dot and `+tag` variants are covered too. Anything shorter
than six characters is rejected, because a two-digit string matches ids
and timestamps in almost every URL.

---

## 2. The Pi application

```bash
cd pi
./setup_pi.sh                        # or: ./setup_pi.sh --geoip-key YOUR_KEY
./.venv/bin/python app.py            # dashboard + telemetry, port 5000
sudo ./.venv/bin/python dns_sinkhole.py   # network-wide blocking, port 53
```

A free MaxMind key (https://www.maxmind.com/en/geolite2/signup) enables
country attribution. Without it everything else still works; the Pi just
cannot say where a destination is.

Then:

- open `http://<pi-address>:5000` for the dashboard
- in the extension popup's settings, set the gateway to
  `http://<pi-address>:5000/api/telemetry`
- to block for every device, point your router's DNS at the Pi

**Run it on boot:** `./setup_pi.sh --install-services` writes systemd units
for both services. The DNS one uses `CAP_NET_BIND_SERVICE` so it can bind
port 53 without running as root.

### What the Pi adds that the extension cannot

- **Country attribution.** The extension knows roughly who owns a domain;
  the Pi resolves it and looks up the country, so offshore transfers under
  the Privacy Act's APP 8 become visible.
- **Whole-network blocking.** DNS covers every device on the Wi-Fi.
- **History.** The extension forgets a tab when you close it. The Pi keeps
  a record.

### Two lists, two questions

Telling you a destination *is a tracker* and *black-holing it at the DNS
layer* are different decisions, so they use different sources.

**EasyPrivacy** answers the first. It is a request-level list: its rules
carry paths and resource types, because a browser extension can act on
those. `||wikipedia.org/beacon/` means Wikipedia serves a beacon at one
path — not that Wikipedia is a tracker. Only whole-domain rules are read.

**A hosts-format list** answers the second, because it is written for DNS
in the first place. A wrong answer here takes a site off the air for every
device on the network, so a list built for name-level blocking is the only
safe input.

Some domains are deliberately absent from the DNS list even though the
extension flags them — `connect.facebook.net` is the common one, because
blocking it breaks "Log in with Facebook" across the web. The dashboard
still shows it as a Facebook-owned tracker.

### What the Pi receives

Hostnames, tracker names, risk scores and hash-match events. **Not** full
page URLs — those carry search terms and session ids, and this is a
privacy tool. Telemetry can be switched off entirely in the extension's
settings.

---

## Layout

```
DataExo/
├── extension/              Chrome MV3 extension
│   ├── service-worker.js   Request capture, classification, risk, PII matching
│   ├── trackers.js         Domain → company, country, category
│   ├── md5.js              MD5 (WebCrypto has SHA but no MD5)
│   ├── warning.html        Malware block page
│   └── popup/              Onboarding, dashboard, settings
├── pi/                     Raspberry Pi application
│   ├── app.py              Telemetry API + dashboard (port 5000)
│   ├── dns_sinkhole.py     Network-wide DNS blocking (port 53)
│   ├── classify.py         Tracker / owner / country lookup
│   ├── store.py            DuckDB storage
│   ├── dashboard.html
│   ├── fetch_reference_data.py
│   └── setup_pi.sh
├── research/               The 50-site measurement study
└── submission/             Project charter, proposal, diagrams
```

## Ethics and scope

Only public pages are observed, and only this machine's own traffic. No
logins, no authentication, no attacks, no attempt to evade anything. This
is passive observation of what a browser already sends, in the tradition
of academic tracking studies such as Princeton's WebTAP.

The identifier watched for leaks is the user's own, entered by them, and
is never transmitted anywhere.

Risk scores are a self-designed heuristic, not a published model. Country
adequacy is a simplification of a legal question, not legal advice.
