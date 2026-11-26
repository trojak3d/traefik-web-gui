# Traefik Web GUI - Quick Start Guide

Simple web interface with authentication for managing Traefik configuration files.

## 🎯 What It Does

- 📝 **Edit configs** - Text editor for YAML files
- ➕ **Create files** - Add new configuration files
- 🗑️ **Delete files** - Remove configurations
- ✅ **YAML validation** - Catches syntax errors before saving
- 🔐 **Authentication** - Username/password login (hashed passwords)
- 👤 **Run as traefik** - No permission issues
- 📊 **Audit logging** - Track who changed what

## ⚡ Install directly from GitHub

On a Debian/Ubuntu LXC, as root, ensure the existing `traefik` user and systemd
are available. `curl` and `ca-certificates` must be installed to download the
helper. Then run:

```bash
curl -fL -o quick-install.sh https://raw.githubusercontent.com/trojak3d/traefik-web-gui/main/install/quick-install.sh
# Review the downloaded script before running it as root.
cat quick-install.sh
bash quick-install.sh
```

The helper checks for required packages and asks before installing any missing
ones with `apt-get`. Declining stops the installation. It downloads only the
files needed by the installer, all from the same
`main` branch commit, into a temporary directory. It runs the existing installer,
fixes virtual-environment read/traverse permissions for the service user, and
starts or restarts the GUI service. It does not create the `traefik` user or
configure a Traefik router. GitHub's `main` branch can change: review the code
you trust before running it as root.

