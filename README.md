# Traefik Web GUI

A simple, secure web interface for managing Traefik configuration files. Edit, create, delete, and validate YAML configurations through a clean, intuitive dashboard.

🎯 **Perfect for**: Managing Traefik configs on LXC containers, Proxmox setups, or cloud servers without SSH access.

<img width="843" height="862" alt="image" src="https://github.com/user-attachments/assets/7da609eb-068f-4b3e-a3bd-c3122b96c0b4" />

## ✨ Features

- 📝 **Text Editor** - Edit YAML configurations directly in browser
- ➕ **Create Files** - Add new configurations with validation
- 🗑️ **Delete Files** - Remove unwanted configs safely
- ✅ **YAML Validation** - Catch syntax errors before Traefik loads them
- 🔐 **Authentication** - Secure username/password login with hashed passwords
- 👤 **Service User** - Runs as traefik user—no permission headaches
- 📊 **Audit Logging** - Track changes with user and timestamp
- 🌐 **Web-Based** - Access from any browser, no SSH needed
- 💾 **Persistent** - Works seamlessly with git-sync and version control

## 📂 Project Structure

```
traefik-web-gui/
├── app/                      # Core application
│   ├── app.py               # Main Flask application
│   ├── requirements.txt      # Python dependencies
│   └── templates/           # HTML templates
├── docker/                  # Docker testing & deployment
│   ├── Dockerfile          # Alpine Python image with app
│   ├── docker-compose.yml  # Local testing setup
│   ├── DOCKER.md           # Docker testing guide
│   └── .dockerignore
├── install/                 # SystemD service installation
│   ├── install.sh          # Production installer script
│   ├── quick-install.sh    # Download and run the installer on the host
│   ├── traefik-web-gui.service  # SystemD unit file
│   └── QUICK-START.md      # Quick installation guide
├── README.md               # This file
└── data/                    # Runtime (not in git)
    └── password.json       # Hashed passwords (auto-created)
```

## 🚀 Installation Methods

### Option 1: SystemD Service (Production) ⭐ **RECOMMENDED**

For LXC containers, Proxmox, or Ubuntu/Debian servers. This is the **primary deployment method**.

📖 **Full guide**: See [install/QUICK-START.md](install/QUICK-START.md)

**Why SystemD?**
- ✅ Runs as systemd service (auto-restart on failure)
- ✅ Runs as traefik user (with sudo permission to restart Traefik)
- ✅ Logs to journalctl (easy debugging)
- ✅ Integrates with git-sync service
- ✅ Boot-on-startup ready
- ✅ Production-grade setup

**Quick install from GitHub**, on a Debian/Ubuntu LXC as root:
```bash
# curl is needed to download the helper.
curl -fL -o quick-install.sh https://raw.githubusercontent.com/trojak3d/traefik-web-gui/main/install/quick-install.sh
# Review the downloaded script before running it as root.
cat quick-install.sh
bash quick-install.sh
```

The existing `traefik` user and systemd are required. The helper downloads the
necessary files from one `main` branch commit, offers to install missing Debian
packages, runs the installer, and starts or restarts the GUI service. Install
`curl` and `ca-certificates` first if needed. It does not configure a Traefik
router. The branch is mutable; review the installer and files you trust before
running them as root.
See the [quick start](install/QUICK-START.md) for a workstation-copy alternative.

**Access via Traefik** (Recommended):
Configure a Traefik router for remote access:

```yaml
# Add to /etc/traefik/dynamic/traefik-web-gui.yml
http:
  routers:
    traefik-gui:
      rule: Host(`gui.yourdomain.com`)
      entryPoints:
        - websecure
      service: traefik-gui
      tls: {}

  services:
    traefik-gui:
      loadBalancer:
        servers:
          - url: http://localhost:5000
```

Then access: `https://gui.yourdomain.com`

**What happens**:
1. Installer creates `/opt/traefik-web-gui/` and `/var/lib/traefik-web-gui/`
2. The helper starts the service and enables it on boot
3. First access → setup page (change default password)
4. All future logins use your new password

### Option 2: Docker (Local Testing)

Perfect for testing and development. No LXC needed.

```bash
cd traefik-web-gui/docker
docker-compose up
```

Then access **http://localhost:5000**

📖 **Full guide**: See [docker/DOCKER.md](docker/DOCKER.md)

