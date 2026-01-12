# Security Scanning Guide

This document describes the security scanning tools and processes used in this repository to ensure no vulnerable packages are introduced.

## Overview

The repository uses multiple layers of security scanning:

1. **Automated CI/CD scanning** - Runs on every pull request and push
2. **Dependabot** - Automated dependency updates and security alerts
3. **Local scanning scripts** - For developers to check before committing

## Automated Scanning

### GitHub Actions

A security workflow (`.github/workflows/security-scan.yml`) automatically scans dependencies on:

- Every pull request to `master` or `main`
- Every push to `master` or `main`
- Weekly schedule (Mondays at 9 AM UTC)
- Manual trigger via workflow_dispatch

The workflow checks:
- **Python dependencies**: Uses `pip-audit` to scan `backend/requirements.txt`
- **Node.js dependencies**: Uses `npm audit` to scan `frontend/package-lock.json`

If vulnerabilities are detected, the workflow fails and uploads detailed audit reports as artifacts.

### Dependabot

GitHub Dependabot is configured (`.github/dependabot.yml`) to:

- Monitor Python packages in `backend/requirements.txt`
- Monitor Node.js packages in `frontend/package.json`
- Create pull requests for security updates weekly
- Group updates to reduce PR noise

Dependabot will automatically:
- Detect vulnerable dependencies
- Create PRs with security updates
- Label PRs with `security` and `dependencies` tags

## Local Scanning

### Unix/Mac (Linux/macOS)

Run the security check script:

```bash
./scripts/security-check.sh
```

The script will:
- Check if `pip-audit` is installed (installs if missing)
- Scan Python dependencies in `backend/requirements.txt`
- Scan Node.js dependencies in `frontend/package.json`
- Display color-coded results (green/yellow/red)
- Exit with error code if vulnerabilities are found

### Windows

Run the security check script:

```cmd
scripts\win-security-check.bat
```

The script performs the same checks as the Unix version, adapted for Windows batch syntax.

## Tools Used

### Python: pip-audit

`pip-audit` is a modern vulnerability scanner that:
- Checks packages against the PyPI Advisory Database
- Provides detailed vulnerability information
- Supports JSON and text output formats
- Actively maintained by the Python Packaging Authority

**Installation:**
```bash
pip install pip-audit>=2.6.0
```

Or install from `backend/requirements-dev.txt`:
```bash
pip install -r backend/requirements-dev.txt
```

**Usage:**
```bash
cd backend
pip-audit --requirement requirements.txt
```

### Node.js: npm audit

`npm audit` is built into npm and:
- Checks packages against the npm Advisory Database
- Provides fix recommendations
- Can automatically fix vulnerabilities with `npm audit fix`

**Usage:**
```bash
cd frontend
npm audit
npm audit --audit-level=moderate  # Only show moderate and above
npm audit fix  # Automatically fix vulnerabilities (use with caution)
```

## Interpreting Results

### pip-audit Output

```
Found 2 known vulnerabilities in 1 package
Package: httpx==0.25.2
  Vulnerability ID: PYSEC-2024-XXX
  Severity: HIGH
  Description: [Vulnerability description]
  Fix: Upgrade to httpx>=0.26.0
```

**Action:** Update the vulnerable package in `backend/requirements.txt` to the recommended version.

### npm audit Output

```
# npm audit report

package-name  <1.2.3
Severity: moderate
Description: [Vulnerability description]
Fix: npm audit fix --force
```

**Action:** 
- For patch/minor updates: `npm audit fix` (safe)
- For major updates: Review and update `package.json` manually
- Always test after applying fixes

## Fixing Vulnerabilities

### Python Dependencies

1. Review the vulnerability details from `pip-audit`
2. Update the package version in `backend/requirements.txt`
3. Test the application to ensure compatibility
4. Commit the change with a clear message:
   ```bash
   git commit -m "security: update httpx to 0.26.0 to fix vulnerability"
   ```

### Node.js Dependencies

**Automatic fix (recommended for patch/minor updates):**
```bash
cd frontend
npm audit fix
```

**Manual fix (for major updates or when audit fix fails):**
1. Review the vulnerability in `npm audit` output
2. Update the package version in `frontend/package.json`
3. Run `npm install` to update `package-lock.json`
4. Test the application
5. Commit the changes

## Best Practices

1. **Run local scans before committing**: Use `./scripts/security-check.sh` or `scripts\win-security-check.bat`

2. **Review Dependabot PRs promptly**: Security updates should be merged quickly after testing

3. **Test after updates**: Always test your application after updating dependencies

4. **Keep dependencies up to date**: Regular updates reduce the attack surface

5. **Review audit reports**: Don't blindly apply fixes - understand what changed

6. **Use exact versions for production**: Pin versions in `requirements.txt` and `package-lock.json` for reproducible builds

## Continuous Monitoring

- **Weekly automated scans**: GitHub Actions runs weekly scans
- **Dependabot alerts**: GitHub will notify you of new vulnerabilities
- **Security tab**: Check the GitHub Security tab for vulnerability alerts

## Reporting Security Issues

If you discover a security vulnerability that's not covered by automated scanning:

1. **Do not** create a public issue
2. Email the maintainers or use GitHub's private security reporting
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Additional Resources

- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [npm audit Documentation](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
