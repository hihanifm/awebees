# Forward Proxy for AI Traffic

A simple, production-ready forward proxy using Caddy that transparently forwards AI traffic (including streaming) to an internal AI server. Supports both Linux and macOS with automatic startup on reboot.

## Features

- **Transparent Forwarding**: Passes through all requests and responses without modification
- **Streaming Support**: Handles streaming AI responses in real-time
- **Auto-Start on Reboot**: Optional service installation for Linux (systemd) and macOS (launchd)
- **Easy Configuration**: Simple environment-based configuration
- **Cross-Platform**: Works on Linux and macOS (Intel and Apple Silicon)

## Quick Start

### 1. Setup

Run the setup script to download Caddy and create configuration:

```bash
cd proxy
./setup.sh
```

This will:
- Download the appropriate Caddy binary for your platform
- Create `config.env` from `config.env.example` (if it doesn't exist)
- Make all scripts executable

### 2. Configure

Edit `config.env` to set your target AI server:

```bash
# For OpenAI (default)
TARGET_HOST=api.openai.com
TARGET_PORT=443
TARGET_PROTOCOL=https

# For your internal AI server
# TARGET_HOST=192.168.1.100
# TARGET_PORT=8000
# TARGET_PROTOCOL=http

# Proxy listen configuration
LISTEN_HOST=0.0.0.0
LISTEN_PORT=8080
```

### 3. Start the Proxy

```bash
./start.sh
```

The proxy will start and forward traffic from `localhost:8080` to your configured target server.

### 4. (Optional) Enable Auto-Start on Reboot

To make the proxy start automatically on system reboot:

```bash
./install-service.sh
```

**Linux**: Requires sudo privileges to install systemd service  
**macOS**: No sudo needed, installs as user launchd agent

## Usage

### Basic Commands

```bash
./start.sh      # Start the proxy
./stop.sh       # Stop the proxy
./restart.sh    # Restart the proxy
./check.sh      # Check proxy status
./show-ip.sh    # Show proxy IP address and connection info
```

### Finding Your Proxy Address

To see your proxy connection information (IP addresses and examples):

```bash
./show-ip.sh
```

This will show:
- **Localhost address** (for connections from the same machine): `http://localhost:8080`
- **Network IP address** (for connections from other devices on your network): `http://YOUR_IP:8080`
- Example configurations for different clients

### Using the Proxy

Once the proxy is running, configure your AI client to use it:

**Important: The proxy forwards paths as-is. Your API service/client must include `/v1` in the path.**
- Base URL: `http://localhost:8080` or `http://192.168.1.214:8080`
- Endpoint: `/v1/chat/completions` (include `/v1` - the proxy does NOT add it)

The proxy is completely transparent - it forwards whatever path you send. Your API service is responsible for constructing the correct path including `/v1`.

**For connections from the same machine:**
- Base URL: `http://localhost:8080` or `http://127.0.0.1:8080`
- Full path: `/v1/chat/completions`

**For connections from other devices on your network:**
- Base URL: `http://YOUR_MACHINE_IP:8080` (run `./show-ip.sh` to find your IP)
- Full path: `/v1/chat/completions`

#### OpenAI Python Client

```python
import openai

# Base URL points to proxy - API service handles /v1 in paths
client = openai.OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:8080",  # Proxy address
    # The OpenAI client will automatically use /v1/chat/completions
)
```

#### OpenAI Node.js Client

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: 'your-api-key',
  httpAgent: new HttpsProxyAgent('http://localhost:8080'),
});
```

#### cURL

```bash
curl -x http://localhost:8080 https://api.openai.com/v1/models \
  -H "Authorization: Bearer your-api-key"
