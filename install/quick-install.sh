#!/bin/bash
# Download and install Traefik Web GUI on a systemd host.

set -Eeuo pipefail

trap 'echo "ERROR: Quick installation failed at line $LINENO" >&2' ERR

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run this script as root (or with sudo)." >&2
    exit 1
fi

if ! id -u traefik >/dev/null 2>&1; then
    echo "ERROR: The existing Traefik service user 'traefik' was not found." >&2
    exit 1
fi

if ! command -v dpkg-query >/dev/null 2>&1; then
    echo "ERROR: This helper requires a Debian or Ubuntu system with dpkg." >&2
    exit 1
fi

missing_packages=()
for package in ca-certificates curl python3 python3-pip python3-venv sudo; do
    status="$(dpkg-query -W -f='${Status}' "$package" 2>/dev/null || true)"
    if [[ "$status" != "install ok installed" ]]; then
        missing_packages+=("$package")
    fi
done

if ((${#missing_packages[@]})); then
    echo "Missing packages: ${missing_packages[*]}"
    if ! command -v apt-get >/dev/null 2>&1; then
        echo "ERROR: apt-get is required to install missing packages." >&2
        exit 1
    fi
    if ! read -r -p "Install these packages with apt-get? [y/N] " answer; then
        echo "ERROR: No response received; packages were not installed." >&2
        exit 1
    fi
    case "$answer" in
        y|Y|yes|YES|Yes) ;;
        *)
            echo "Installation cancelled; packages were not installed." >&2
            exit 1
            ;;
    esac
    apt-get update
    apt-get install -y "${missing_packages[@]}"
fi

for cmd in curl python3 pip3 sudo systemctl; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' is missing after checking packages." >&2
        exit 1
    fi
done

umask 077
staging_dir="$(mktemp -d)"
trap 'rm -rf -- "$staging_dir"' EXIT

echo "Resolving the latest main branch commit..."
commit="$(curl --fail --silent --show-error --location --retry 3 \
    https://api.github.com/repos/trojak3d/traefik-web-gui/commits/main |
    python3 -c 'import json, re, sys; sha = json.load(sys.stdin)["sha"]; sys.exit("Invalid commit SHA") if not re.fullmatch(r"[0-9a-f]{40}", sha) else print(sha)')"
echo "Downloading installation files at $commit..."

mkdir -p "$staging_dir/app/templates" "$staging_dir/install"
for file in \
    app/app.py \
    app/requirements.txt \
    app/templates/index.html \
    app/templates/login.html \
    app/templates/setup.html \
    install/install.sh \
    install/traefik-web-gui.service; do
    curl --fail --silent --show-error --location --retry 3 \
        "https://raw.githubusercontent.com/trojak3d/traefik-web-gui/$commit/$file" \
        --output "$staging_dir/$file"
done

bash "$staging_dir/install/install.sh"

# The installer creates the venv under a restrictive umask; its service user must read it.
chmod -R a+rX /opt/traefik-web-gui/venv

echo "Starting or restarting the web GUI service..."
if ! systemctl restart traefik-web-gui || ! systemctl is-active --quiet traefik-web-gui; then
    echo "ERROR: The web GUI service did not start. Check: journalctl -u traefik-web-gui -n 50 --no-pager" >&2
    exit 1
fi
echo "Web GUI service is active. Configure a Traefik route to access it remotely."