**Features**:
- ✅ Test without deploying
- ✅ Mirrors production setup
- ✅ Persist passwords across restarts
- ✅ Full integration testing

**What happens**:
1. First run → setup page (change default password)
2. Login page → authenticate
3. File manager → edit configs
4. Changes saved to `../test-configs/`

## 🎮 Quick Start

### 1. Access the GUI

**SystemD (Production)**:
- Use Traefik reverse proxy (recommended): `https://gui.yourdomain.com`
- Or SSH tunnel (temporary): `ssh -L 5000:localhost:5000 root@<lxc-ip>` then `http://localhost:5000`

**Docker (Testing)**:
- Direct access: `http://localhost:5000`

### 2. Complete Setup (First Run Only)
On first access, you'll see the setup page:
- **Username**: `admin` (pre-set)
- **Current password**: `admin` (default)
- **New password**: Enter your secure password (minimum 6 characters)
- Click **Complete Setup**

### 3. Login (Subsequent Visits)
- Username: `admin`
- Password: (the one you set during setup)

### 4. Use the GUI
- **Edit**: Click file → edit → save
- **Create**: "+ New File" button → enter name and content → create
- **Delete**: Select file → delete → confirm
- **Restart Traefik**: After config changes, click "🔄 Restart Traefik" to reload

## ⚙️ Configuration

### Environment Variables

The app accepts these environment variables (all optional, defaults work fine):

```bash
export GUI_PORT=5000                           # Port to listen on (default: 5000)
export GUI_HOST=0.0.0.0                        # Bind address (0.0.0.0 = all interfaces; default: 0.0.0.0)
export TRAEFIK_CONFIG_DIR=/etc/traefik/dynamic # Path to Traefik configs (default: /etc/traefik/dynamic)
export GUI_DATA_DIR=/var/lib/traefik-web-gui   # Where passwords and secret key are stored (default: /var/lib/traefik-web-gui)
export GUI_USERNAME=admin                      # Username (changed on setup; default: admin)
# SECRET_KEY: Automatically generated and stored securely on first run. Optionally set to override.
```

**Note on SECRET_KEY:** A cryptographically secure session key is **automatically generated** during the first run and stored in `$GUI_DATA_DIR/.secret_key`. You do not need to manually set this—it's handled for you as a security best practice.

For LXC deployment, these are set via systemd:
```bash
# See install/traefik-web-gui.service
Environment="TRAEFIK_CONFIG_DIR=/etc/traefik/dynamic"
Environment="GUI_PORT=5000"
Environment="GUI_HOST=0.0.0.0"
```

### Changing Your Password

After initial setup, there's currently no in-app way to change the password. To reset:

**Docker**:
```bash
# Stop and remove volumes
docker-compose down -v

# Start again - setup page will appear
docker-compose up
```

**LXC/SystemD**:
```bash
# Stop service
sudo systemctl stop traefik-web-gui

# Remove password file
sudo rm /var/lib/traefik-web-gui/password.json

# Start service
sudo systemctl start traefik-web-gui

# Access via Traefik (see Installation section)
```

## 🔐 Security

- ✅ **Passwords hashed** - Stored securely using scrypt, never plain text
- ✅ **Session cookies** - Automatic logout after inactivity
- ✅ **YAML validation** - Prevents syntax errors in configs
- ✅ **Path protection** - Can't escape the config directory
- ✅ **Audit logging** - All actions logged with username and timestamp
- ✅ **Non-root execution** - Runs as traefik user (not root)
- ✅ **HTTPS recommended** - Use Traefik with TLS and restrict direct access to port 5000
- ✅ **Restart capability** - Can reload Traefik configs with one click (via sudo)

### Production Deployment

**Always use Traefik as a reverse proxy:**

```yaml
# /etc/traefik/dynamic/traefik-web-gui.yml
http:
  routers:
    traefik-gui:
      rule: Host(`gui.yourdomain.com`)
      entryPoints:
        - websecure
      service: traefik-gui-svc
      tls: {}
      # Optional: Add middleware for IP restriction
      middlewares:
        - traefik-gui-auth

  services:
    traefik-gui-svc:
      loadBalancer:
        servers:
          - url: http://localhost:5000

  middlewares:
    traefik-gui-auth:
      ipWhiteList:
        sourceRange:
          - "192.168.1.0/24"  # Restrict to your network
```

