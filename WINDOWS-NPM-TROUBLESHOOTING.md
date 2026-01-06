# Windows npm Installation Troubleshooting

If you encounter the error "Exit handler never called!" or other npm installation issues during setup, try these solutions:

## Quick Fix (Most Common)

Run these commands in order:

```cmd
cd frontend
npm cache clean --force
del package-lock.json
npm install
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

- **Corrupted npm cache**: Solution 1
- **Permission issues**: Solution 2
- **Antivirus interference**: Solution 3
- **Outdated npm**: Solution 4
- **Corrupted Node.js installation**: Solution 5
- **Firewall blocking npm registry**: Check firewall settings
- **Corporate proxy**: Configure npm proxy settings

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

