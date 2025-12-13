# 🚀 Deployment Guide: FastAPI on DigitalOcean

This guide documents the infrastructure setup, security configuration, and automated CI/CD pipeline for the Cencad FastAPI backend.

## **Phase 1: Infrastructure Setup (The Droplet)**

1.  **Create Droplet:**

      * Log in to DigitalOcean.
      * Select **Create Droplet**.
      * **Region:** Choose nearest to users (e.g., Toronto/New York).
      * **Image:** Select **Marketplace** -\> **Docker** (This installs Docker & Ubuntu 22.04 automatically).
      * **Size:** Basic ($6/mo or higher).
      * **Authentication:** Select "SSH Key" (Recommended) or Password.

2.  **Clone Repository:**
    SSH into the server and clone the code to the specific folder used in our scripts.

    ```bash
    ssh root@<DROPLET_IP>
    git clone https://github.com/your-org/cencad-fastapi.git
    cd cencad-fastapi
    ```

## **Phase 2: Networking & HTTPS (DNS + Caddy)**

### 1\. DNS Configuration

Go to your domain provider (GoDaddy, Namecheap, Cloudflare) and set an **A Record**:

  * **Host:** `api` (or `@` for root domain)
  * **Value:** `<YOUR_DROPLET_IP>`
  * **TTL:** Automatic/1 hour.

### 2\. Configure Firewall

By default, the Droplet firewall blocks web traffic. Open ports 80 (HTTP) and 443 (HTTPS).

```bash
ufw allow 80
ufw allow 443
ufw allow 22    # IMPORTANT: Keep SSH open!
ufw enable      # Turn firewall on
ufw reload
```

### 3\. Setup Caddy (Reverse Proxy)

Caddy sits in front of Docker to handle HTTPS/SSL automatically.

**A. Install Caddy:**

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

**B. Configure Caddy:**
Edit the config file: `nano /etc/caddy/Caddyfile`

```text
api.cencad.ca {
    reverse_proxy localhost:8080
}
```

**C. Restart Caddy:**

```bash
systemctl reload caddy
```

-----

## **Phase 3: Secrets Management**

Create the production environment file directly on the server. This file is **never** committed to GitHub.

1.  **Create the file:**

    ```bash
    nano /root/cencad-fastapi/.env
    ```

2.  **Paste Production Variables:**

    ```ini
    # MongoDB (Ensure Certifi is used in code)
    MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cencad-prod
    MONGODB_DB=proddb

    # Security
    JWT_SECRET_KEY=your_super_secret_key
    JWT_ALGORITHM=HS256

    # Frontend (For CORS and Email Links)
    FRONTEND_URL=https://cencad-frontend.vercel.app

    # Mailtrap
    MAILTRAP_API_TOKEN=your_token
    ```

-----

## **Phase 4: CI/CD Automation (GitHub Actions)**

This sets up the pipeline so pushing to `main` automatically updates the server.

### 1\. Generate Deploy Keys (Local Machine)

Run this in your local terminal (PowerShell/Bash):

```bash
ssh-keygen -t ed25519 -C "github-actions" -f gh_action_key
```

  * This creates `gh_action_key` (Private) and `gh_action_key.pub` (Public).

### 2\. Authorize the Key on the Droplet

Copy the content of `gh_action_key.pub` and run this **on the Droplet**:

```bash
echo "PASTE_PUBLIC_KEY_CONTENT_HERE" >> ~/.ssh/authorized_keys
```

### 3\. Add Secrets to GitHub

Go to **GitHub Repo -\> Settings -\> Secrets and variables -\> Actions**. Add these 3 secrets:

| Secret Name | Value |
| :--- | :--- |
| `DROPLET_HOST` | `<YOUR_DROPLET_IP>` |
| `DROPLET_USERNAME` | `root` |
| `SSH_PRIVATE_KEY` | Paste the **entire** content of the `gh_action_key` file. |

### 4\. Create the Workflow File

Create `.github/workflows/deploy.yml` in your project:

```yaml
name: Deploy to DigitalOcean

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.DROPLET_HOST }}
          username: ${{ secrets.DROPLET_USERNAME }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            # 1. Navigate to project folder
            cd /root/cencad-fastapi

            # 2. Pull latest code
            git pull origin main

            # 3. Rebuild Docker Image
            docker build -t cencad-api .

            # 4. Stop old container
            docker rm -f cencad_app || true

            # 5. Run new container
            # Maps port 8080 to match Caddy
            # Uses .env file from the server
            docker run -d \
              --name cencad_app \
              --restart always \
              --env-file .env \
              -p 8080:8080 \
              cencad-api

            # 6. Clean up
            docker image prune -f
```

-----

## **Troubleshooting**

  * **Site not loading?** Check firewall: `ufw status`.
  * **502 Bad Gateway?** Docker crashed. Check logs: `docker logs cencad_app`.
  * **SSL Error?** Check Caddy: `systemctl status caddy`.
  * **Database connection fail?** Ensure `tlsCAFile=certifi.where()` is in your Python `MongoClient` setup.