**Why not direct port 5000 access?**
- Direct port 5000 access depends on your network and firewall configuration
- Traefik provides HTTPS/TLS termination
- Traefik enables middleware (auth, IP restrictions, etc.)

**Additional Security Steps**:
1. **Monitor logs**: Regularly check for failed login attempts
   ```bash
   journalctl -u traefik-web-gui -f
   ```

2. **Change default password immediately** on first setup

3. **Restrict by IP** using Traefik middleware (see example above)

## 🧪 Testing

### Docker Quick Test
```bash
cd docker
docker-compose up --build
# Wait for "Running on http://0.0.0.0:5000"
# Navigate to http://localhost:5000
```

### Manual Testing
```bash
# Test Python app directly
cd app
pip install -r requirements.txt
python3 app.py

# Access http://localhost:5000 in another terminal
```

## 🔍 Troubleshooting

### Can't access the GUI?

**Docker**:
```bash
# Check container is running
docker ps | grep traefik-web-gui

# View logs
docker logs traefik-web-gui-dev

# Try alternative IP (Windows/Mac)
docker inspect traefik-web-gui-dev | grep IPAddress
```

**LXC**:
```bash
# Check service status
sudo systemctl status traefik-web-gui

# View logs
sudo journalctl -u traefik-web-gui -f

# Check firewall
sudo ufw allow 5000/tcp

# Verify port is listening
sudo ss -tlnp | grep 5000
```

### Stuck on setup page?

```bash
# Docker
docker logs traefik-web-gui-dev | grep ERROR

# LXC
sudo journalctl -u traefik-web-gui -n 50 --no-pager
```

### Login fails after setup?

```bash
# Double-check you entered the correct password
# Try password reset procedure (see above)

# Check permissions (LXC)
ls -la /var/lib/traefik-web-gui/
sudo cat /var/lib/traefik-web-gui/password.json
```

### Changes not saving?

```bash
# Check config directory permissions
ls -la /etc/traefik/dynamic/

# Verify traefik user owns directory (LXC)
sudo chown -R traefik:traefik /etc/traefik/dynamic

# Restart service
sudo systemctl restart traefik-web-gui
```

## 📚 Additional Guides

- **[docker/DOCKER.md](docker/DOCKER.md)** - Detailed Docker testing guide with examples
- **[install/QUICK-START.md](install/QUICK-START.md)** - SystemD installation and usage
- **[docker/DOCKER.md](docker/DOCKER.md#development)** - Live code reload for development

## 🤝 Integration with Other Services

### Git Sync Service

This GUI works great with the `traefik-git-sync` service:

```
GUI edits → Save → Git commit → Git push → Traefik reloads
```

Or:

```
Git push → Git pull → Reload in GUI → Review changes
```

Both services can run simultaneously without conflicts.

## 📦 Dependencies

**Python** (3.11+):
- Flask 2.3.3 - Web framework
- Werkzeug 2.3.7 - WSGI utilities & password hashing
- PyYAML 6.0 - YAML validation

**System**:
- Python 3.11+ with pip
- For Docker: Docker & Docker Compose

**For LXC**:
- Python 3.11+ 
- systemd (standard on Ubuntu/Debian)

## 🛠️ Development

### Running Locally

```bash
cd app
pip install -r requirements.txt
export TRAEFIK_CONFIG_DIR=../test-configs
export GUI_DATA_DIR=../data
mkdir -p ../test-configs ../data
python3 app.py
```

### File Structure

```
app/
├── app.py              # Main application (369 lines)
│   ├── Setup page (verify & persist passwords)
│   ├── Login endpoint
│   ├── File operations (read/edit/create/delete)
│   └── YAML validation
├── requirements.txt    # Dependencies
└── templates/
    ├── index.html      # Main dashboard
    ├── setup.html      # First-run setup
    └── login.html      # Login page
```

## 📄 License

MIT License - See LICENSE file for details.

This project is not affiliated with Traefik Labs but respects their open-source license.

## 🙋 Support

**Found a bug?** Check existing issues or create a new one.

**Have questions?** See the troubleshooting section or specific guide:
- Docker testing: [docker/DOCKER.md](docker/DOCKER.md)
- LXC installation: [install/QUICK-START.md](install/QUICK-START.md)

---

**Ready to get started?** Choose your installation method above! 🚀
