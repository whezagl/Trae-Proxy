<div align="center">
  <img src="asset/logo.png" alt="Trae Proxy" width="64" height="64">
  <h1>Trae Proxy</h1>
</div>

[English](README.md)

A high-performance, low-latency API proxy middleware designed for large language model applications, capable of seamlessly intercepting and redirecting OpenAI API requests to any custom backend service. Supports multi-backend load balancing, intelligent routing, dynamic model mapping, and streaming response handling.

> **📖 Recommended**: For the easiest deployment with real SSL certificates, use Trae-Proxy with **Nginx-Proxy-Manager**. See [Integration Guide](INTEGRATION_WITH_NGINX_PROXY_MANAGER.md).

## 📢 Introduction

1. Trae IDE currently supports custom model providers, but only those fixed in the list, and does not support custom base_url, making it impossible to use your own API service.
2. There are many related issues on Github, but the official response is minimal, such as: [Add custom model provider base_url capability](https://github.com/Trae-AI/Trae/issues/1206), [Custom AI API Endpoint](https://github.com/Trae-AI/Trae/issues/963).
3. Based on this situation, Trae-Proxy was developed to proxy OpenAI API requests to custom backends, while supporting custom model ID mapping and dynamic backend switching.
4. We hope the official team will soon implement custom base_url capability, making Trae a truly customizable IDE.

## 📸 Screenshots

<div align="center">

<table>
<tr>
<td align="center">
<h3>Custom-Model</h3>
<img src="./asset/Custom-Model.png" alt="Custom-Model" width="330">
<br>
<em>Support for custom OpenAI-compatible APIs</em>
</td>
<td align="center">
<h3>IDE-Builder</h3>
<img src="./asset/IDE-Chat.png" alt="IDE-Chat" width="290">
<br>
<em>Integration with Qwen3-Coder-Plus model</em>
</td>
</tr>
</table>
</div>

## ✨ Key Features

- **Intelligent Proxy**: Intercept OpenAI API requests and forward them to custom backends
- **Multi-Backend Support**: Configure multiple API backends with dynamic switching
- **Model Mapping**: Custom model ID mapping for seamless model replacement
- **Streaming Response**: Support for both streaming and non-streaming response modes
- **Docker Deployment**: One-click containerized deployment for production environments
- **NPM Integration**: Works seamlessly with Nginx-Proxy-Manager for real SSL certificates

## 🚀 Deployment Options

### Understanding the Two Approaches

Trae IDE has a limitation: when you select "OpenAI" as the provider, it **hardcodes** the base URL to `api.openai.com`. This gives us two options:

| Approach | How It Works | Pros | Cons |
|----------|--------------|------|------|
| **A. Custom Domain** | IDE connects to `openai-proxy.yourdomain.com` | Real SSL, no client setup | Requires IDE to support custom base URL* |
| **B. Domain Impersonation** | Trick IDE into thinking your server IS `api.openai.com` | Works with any OpenAI-compatible IDE | Requires client certificate installation |

**\** *Check if your IDE supports "Custom" provider with editable base URL before choosing.*

---

### Option A: With Nginx-Proxy-Manager (Recommended)

**Best for:** IDEs that support custom base URL (editable "Base URL" field)

**Advantages:**
- Real SSL certificates from Let's Encrypt
- No client-side certificate installation
- Uses your own domain (e.g., `openai-proxy.yourdomain.com`)
- Simpler client setup

**Prerequisites:**
- A domain name (or free DDNS like [Dynu](https://www.dynu.com/))
- Nginx-Proxy-Manager running on port 443

**Quick Start:**

```bash
# Clone the repository
git clone https://github.com/whezagl/Trae-Proxy.git
cd Trae-Proxy

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

Then configure Nginx-Proxy-Manager to proxy `openai-proxy.yourdomain.com` → `trae-proxy:8443`.

**Detailed Guide:** See [INTEGRATION_WITH_NGINX_PROXY_MANAGER.md](INTEGRATION_WITH_NGINX_PROXY_MANAGER.md) for step-by-step instructions.

---

### Option B: Domain Impersonation (api.openai.com)

**Best for:** IDEs that DON'T support custom base URL (hardcoded to `api.openai.com`)

**How It Works:**
```
Trae IDE thinks it's talking to api.openai.com
           ↓
But DNS/hosts file points api.openai.com to YOUR server
           ↓
Nginx-Proxy-Manager (port 443) receives the request
           ↓
Forwards to Trae-Proxy (port 8443)
           ↓
Trae-Proxy sends request to REAL backend (DeepSeek, Kimi, etc.)
```

**⚠️ Important Limitations:**
- ❌ **Cannot use Let's Encrypt** - You don't own `api.openai.com`, so can't get real SSL
- ✅ **Must use self-signed certificates** - Requires installation on each client
- ✅ **Must modify hosts file** - Point `api.openai.com` to your server IP

**Setup:** This combines Nginx-Proxy-Manager with domain impersonation. See instructions below.

---

### Option C: Standalone (Self-Signed SSL, Without NPM)

**Use this when:**
- You don't want to use Nginx-Proxy-Manager
- You need to impersonate `api.openai.com`
- You're comfortable with manual certificate management

**Disadvantages:**
- Requires self-signed certificate installation on each client
- Requires modifying `/etc/hosts` file on each client
- More complex setup
- Manual certificate renewal

#### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Generate self-signed certificates
python generate_certs.py

# Start the proxy server
python trae_proxy.py
```

#### Client Configuration

You'll need to:

1. **Install the CA certificate** on each client machine
2. **Modify the hosts file** to point `api.openai.com` to your server IP
3. **Configure your IDE** to use OpenAI as the provider

**Detailed instructions:** See the [Standalone Setup](#standalone-setup-with-self-signed-ssl) section below.

## 📝 Configuration File Structure

Trae-Proxy uses a YAML format configuration file `config.yaml`:

> **⚠️ Important:** The port and domain settings depend on which deployment option you choose. See the explanation below.

### Which Port Should I Use?

| Deployment Mode | Port Setting | Domain | Why? |
|-----------------|--------------|--------|------|
| **Option A: Custom Domain** | `port: 8443` | Your domain | NPM handles port 443, Trae-Proxy uses internal port 8443 |
| **Option B: Domain Impersonation** | `port: 8443` | `api.openai.com` | Same setup, different domain in NPM |
| **Option C: Standalone** | `port: 443` | `api.openai.com` | Trae-Proxy directly handles port 443 |

**Simple Explanation:**
- Think of NPM as a "front desk" that greets visitors at the main door (port 443)
- Trae-Proxy works in the back room on port 8443
- NPM passes requests to Trae-Proxy - your IDE never talks to port 8443 directly
- The "domain" is just the name on the door - can be your domain or `api.openai.com`

### Example Configuration (With Nginx-Proxy-Manager)

```yaml
# Trae-Proxy configuration file

# Proxy domain configuration
# IMPORTANT: Only needed for standalone mode with self-signed SSL
# When using Nginx-Proxy-Manager, this field is ignored
domain: api.openai.com

# Backend API configuration list
apis:
  - name: "deepseek-r1"
    endpoint: "https://api.deepseek.com"
    custom_model_id: "deepseek-reasoner"
    target_model_id: "deepseek-reasoner"
    stream_mode: null
    active: true
  - name: "kimi-k2"
    endpoint: "https://api.moonshot.cn"
    custom_model_id: "kimi-k2-0711-preview"
    target_model_id: "kimi-k2-0711-preview"
    stream_mode: null
    active: true
  - name: "qwen3-coder-plus"
    endpoint: "https://dashscope.aliyuncs.com/compatible-mode"
    custom_model_id: "qwen3-coder-plus"
    target_model_id: "qwen3-coder-plus"
    stream_mode: null
    active: true

# Proxy server configuration
server:
  # Use port 8443 when using Nginx-Proxy-Manager (recommended)
  # Use port 443 ONLY for standalone mode (without NPM, with self-signed SSL)
  port: 8443
  debug: true
```

## 🖥️ IDE Configuration

### Option A: Custom Domain (Recommended)

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI (or Custom if available) |
| **Base URL** | `https://openai-proxy.yourdomain.com` |
| **Model ID** | Your configured model (e.g., `deepseek-reasoner`) |
| **API Key** | Your backend API key |

### Option B: Domain Impersonation (api.openai.com)

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI |
| **Base URL** | `https://api.openai.com` (auto-filled, don't change) |
| **Model ID** | Your configured model |
| **API Key** | Your backend API key |

**Requires:**
- Self-signed certificate installed on client (see [Option B Setup](#option-b-domain-impersonation-with-npm) below)
- Hosts file modified to point `api.openai.com` to your server

### Option C: Standalone (Self-Signed)

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI |
| **Base URL** | `https://api.openai.com` (uses hosts file) |
| **Model ID** | Your configured model |
| **API Key** | Your backend API key |

---

## Option B: Domain Impersonation (With NPM)

<details>
<summary>Click to expand Domain Impersonation setup instructions</summary>

This approach makes your server pretend to be `api.openai.com`. Useful when your IDE doesn't support custom base URLs.

### Why This Works

```
Your IDE (Trae/VSCode/JetBrains)
  "I need to talk to api.openai.com"
  ↓
But your hosts file says:
  "api.openai.com = YOUR_SERVER_IP"
  ↓
Request goes to YOUR server instead!
  ↓
Nginx-Proxy-Manager receives it (port 443)
  ↓
Forwards to Trae-Proxy (port 8443)
  ↓
Trae-Proxy sends it to DeepSeek/Kimi/Qwen/etc.
```

### Step 1: Generate Self-Signed Certificate for api.openai.com

Since you don't own `api.openai.com`, you can't use Let's Encrypt. You must create a self-signed certificate.

```bash
# On your server, create certificate directory
mkdir -p nginx/certs

# Generate self-signed certificate for api.openai.com
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/api.openai.com.key \
  -out nginx/certs/api.openai.com.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=api.openai.com"

# Generate CA certificate (for client installation)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/ca.key \
  -out nginx/certs/ca.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=Trae-Proxy-CA"
```

### Step 2: Upload Certificate to Nginx-Proxy-Manager

1. Open NPM web interface: `http://your-server-ip:81`

2. Go to **SSL Certificates** tab (in the left menu)

3. Click the **Add SSL Certificate** button (top-right)

4. Fill in the form:
   - **Name**: `api.openai.com`
   - Select **Custom** certificate type
   - **Key**: Paste content of `api.openai.com.key`
   - **Certificate**: Paste content of `api.openai.com.crt`
   - Click **Save**

5. Now go to **Proxy Hosts** tab and add a new proxy host:

| Field | Value |
|-------|-------|
| **Domain Names** | `api.openai.com` |
| **Scheme** | `http` |
| **Forward Hostname/IP** | `trae-proxy` |
| **Forward Port** | `8443` |
| **Cache Assets** | ❌ unchecked |
| **Block Common Exploits** | ✅ checked |

> **⚠️ Important:** Use `http` scheme for forwarding (not `https`). Trae-Proxy runs in HTTP mode, and NPM handles the HTTPS termination. |

6. Click on the **SSL** tab:
   - Select the certificate you just uploaded (`api.openai.com`) from the dropdown
   - Enable **Force SSL**
   - Enable **HTTP/2 Support**
   - Click **Save**

### Step 3: Install CA Certificate on Each Client

**Windows:**
1. Copy `ca.crt` from server to your Windows machine
2. Double-click `ca.crt`
3. Select **Install Certificate** → **Local Machine**
4. Place in: **Trusted Root Certification Authorities**
5. Complete the wizard

**macOS:**
1. Copy `ca.crt` from server to your Mac
2. Double-click `ca.crt` (opens Keychain Access)
3. Add to **System** keychain
4. Double-click the imported certificate
5. Expand **Trust** → Set **When using this certificate** to **Always Trust**
6. Close and enter your password

**Linux (Debian/Ubuntu):**
```bash
sudo cp ca.crt /usr/local/share/ca-certificates/api.openai.com.crt
sudo update-ca-certificates
```

### Step 4: Modify Hosts File on Each Client

**Windows:**
1. Open Notepad as Administrator
2. Open: `C:\Windows\System32\drivers\etc\hosts`
3. Add this line (replace with your server IP):
   ```
   YOUR_SERVER_IP api.openai.com
   ```
4. Save and exit

**macOS/Linux:**
```bash
sudo nano /etc/hosts
# Add this line (replace with your server IP):
YOUR_SERVER_IP api.openai.com
# Save: Ctrl+O, Enter, Ctrl+X
```

### Step 5: Configure Your IDE

Now set up your IDE to use OpenAI:

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI |
| **Base URL** | `https://api.openai.com` (leave as-is) |
| **Model ID** | `deepseek-reasoner` (or your configured model) |
| **API Key** | Your DeepSeek/Kimi/Qwen API key |

### Step 6: Test It

```bash
# Should show your Trae-Proxy models
curl https://api.openai.com/v1/models
```

If successful, you'll see the models configured in Trae-Proxy!

> **💡 Alternative Method:** If the UI doesn't work, you can manually place certificate files in NPM's data directory (`/path/to/nginx/storage/nginx/ssl/`) and restart NPM.

</details>

---

## Standalone Setup (With Self-Signed SSL)

<details>
<summary>Click to expand standalone setup instructions</summary>

### 1. Get Server Self-Signed Certificate

Copy the CA certificate from the server to your local machine:

```bash
# Copy CA certificate from server
scp user@your-server-ip:/path/to/trae-proxy/ca/api.openai.com.crt .
```

### 2. Install CA Certificate

#### Windows

1. Double-click the `api.openai.com.crt` file
2. Select "Install Certificate"
3. Select "Local Machine"
4. Select "Place all certificates in the following store" → "Browse" → "Trusted Root Certification Authorities"
5. Complete the installation

#### macOS

1. Double-click the `api.openai.com.crt` file, which will open "Keychain Access"
2. Add the certificate to the "System" keychain
3. Double-click the imported certificate, expand the "Trust" section
4. Set "When using this certificate" to "Always Trust"
5. Close the window and enter your administrator password to confirm

### 3. Modify Hosts File

#### Windows

1. Edit `C:\Windows\System32\drivers\etc\hosts` as administrator
2. Add the following line (replace with your server IP):
   ```
   your-server-ip api.openai.com
   ```

#### macOS

1. Open Terminal
2. Execute `sudo vim /etc/hosts`
3. Add the following line (replace with your server IP):
   ```
   your-server-ip api.openai.com
   ```

### 4. Test Connection

```bash
curl https://api.openai.com/v1/models
```

If configured correctly, you should see the model list returned by the proxy server.

</details>

## 🔧 System Requirements

- **Server**: Python 3.9+, Docker
- **Client (NPM mode)**: None special requirements
- **Client (Standalone)**: Administrator privileges (for modifying hosts file and installing certificates)

## 📁 Project Structure

```
trae-proxy/
├── trae_proxy.py          # Main proxy server
├── trae_proxy_cli.py      # Command-line management tool
├── generate_certs.py      # Certificate generation tool (standalone mode)
├── config.yaml            # Configuration file
├── docker-compose.yml     # Docker deployment configuration
├── requirements.txt       # Python dependencies
├── ca/                    # Certificates directory (standalone mode)
├── INTEGRATION_WITH_NGINX_PROXY_MANAGER.md  # NPM integration guide
└── README.md              # This file
```

## 🔍 How It Works

```
 +------------------+    +--------------+    +------------------+
 |                  |    |              |    |                  |
 |  DeepSeek API    +--->+              +--->+  Trae IDE        |
 |  Moonshot API    +--->+              +--->+  VSCode          |
 |  Aliyun API      +--->+  Trae-Proxy  +--->+  JetBrains       |
 |  Self-hosted LLM +--->+              +--->+  OpenAI Clients  |
 |  Other API Svcs  +--->+              |    |                  |
 +------------------+    +--------------+    +------------------+
   Backend Services       Proxy Server        Client Apps
```

## 💡 Use Cases

- **API Proxy**: Forward OpenAI API requests to privately deployed model services
- **Model Replacement**: Replace official OpenAI models with custom models
- **Load Balancing**: Distribute requests among multiple backend services
- **Development Testing**: API simulation and testing in local development environments

## ⚠️ Disclaimer

1. **Trae-Proxy** is a tool for intercepting and redirecting OpenAI API requests to custom backend services, without modifying or reverse engineering official software.
2. This tool is for learning and research purposes only. Users should comply with relevant laws, regulations, and service terms.
3. Theoretically, not only TraeIDE but also other IDEs or clients that support OpenAI SDK or API can seamlessly integrate with this tool.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.