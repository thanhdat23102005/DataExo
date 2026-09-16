#!/usr/bin/env bash
# First-time setup for the DataExodus Pi application.
#
#   ./setup_pi.sh                       # app only
#   ./setup_pi.sh --geoip-key YOUR_KEY  # adds country attribution
#
# Installs into a local venv, downloads the reference data, and prints the
# two commands that start the services. Nothing is installed system-wide and
# no systemd unit is written without you asking - see --install-services.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

GEOIP_KEY=""
INSTALL_SERVICES=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --geoip-key) GEOIP_KEY="$2"; shift 2 ;;
    --install-services) INSTALL_SERVICES=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv ..."
  python3 -m venv .venv
fi
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.txt
echo "Dependencies installed."

mkdir -p data/blocklists
if [[ -n "$GEOIP_KEY" ]]; then
  ./.venv/bin/python fetch_reference_data.py --geoip-key "$GEOIP_KEY"
else
  ./.venv/bin/python fetch_reference_data.py
fi

if [[ "$INSTALL_SERVICES" == "1" ]]; then
  DIR="$(pwd)"
  USER_NAME="$(id -un)"
  echo "Writing systemd units (requires sudo) ..."

  sudo tee /etc/systemd/system/dataexodus-app.service > /dev/null <<EOF
[Unit]
Description=DataExodus Pi application
After=network.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${DIR}
ExecStart=${DIR}/.venv/bin/python app.py --host 0.0.0.0 --port 5000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  # CAP_NET_BIND_SERVICE lets the sinkhole bind port 53 without running the
  # whole process as root.
  sudo tee /etc/systemd/system/dataexodus-dns.service > /dev/null <<EOF
[Unit]
Description=DataExodus DNS sinkhole
After=dataexodus-app.service

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${DIR}
AmbientCapabilities=CAP_NET_BIND_SERVICE
ExecStart=${DIR}/.venv/bin/python dns_sinkhole.py --port 53
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  sudo systemctl enable --now dataexodus-app dataexodus-dns
  echo "Services enabled. Check with: systemctl status dataexodus-app dataexodus-dns"
else
  cat <<'EOF'

Setup complete. Start the two services:

  ./.venv/bin/python app.py                      # dashboard + telemetry, port 5000
  sudo ./.venv/bin/python dns_sinkhole.py        # network-wide blocking, port 53

Then:
  - open http://<pi-address>:5000 for the dashboard
  - in the extension popup, set the gateway to http://<pi-address>:5000/api/telemetry
  - to block for every device, set your router's DNS server to the Pi's address

Run with --install-services to have systemd start both on boot instead.
EOF
fi
