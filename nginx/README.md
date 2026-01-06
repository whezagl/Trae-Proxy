# Nginx Proxy Manager for Trae-Proxy

## What is Nginx Proxy Manager? (In Simple Terms)

Imagine you have a house with many doors. **Nginx Proxy Manager (NPM)** is like a smart doorman that:
- Opens the correct door for each visitor
- Handles security (SSL certificates) automatically
- Lets you use your own domain name instead of fake addresses

**Why use it with Trae-Proxy?**
- Real SSL certificates (trusted by browsers/IDEs)
- No need to install certificates manually on your computer
- Uses your own domain name (e.g., `openai-proxy.yourdomain.com`)
- Simple setup through a web interface

---

## How It Works (The Big Picture)

```
Your Computer (IDE)
       ↓
   [Asks for: openai-proxy.yourdomain.com]
       ↓
Nginx Proxy Manager (Port 443 - The Doorman)
       ↓
   [Forwards to: Trae-Proxy on Port 8443]
       ↓
Trae-Proxy (The Router)
       ↓
   [Sends to: DeepSeek, Kimi, Qwen, etc.]
```

**Key Points:**
1. NPM handles the security (HTTPS/SSL)
2. NPM listens on port 443 (the standard HTTPS port)
3. Trae-Proxy runs on port 8443 (internal only, not exposed to internet)
4. Your IDE only talks to NPM - it doesn't know about Trae-Proxy

---

## Quick Start Guide

### Step 1: Start Nginx Proxy Manager

```bash
cd /Users/wharsojo/dev/Trae-Proxy/nginx
docker-compose up -d
```

