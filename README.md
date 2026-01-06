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

### Option 1: With Nginx-Proxy-Manager (Recommended)

**Advantages:**
- Real SSL certificates from Let's Encrypt
- No client-side certificate installation
- Uses your own domain (e.g., `openai-proxy.yourdomain.com`)
- Simpler client setup

**Prerequisites:**
- A domain name
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

> **💡 Don't have a domain?** Use a free Dynamic DNS service like [Dynu](https://www.dynu.com/) to get a free domain name that points to your home/office server.

Then configure Nginx-Proxy-Manager to proxy `openai-proxy.yourdomain.com` to `trae-proxy:8443`.

**Detailed Guide:** See [INTEGRATION_WITH_NGINX_PROXY_MANAGER.md](INTEGRATION_WITH_NGINX_PROXY_MANAGER.md) for step-by-step instructions.

---

### Option 2: Standalone (Self-Signed SSL)

**Use this when:**
- You don't have a domain name
- You can't use Nginx-Proxy-Manager
- You need to impersonate `api.openai.com`

**Disadvantages:**
- Requires self-signed certificate installation on each client
- Requires modifying `/etc/hosts` file on each client
- More complex setup

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

```yaml
# Trae-Proxy configuration file

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
  port: 8443  # Use 8443 with NPM, or 443 for standalone
  debug: true
```

## 🖥️ IDE Configuration

### With Nginx-Proxy-Manager

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI (or Custom) |
| **Base URL** | `https://openai-proxy.yourdomain.com` |
| **Model ID** | Your configured model (e.g., `deepseek-reasoner`) |
| **API Key** | Your backend API key |

### Standalone (Self-Signed)

| Setting | Value |
|---------|-------|
| **Provider** | OpenAI |
| **Base URL** | `https://api.openai.com` (uses hosts file) |
| **Model ID** | Your configured model |
| **API Key** | Your backend API key |

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