```

#### Environment Variables

```bash
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
```

### Service Management (if installed)

#### Linux (systemd)

```bash
sudo systemctl status caddy-proxy    # Check status
sudo systemctl stop caddy-proxy      # Stop
sudo systemctl start caddy-proxy      # Start
sudo systemctl restart caddy-proxy    # Restart
```

#### macOS (launchd)

```bash
launchctl list | grep caddy          # Check if loaded
launchctl unload ~/Library/LaunchAgents/com.caddy.proxy.plist  # Unload
launchctl load ~/Library/LaunchAgents/com.caddy.proxy.plist    # Load
```

### Uninstall Service

To remove auto-start on reboot:

```bash
./uninstall-service.sh
```

## Configuration

### Environment Variables (`config.env`)

| Variable | Description | Default |
|----------|-------------|---------|
| `TARGET_HOST` | Target AI server hostname or IP | `api.openai.com` |
| `TARGET_PORT` | Target AI server port | `443` |
| `TARGET_PROTOCOL` | Protocol: `http` or `https` | `https` |
| `LISTEN_HOST` | Proxy listen address | `0.0.0.0` |
| `LISTEN_PORT` | Proxy listen port | `8080` |
| `CADDY_BINARY` | Path to Caddy binary | `./caddy` |

### Logs

- **Caddy logs**: `logs/caddy.log`
- **Access logs**: `logs/access.log`
- **Service logs** (if installed):
  - Linux: `journalctl -u caddy-proxy`
  - macOS: `logs/service.log` and `logs/service.error.log`

## Platform Support

### Linux

- Ubuntu/Debian
- CentOS/RHEL
- Generic Linux distributions
- Supports both x86_64 (amd64) and ARM64 architectures

### macOS

- Intel (x86_64)
- Apple Silicon (M1/M2/M3 - ARM64)
- No sudo required for service installation (runs as user agent)

## Troubleshooting

### Getting 404 errors

If you're getting 404 errors, check that your API service/client is including `/v1` in the request path:

- ✅ **Correct**: Request path = `/v1/chat/completions`
- ❌ **Wrong**: Request path = `/chat/completions` (missing `/v1`)

**Solution**: Ensure your API service constructs paths with `/v1` prefix. The proxy forwards paths exactly as received - it does NOT add `/v1` automatically.

### Proxy won't start

1. Check if port is already in use:
   ```bash
   lsof -i :8080  # Linux/macOS
   ```

2. Check Caddy logs:
   ```bash
   tail -f logs/caddy.log
   ```

3. Verify configuration:
   ```bash
   ./check.sh
   ```

### Connection refused

1. Verify proxy is running:
   ```bash
   ./check.sh
   ```

2. Check firewall settings (Linux):
   ```bash
   sudo ufw allow 8080/tcp
   ```

3. Test connectivity:
   ```bash
   curl -v -x http://localhost:8080 http://example.com
   ```

### Service not starting on reboot

**Linux:**
```bash
sudo systemctl status caddy-proxy
sudo journalctl -u caddy-proxy -n 50
```

**macOS:**
```bash
launchctl list | grep caddy
cat logs/service.error.log
```

### Streaming not working

The proxy is configured with `flush_interval -1` to enable streaming. If streaming still doesn't work:

1. Check that your client supports HTTP proxies
2. Verify the target server supports streaming
3. Check Caddy logs for any errors

## How It Works

The proxy uses Caddy's `reverse_proxy` directive to forward all incoming requests to the configured target server. Key features:

- **No modification**: Headers and payloads are passed through unchanged
- **Streaming**: `flush_interval -1` enables real-time streaming of responses
- **HTTPS support**: Handles both HTTP and HTTPS traffic
- **Auto-restart**: Service automatically restarts on failure

## Security Notes

- The proxy listens on `0.0.0.0` by default, making it accessible from all network interfaces
- For production use, consider:
  - Binding to a specific IP address (`LISTEN_HOST`)
  - Using firewall rules to restrict access
  - Running behind a reverse proxy with authentication
  - Using TLS termination if exposing externally

## License

This is a utility project. Caddy is licensed under Apache 2.0.