This starts Nginx Proxy Manager with:
- **Port 80**: For HTTP (Let's Encrypt uses this to verify your domain)
- **Port 81**: For the web management interface
- **Port 443**: For HTTPS (this is where your IDE connects)

### Step 2: Access the Web Interface

1. Open your browser
2. Go to: `http://your-server-ip:81`
3. **Default login** (first time only):
   - Email: `admin@example.com`
   - Password: `changeme`
4. **Change the password** when prompted

### Step 3: Add a Proxy Host for Trae-Proxy

1. Click **"Proxy Hosts"** in the left menu
2. Click **"Add Proxy Host"** button

Fill in the form:

| Field | What to Enter | Why? |
|-------|---------------|------|
| **Domain Names** | `openai-proxy.yourdomain.com` | This is the address your IDE will use |
| **Scheme** | `https` | For secure connections |
| **Forward Hostname/IP** | `trae-proxy` | The Docker container name for Trae-Proxy |
| **Forward Port** | `8443` | The internal port Trae-Proxy listens on |
| **Cache Assets** | ❌ unchecked | Don't cache API responses |
| **Block Common Exploits** | ✅ checked | Security best practice |

### Step 4: Set Up SSL Certificate (The Magic Part!)

1. Click on the **SSL** tab
2. Select **"Request a new SSL Certificate"**
3. Select **"Let's Encrypt"**
4. Check these options:
   - ✅ **Force SSL** - Redirects HTTP to HTTPS
   - ✅ **HTTP/2 Support** - Faster connections
   - ✅ **HSTS Enabled** - Extra security
5. Click **Save**

NPM will:
- Contact Let's Encrypt
- Verify you own the domain
- Get a **real, trusted SSL certificate**
- Set everything up automatically

### Step 5: Make Sure Trae-Proxy is Running

In another terminal:

```bash
cd /Users/wharsojo/dev/Trae-Proxy
docker-compose up -d
```

### Step 6: Test It

Open your terminal and test:

```bash
curl https://openai-proxy.yourdomain.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

If you see a list of models, it's working!

---

## Configure Your IDE

Now you can use your new proxy in your IDE:

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI (or Custom) |
| **Base URL** | `https://openai-proxy.yourdomain.com` |
| **Model ID** | Whatever you configured (e.g., `deepseek-reasoner`) |
| **API Key** | Your backend API key (e.g., DeepSeek key) |

**That's it!** No certificate installation, no hosts file editing.

---

## Domain Requirements

You need a domain name for this to work. Here are your options:

### Option 1: Buy a Domain (Recommended for long-term)

- **Namecheap**: https://www.namecheap.com
- **Cloudflare Registrar**: https://www.cloudflare.com/products/registrar/
- **GoDaddy**: https://www.godaddy.com

Then create an **A record** pointing to your server IP:
```
Type: A
Name: openai-proxy
Value: your-server-ip
```

### Option 2: Free Dynamic DNS (Good for testing/home servers)

- **Dynu**: https://www.dynu.com/ (Free, no credit card required)
- **No-IP**: https://www.noip.com/
- **DuckDNS**: https://www.duckdns.org/

These services give you a free subdomain that points to your changing IP.

---

## Common Problems & Solutions

### Problem: "502 Bad Gateway"

**What it means:** Nginx can't reach Trae-Proxy

**Solutions:**

1. Check if Trae-Proxy is running:
   ```bash
   docker ps | grep trae-proxy
   ```

2. Check if they're on the same Docker network:
   ```bash
   docker network inspect nginx_bridges
   ```

3. Make sure Trae-Proxy is on the `nginx_bridges` network:
   - Edit Trae-Proxy's `docker-compose.yml`
   - Add the network:
     ```yaml
     networks:
       bridges:
         external: true
         name: nginx_bridges
     ```

### Problem: "SSL Certificate Error"

**What it means:** Let's Encrypt can't verify your domain

**Solutions:**

1. **Check DNS**: Make sure your domain points to your server
   ```bash
   nslookup openai-proxy.yourdomain.com
   ```

2. **Wait**: DNS changes can take 5-30 minutes to propagate

3. **Open Port 80**: Let's Encrypt needs port 80 to verify your domain
   ```bash
   # Test if port 80 is open
   curl http://your-server-ip
   ```

4. **Check NPM logs**:
   ```bash
   docker logs nginx
   ```

### Problem: "Connection Refused"

**What it means:** Trae-Proxy isn't listening on port 8443

**Solutions:**

1. Check Trae-Proxy logs:
   ```bash
   docker logs trae-proxy
   ```

2. Verify Trae-Proxy configuration:
   ```bash
   docker exec -it trae-proxy cat /app/config.yaml
   ```

---

## Ports Reference

| Port | Used By | Accessible From | Purpose |
|------|---------|-----------------|---------|
| **80** | NPM | Internet | HTTP & Let's Encrypt verification |
| **81** | NPM | Your network only | Web management interface |
| **443** | NPM | Internet | HTTPS (your IDE connects here) |
| **8443** | Trae-Proxy | Local only | Internal proxy (not exposed) |

---

## Docker Networking (Important!)

For NPM to talk to Trae-Proxy, they need to be on the same Docker network.

**NPM creates a network called:** `nginx_bridges`

**Trae-Proxy needs to join this network:**

Update Trae-Proxy's `docker-compose.yml`:

```yaml
services:
  trae-proxy:
    # ... other config ...
    networks:
      - bridges

networks:
  bridges:
    external: true
    name: nginx_bridges
```

Then restart Trae-Proxy:

```bash
cd /Users/wharsojo/dev/Trae-Proxy
docker-compose down
docker-compose up -d
```

**Verify they can communicate:**

```bash
# From inside the Nginx container
docker exec -it nginx ping trae-proxy

# Should see something like:
# PING trae-proxy (172.18.0.3) 56(84) bytes of data.
# 64 bytes from trae-proxy (172.18.0.3): icmp_seq=1 ttl=64 time=0.123 ms
```

---

## File Locations

```
/Users/wharsojo/dev/Trae-Proxy/nginx/
├── docker-compose.yml          # NPM configuration
├── conf/                       # Custom configs (not needed for Trae-Proxy)
├── storage/
│   └── nginx/
│       ├── data/               # NPM database & settings
│       └── letsencrypt/        # SSL certificates (managed automatically)
└── README.md                   # This file
```

---

## Security Checklist

- [ ] Changed default admin password
- [ ] Using HTTPS (port 443) only
- [ ] SSL certificate is valid
- [ ] Port 81 (admin panel) not exposed to internet
- [ ] Trae-Proxy not directly accessible from internet
- [ ] Firewall allows ports 80, 443
- [ ] Regular backups of NPM data

---

## Advanced: Multiple Proxy Hosts

You can add multiple subdomains for different services:

| Subdomain | Forwards To | Purpose |
|-----------|-------------|---------|
| `openai-proxy.yourdomain.com` | Trae-Proxy | AI API proxy |
| `trae.yourdomain.com` | Trae-Proxy web UI | Trae-Proxy management |
| `other.yourdomain.com` | Other service | Whatever you need |

Each one gets its own SSL certificate automatically!

---

## Getting Help

If you're stuck:

1. Check the logs:
   ```bash
   docker logs nginx
   docker logs trae-proxy
   ```

2. Read the main Trae-Proxy integration guide:
   [INTEGRATION_WITH_NGINX_PROXY_MANAGER.md](../INTEGRATION_WITH_NGINX_PROXY_MANAGER.md)

3. Nginx Proxy Manager documentation:
   https://nginxproxymanager.com/

---

## Summary: What You Need to Do

1. ✅ Start NPM: `docker-compose up -d` (in this folder)
2. ✅ Start Trae-Proxy: `docker-compose up -d` (in parent folder)
3. ✅ Add proxy host in NPM web UI (port 81)
4. ✅ Configure your IDE with your new domain
5. ✅ Done! Use your custom AI models

---

**Last Updated:** 2026-01-06
