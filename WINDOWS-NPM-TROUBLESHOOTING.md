# Windows npm Installation Troubleshooting

If you encounter the error "Exit handler never called!" or SSL certificate errors like "UNABLE_TO_GET_ISSUER_CERT_LOCALLY" during setup, try these solutions:

## Quick Fix (Most Common)

Run these commands in order:

```cmd
cd frontend
npm cache clean --force
del package-lock.json
npm install
```

## SSL Certificate Error Fix (UNABLE_TO_GET_ISSUER_CERT_LOCALLY)

If you see `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` errors, this is an SSL certificate verification issue. Try these solutions in order:

### Solution A: Configure npm to Handle SSL Issues (Quick Fix)

**Warning:** This disables strict SSL verification. Only use if other solutions don't work.

```cmd
npm config set strict-ssl false
npm config set registry https://registry.npmjs.org/
cd frontend
npm install
```

To re-enable strict SSL later:
```cmd
npm config set strict-ssl true
```

### Solution B: Configure Corporate Proxy (If Behind a Proxy)

If you're behind a corporate proxy, configure npm to use it:

```cmd
npm config set proxy http://your-proxy-server:port
npm config set https-proxy http://your-proxy-server:port
npm config set registry https://registry.npmjs.org/
cd frontend
npm install
```

### Solution C: Use Environment Variables

Set these environment variables before running npm install:

```cmd
set NODE_TLS_REJECT_UNAUTHORIZED=0
cd frontend
npm install
```

**Note:** This is less secure but may work in restricted environments.

### Solution D: Install CA Certificates (Best Long-term Solution)

1. Download the npm registry CA certificate bundle
2. Configure npm to use it:

```cmd
npm config set cafile "C:\path\to\ca-bundle.crt"
cd frontend
npm install
```

Or set the environment variable:
```cmd
set NODE_EXTRA_CA_CERTS=C:\path\to\ca-bundle.crt
cd frontend
npm install
```

### Solution E: Use Alternative Registry (Temporary Workaround)

Try using a different registry mirror:

```cmd
npm config set registry https://registry.npmmirror.com
cd frontend
npm install
```

Then reset to official registry:
```cmd
npm config set registry https://registry.npmjs.org/
```

## Solution 1: Clear npm Cache

```cmd
npm cache clean --force
npm cache verify
```

Then try the setup again:
```cmd
scripts\win-setup.bat
```

## Solution 2: Run as Administrator

1. Right-click on Command Prompt
2. Select "Run as Administrator"
3. Navigate to your project directory
4. Run the setup script again

## Solution 3: Temporarily Disable Antivirus

Some antivirus software interferes with npm:

1. Temporarily disable your antivirus
2. Run the setup script
3. Re-enable your antivirus after installation

## Solution 4: Update npm

```cmd
npm install -g npm@latest
```

Then try the setup again.

## Solution 5: Reinstall Node.js

1. Uninstall Node.js from Control Panel
2. Download the latest LTS version from https://nodejs.org/
3. Install with default options
4. **Important:** Check "Add to PATH" during installation
5. Restart Command Prompt
6. Verify installation:
   ```cmd
   node --version
   npm --version
   ```
7. Run the setup script again

## Solution 6: Check npm Logs

If the error persists, check the detailed log file mentioned in the error message:

```cmd
type C:\Users\YourUsername\AppData\Local\npm-cache\_logs\[timestamp]-debug-0.log
```

Look for specific error details that might indicate the root cause.

## Solution 7: Manual Installation

If all else fails, install dependencies manually:

```cmd
cd frontend
npm cache clean --force
del package-lock.json
del node_modules /s /q
npm install --verbose
```

The `--verbose` flag will show detailed output to help identify where the failure occurs.

## Common Causes

- **SSL certificate issues**: See "SSL Certificate Error Fix" section above
- **Corporate proxy/firewall**: Solution B in SSL section
- **Corrupted npm cache**: Solution 1
- **Permission issues**: Solution 2
- **Antivirus interference**: Solution 3
- **Outdated npm**: Solution 4
- **Corrupted Node.js installation**: Solution 5
- **Firewall blocking npm registry**: Check firewall settings

## Still Having Issues?

1. Check Node.js and npm versions:
   ```cmd
   node --version
   npm --version
   ```
   Recommended: Node.js 18.x or later, npm 9.x or later

2. Try using a different package manager:
   ```cmd
   npm install -g yarn
   cd frontend
   yarn install
   ```

3. Check for disk space and permissions on `node_modules` directory

4. Review the complete error log for specific error messages

