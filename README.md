# Traefik Web GUI

A simple, secure web interface for managing Traefik configuration files. Edit, create, delete, and validate YAML configurations through a clean, intuitive dashboard.

🎯 **Perfect for**: Managing Traefik configs on LXC containers, Proxmox setups, or cloud servers without SSH access.

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
│   ├── traefik-web-gui.service  # SystemD unit file
│   └── QUICK-START.md      # Quick installation guide
├── README.md               # This file
└── data/                    # Runtime (not in git)
    └── password.json       # Hashed passwords (auto-created)
```

## 🚀 Installation Methods

### Option 1: Docker (Local Testing)

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

### Option 2: SystemD Service (Production)

For LXC containers or Ubuntu/Debian servers.

```bash
# SSH into your LXC
ssh root@<your-lxc-ip>

# Copy and run installer
cd /opt
scp -r <your-workstation>:/path/to/traefik-web-gui .
cd traefik-web-gui/install
chmod +x install.sh
sudo ./install.sh

# Start service
sudo systemctl start traefik-web-gui

# Access
# http://<your-lxc-ip>:5000
```

📖 **Full guide**: See [install/QUICK-START.md](install/QUICK-START.md)

**Features**:
- ✅ Runs as systemd service (auto-restart)
- ✅ Runs as traefik user (correct permissions)
- ✅ Logs to journalctl (easy debugging)
- ✅ Integrates with git-sync service
- ✅ Boot-on-startup ready

**What happens**:
1. Installer creates `/opt/traefik-web-gui/` and `/var/lib/traefik-web-gui/`
2. Service starts on boot
3. First access → setup page (change default password)
4. All future logins use your new password

## 🎮 Quick Start (Either Method)

### 1. Access the GUI
- **Docker**: http://localhost:5000
- **LXC**: http://<your-lxc-ip>:5000

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

## ⚙️ Configuration

### Environment Variables

The app accepts these environment variables (optional, defaults work fine):

```bash
export GUI_PORT=5000                           # Port to listen on
export GUI_HOST=0.0.0.0                        # Bind address (0.0.0.0 = all interfaces)
export TRAEFIK_CONFIG_DIR=/etc/traefik/dynamic # Path to Traefik configs
export GUI_DATA_DIR=/var/lib/traefik-web-gui   # Where passwords are stored
export GUI_USERNAME=admin                      # Username (changed on setup)
export SECRET_KEY=change-me-for-production     # Flask session secret
```

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

# Access and re-run setup
# http://<your-lxc-ip>:5000
```

## 🔐 Security

- ✅ **Passwords hashed** - Stored securely using scrypt, never plain text
- ✅ **Session cookies** - Automatic logout after inactivity
- ✅ **YAML validation** - Prevents syntax errors in configs
- ✅ **Path protection** - Can't escape the config directory
- ✅ **Audit logging** - All actions logged with username and timestamp
- ✅ **Non-root execution** - Runs as traefik user (not root)
- ✅ **Local-only by default** - Use firewall/Traefik to expose safely

### Production Tips

1. **Use HTTPS**: Put this behind Traefik with TLS certificates
   ```yaml
   # In Traefik dynamic config
   traefik-web-gui:
     service: traefik-web-gui-svc
     rule: "Host(`gui.example.com`)"
     tls:
       certResolver: letsencrypt
   ```

2. **Restrict access**: Use Traefik middleware to limit IPs
   ```yaml
   ipwhitelist:
     sourceRange:
       - "192.168.1.0/24"
       - "10.0.0.1"
   ```

3. **Monitor logs**: Regularly check for failed login attempts
   ```bash
   journalctl -u traefik-web-gui -f
   ```

4. **Change default password immediately** on first setup

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