Configure a Traefik router as described in [Network Access](#-network-access)
before accessing the GUI remotely. Check the service with
`systemctl status traefik-web-gui` and `journalctl -u traefik-web-gui -n 50 --no-pager`.

## Workstation-copy installation

### 0. Prerequisites

Ensure your LXC has the required packages:
```bash
ssh root@<your-lxc-ip> 'apt-get update && apt-get install -y python3-pip python3-venv'
```

**If you're using a regular user account:**
```bash
ssh -t <your-user>@<your-lxc-ip> 'sudo apt-get update && sudo apt-get install -y python3-pip python3-venv'
```

Also ensure the `traefik` user exists:
```bash
ssh root@<your-lxc-ip> 'id traefik'
```

If not found, ensure Traefik and its service user are installed before proceeding.

### 1. Copy files from your workstation

**From within the repo root directory:**

**If you have direct root SSH access (easiest):**
```bash
# Create staging directory on LXC
ssh root@<your-lxc-ip> 'mkdir -p /opt/setup-gui'

# Copy only necessary files
scp -r app root@<your-lxc-ip>:/opt/setup-gui/
scp -r install root@<your-lxc-ip>:/opt/setup-gui/
```

**If you SSH as a regular user (with sudo):**
```bash
# Create staging directory on LXC (allocate terminal with -t for sudo prompt)
ssh -t <your-user>@<your-lxc-ip> 'sudo mkdir -p /opt/setup-gui && sudo chown $USER /opt/setup-gui'

# Copy only necessary files (now writable by your user)
scp -r app <your-user>@<your-lxc-ip>:/opt/setup-gui/
scp -r install <your-user>@<your-lxc-ip>:/opt/setup-gui/
```

### 2. Fix line endings and run installer

**SSH to the LXC and run the installer:**
```bash
ssh root@<your-lxc-ip>

# Then inside the LXC:
cd /opt/setup-gui/install

# Fix Windows line endings if needed
sed -i 's/\r$//' install.sh

# Run installer (creates directories, installs dependencies, sets up systemd, creates log file)
chmod +x install.sh
./install.sh

# Clean up staging directory
cd /
rm -rf /opt/setup-gui
```

**Or as a single SSH command (root):**
```bash
ssh root@<your-lxc-ip> 'cd /opt/setup-gui/install && sed -i "s/\r$//" install.sh && chmod +x install.sh && ./install.sh && cd / && rm -rf /opt/setup-gui'
```

**Security notes:**
- ⚠️ Only necessary files (`app/` and `install/`) are copied
- ⚠️ Staging directory is removed after installation
- ⚠️ Verify SSH host key before connecting
- ⚠️ Installer runs as root - ensure you trust the source
- ⚠️ Line ending fix is needed when copying from Windows
- ⚠️ Installer creates log file `/var/log/traefik-web-gui.log` with appropriate permissions

### 3. Start the service
```bash
systemctl start traefik-web-gui
```

**Verify it's running:**
```bash
systemctl status traefik-web-gui
journalctl -u traefik-web-gui -n 10
```

### 4. Access the GUI and complete setup

**Test locally on the LXC:**
```bash
curl http://localhost:5000
```

For remote access, configure the Traefik router in
[Network Access](#-network-access) and open its HTTPS hostname in your browser.

**On first run, complete the setup:**
1. You'll be redirected to the setup page
2. **Default credentials:**
   - Username: `admin`
   - Current password: `admin`
3. Enter a new password (minimum 6 characters)
4. Click **Complete Setup**
5. You'll be logged into the dashboard

**On subsequent visits, use the new password you set.**

## 🌐 Network Access

**Local access on the LXC:**
```bash
curl http://localhost:5000
```

**Remote access from your workstation:**

If you can SSH to the LXC but can't directly access port 5000, use SSH port forwarding:

```bash
# From your workstation (Windows PowerShell or WSL):
ssh -L 5000:localhost:5000 root@<your-lxc-ip>

# Keep this terminal open, then access:
# http://localhost:5000
```

**Or route through Traefik** (if you want permanent external access):
Add a router to `/etc/traefik/dynamic/traefik-web-gui.yml`:

```yaml
http:
  routers:
    gui:
      rule: Host(`gui.t3d.local`)  # or your domain
      entryPoints:
        - websecure
      service: gui-backend
      tls: {}
  
  services:
    gui-backend:
      loadBalancer:
        servers:
          - url: http://localhost:5000
```

Direct port 5000 access depends on your network and firewall configuration.
Use a hostname that resolves to Traefik and configure a suitable TLS certificate.

## 🎮 Using the GUI

### Login
1. Enter username (`admin`) and password (the one you set during setup)
2. Click **Login**
3. Access file manager

### Edit a File
1. Click file in left panel
2. Make changes in editor
3. Click **Save**

### Create a New File
1. Click **+ New File**
2. Enter filename (must end in `.yml` or `.yaml`)
3. Enter your configuration
4. Click **Create**

### Delete a File
1. Select the file
2. Click **Delete**
3. Confirm in popup

### Logout
Click **Logout** button in top-right corner

## 🔐 Changing Your Password

After initial setup, there's currently no in-app way to change the password. To reset:

```bash
# Stop the service
systemctl stop traefik-web-gui

# Remove the password file (this will trigger setup on next run)
rm /var/lib/traefik-web-gui/password.json

# Start the service
systemctl start traefik-web-gui

# Access http://<your-lxc-ip>:5000 and complete setup again with new password
```

## ⚙️ Configuration via Environment

The service accepts environment variables for configuration:

```bash
# Environment variables (all optional—defaults work fine)
export GUI_PORT=5000                           # Port to listen on (default: 5000)
export GUI_HOST=0.0.0.0                        # Bind address (default: 0.0.0.0)
export TRAEFIK_CONFIG_DIR=/etc/traefik/dynamic # Path to Traefik configs (default: /etc/traefik/dynamic)
export GUI_DATA_DIR=/var/lib/traefik-web-gui   # Data directory for passwords and secret key (default: /var/lib/traefik-web-gui)
export GUI_USERNAME=admin                      # Username (default: admin)
# SECRET_KEY is automatically generated on first run—no manual configuration needed
```

Most defaults work fine. The only critical one is:
- **`TRAEFIK_CONFIG_DIR`** - Where your Traefik configs are stored (default: `/etc/traefik/dynamic`)

**Note:** The Flask session secret key is automatically generated and stored securely during the first run—you don't need to set it manually.

## 🔍 Verification

```bash
# Service running?
systemctl status traefik-web-gui

# View logs
journalctl -u traefik-web-gui -f

# Test access
curl http://localhost:5000
```

## 🆘 Troubleshooting

**Can't access the GUI?**
- Check firewall: `ufw allow 5000/tcp`
- Check service: `systemctl status traefik-web-gui`
- Check logs: `journalctl -u traefik-web-gui -n 50`

**Stuck on setup page?**
- Verify service has write access: `ls -la /var/lib/traefik-web-gui/`
- Check permissions: `systemctl status traefik-web-gui`

**Login fails?**
- Use the password you set during setup (not `admin/admin`)
- Check logs: `journalctl -u traefik-web-gui -f`

**Permission denied when saving?**
- Service runs as traefik user
- Verify traefik owns config dir: `ls -la /etc/traefik/dynamic/`
- Check service status: `systemctl status traefik-web-gui`

**Changes not appearing?**
- Refresh browser (Ctrl+F5)
- Check git-sync service isn't interfering
- Verify file was saved

## 📋 Common Tasks

```bash
systemctl stop traefik-web-gui           # Stop service
systemctl restart traefik-web-gui        # Restart service
journalctl -u traefik-web-gui -f         # Watch logs
systemctl status traefik-web-gui         # Check status
```

## 🔐 Security

✅ **Passwords hashed** - Stored securely using scrypt, never in plain text
✅ **Session cookies** - Automatic logout after inactivity
✅ **YAML validation** - Prevents syntax errors
✅ **File path protection** - Can't escape config directory
✅ **Audit logging** - All actions logged with username
✅ **Local network** - Use firewall to restrict access
✅ **HTTPS** - Use Traefik reverse proxy for TLS

## 🎯 With Git Sync Service

Combine with `traefik-git-sync` for complete workflow:

```
GUI edits → Save → Git sync picks up → Traefik reloads
```

Or:

```
Git push → Git sync → Reload in GUI → Review
```

Both services work together seamlessly!

---

**Ready to use!** For more details, see [README.md](README.md).
