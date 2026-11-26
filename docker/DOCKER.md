# Traefik Web GUI - Docker Testing Guide

Docker wrapper for local testing of Traefik Web GUI with authentication.

## Overview

Test the entire Traefik Web GUI locally without deploying to LXC. Mirrors production closely.

**Important**: Docker is for **testing only**. Production uses systemd service on LXC.

## Prerequisites

- Docker installed and running
- Docker Compose

## Quick Start

### 1. Build and Start

```bash
cd traefik-web-gui
docker-compose up --build
```

Service available at: **http://localhost:5000**

### 2. Initial Setup

On first run, you'll see a setup page:

1. Navigate to `http://localhost:5000`
2. You'll be redirected to setup
3. **Default credentials:**
   - Username: `admin`
   - Current password: `admin`
4. Enter a new password (minimum 6 characters)
5. Click "Complete Setup"
6. You'll be logged into the dashboard

### 3. Test Features

**Login on subsequent runs:**
- Use the username (`admin`) and password you set during setup

**Edit a config:**
1. Click on a `.yml` file in the list
2. Make changes in editor
3. Click "Save"
4. Changes saved to `test-configs/`

**Create a config:**
1. Click "+ New File"
2. Enter filename (e.g., `app.yml`)
3. Enter YAML configuration
4. Click "Create"
5. File appears in list and `test-configs/`

**Delete a config:**
1. Select file
2. Click "Delete"
3. Confirm
4. File removed from `test-configs/`

### 4. Stop the Container

```bash
docker-compose down
```

## Commands

### Start

```bash
docker-compose up              # Foreground (view logs)
docker-compose up -d           # Background
```

### View Logs

```bash
docker logs traefik-web-gui-dev        # Current logs
docker logs -f traefik-web-gui-dev     # Follow logs
```

### Restart

```bash
docker-compose restart
```

### Remove Container

```bash
docker-compose down -v         # Remove volumes too (erases password)
```

## Volumes

| Volume | Purpose | Path in Container |
|--------|---------|-----------------|
| `test-configs` | Traefik config files | `/etc/traefik/dynamic` |
| `data` | Persistent password storage | `/var/lib/traefik-web-gui` |
| `logs` | Application logs | `/var/log` |

## Testing Password Reset

To test first-run setup again:

```bash
# Stop container and remove volumes
docker-compose down -v

# Start fresh - setup will be required again
docker-compose up
```

## Security Notes

- 🔐 Passwords stored in `data/password.json` as scrypt hashes
- 🔑 Session cookies expire with browser/logout
- 📁 Volume mounts simulate LXC permissions
- ✅ YAML validation prevents syntax errors

## Troubleshooting

### Port 5000 Already in Use

```bash
# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Use 5001 instead
```

Then access at `http://localhost:5001`

### Container Won't Start

```bash
docker logs traefik-web-gui-dev
# Check for errors - usually permission or missing directories
```

### Can't Access http://localhost:5000

```bash
# Verify container is running
docker ps | grep traefik-web-gui

# Try Docker Desktop's alternative IP (on Windows/Mac)
docker inspect traefik-web-gui-dev | grep '"IPAddress"'
# Access using that IP instead
```

### Lost Password

If you forgot the password set during setup:

```bash
docker-compose down -v    # Remove everything including password file
docker-compose up         # Setup page will appear again
```

## Development

### Live Code Reload

Uncomment the app mount in docker-compose.yml to edit Python code and see changes instantly:

```yaml
volumes:
  - .:/app  # Uncomment for development
```

Then access http://localhost:5000 - changes to `app.py` will auto-reload.

### View File Permissions

```bash
docker exec traefik-web-gui-dev ls -la /var/lib/traefik-web-gui/
docker exec traefik-web-gui-dev cat /var/lib/traefik-web-gui/password.json
```

## Full Integration Test

To test with actual Traefik running in Docker:

1. Uncomment the Traefik service in docker-compose.yml (at the bottom)
2. Run `docker-compose up`
3. Traefik dashboard: http://localhost:8080
4. Web GUI: http://localhost:5000

Changes in the GUI will update files that Traefik monitors.
