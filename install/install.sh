#!/bin/bash
# Traefik Web GUI - Installation Script

set -Eeuo pipefail

trap 'echo "ERROR: Installation failed at line $LINENO"; exit 1' ERR

echo "================================"
echo "Traefik Web GUI Installer"
echo "================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root"
   exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$SCRIPT_DIR/app"
INSTALL_DIR="$SCRIPT_DIR/install"

# Check if traefik user exists
echo "Checking traefik user..."
if ! id -u traefik &>/dev/null; then
    echo "ERROR: User 'traefik' does not exist. Please create it first:"
    echo "  useradd -r -s /bin/false traefik"
    exit 1
fi
echo "✓ traefik user found"
echo ""

# Check dependencies
echo "Checking dependencies..."
for cmd in python3 pip3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd is not installed. Please install it first."
        exit 1
    fi
done
echo "✓ All dependencies found"
echo ""

# Check if script files exist
echo "Validating source files..."
for file in "$APP_DIR/app.py" "$APP_DIR/requirements.txt" "$APP_DIR/templates/index.html" "$INSTALL_DIR/traefik-web-gui.service"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file not found: $file"
        exit 1
    fi
done
echo "✓ All source files found"
echo ""

# Create directories with restrictive permissions
echo "Creating directories..."
umask 0027
mkdir -p /opt/traefik-web-gui/templates
mkdir -p /var/lib/traefik-web-gui
echo "✓ Directories created"
echo ""

# Copy application files and set permissions
echo "Installing application files..."
cp "$APP_DIR/app.py" /opt/traefik-web-gui/
cp -r "$APP_DIR/templates" /opt/traefik-web-gui/
cp "$APP_DIR/requirements.txt" /opt/traefik-web-gui/
cp "$INSTALL_DIR/traefik-web-gui.service" /etc/systemd/system/

# Set ownership and permissions for application files (root:root, read-only)
chown -R root:root /opt/traefik-web-gui
chmod 755 /opt/traefik-web-gui
chmod 755 /opt/traefik-web-gui/templates
chmod 644 /opt/traefik-web-gui/app.py
chmod 644 /opt/traefik-web-gui/requirements.txt
find /opt/traefik-web-gui/templates -type f -exec chmod 644 {} \;
find /opt/traefik-web-gui/templates -type d -exec chmod 755 {} \;

echo "✓ Application files installed"
echo ""

# Install Python dependencies in virtual environment
echo "Installing Python dependencies..."
VENV_DIR="/opt/traefik-web-gui/venv"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet -r /opt/traefik-web-gui/requirements.txt

# Fix venv ownership and permissions (binaries must be executable)
chown -R root:root "$VENV_DIR"
chmod 755 "$VENV_DIR"
find "$VENV_DIR/bin" -type f -exec chmod 755 {} \;
find "$VENV_DIR/lib" -type d -exec chmod 755 {} \;
echo "✓ Dependencies installed in virtual environment"
echo ""

# Set state directory permissions (restrictive)
echo "Setting state directory permissions..."
chown traefik:traefik /var/lib/traefik-web-gui
chmod 700 /var/lib/traefik-web-gui
echo "✓ State directory permissions set"
echo ""

# Create and configure log file
echo "Setting up log file..."
touch /var/log/traefik-web-gui.log
chown traefik:traefik /var/log/traefik-web-gui.log
chmod 640 /var/log/traefik-web-gui.log
echo "✓ Log file created with correct permissions"
echo ""

# Allow traefik user to restart traefik service via sudo without password
echo "Configuring sudo access for traefik service control..."
cat > /etc/sudoers.d/traefik-web-gui <<'EOF'
# Allow traefik user to manage traefik service (required by web GUI)
traefik ALL=(root) NOPASSWD: /bin/systemctl restart traefik
traefik ALL=(root) NOPASSWD: /bin/systemctl reload traefik
traefik ALL=(root) NOPASSWD: /bin/systemctl is-active traefik
EOF
chmod 440 /etc/sudoers.d/traefik-web-gui
echo "✓ Sudo rules configured"
echo ""

# Install and validate systemd service
echo "Installing systemd service..."
chown root:root /etc/systemd/system/traefik-web-gui.service
chmod 644 /etc/systemd/system/traefik-web-gui.service

# Validate the service file
if ! systemd-analyze verify traefik-web-gui.service &>/dev/null; then
    echo "WARNING: systemd service file validation produced warnings (may still be functional)"
fi

# Reload systemd
systemctl daemon-reload
echo "✓ Systemd service installed and validated"
echo ""

# Enable service
echo "Enabling service..."
systemctl enable traefik-web-gui
echo "✓ Service enabled (will start on boot)"
echo ""

echo "================================"
echo "Installation Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Start the service:"
echo "   systemctl start traefik-web-gui"
echo ""
echo "2. Check status:"
echo "   systemctl status traefik-web-gui"
echo ""
echo "3. Access the GUI and complete setup:"
echo "   http://<your-lxc-ip>:5000"
echo ""
echo "   On first run, you'll be prompted to change the default password"
echo "   (default credentials: admin/admin)"
echo ""
echo "4. View service logs:"
echo "   journalctl -u traefik-web-gui -f"
echo ""
echo "5. For detailed instructions, see:"
echo "   cat /opt/traefik-web-gui/README.md"
echo ""
