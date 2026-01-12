#!/bin/bash

# Security Check Script
# Scans Python and Node.js dependencies for known vulnerabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any vulnerabilities are found
VULN_FOUND=0

echo "🔒 Running security vulnerability scans..."
echo ""

# Check Python dependencies
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Python Dependencies Scan"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "backend/requirements.txt" ]; then
    echo -e "${YELLOW}⚠️  backend/requirements.txt not found. Skipping Python scan.${NC}"
else
    # Check if pip-audit is installed
    if ! command -v pip-audit &> /dev/null; then
        echo -e "${YELLOW}⚠️  pip-audit not found. Installing...${NC}"
        pip install --upgrade pip
        pip install pip-audit>=2.6.0
    fi

    cd backend
    if pip-audit --requirement requirements.txt; then
        echo -e "${GREEN}✅ No Python vulnerabilities found${NC}"
    else
        echo -e "${RED}❌ Python vulnerabilities detected!${NC}"
        VULN_FOUND=1
    fi
    cd ..
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Node.js Dependencies Scan"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "frontend/package.json" ]; then
    echo -e "${YELLOW}⚠️  frontend/package.json not found. Skipping Node.js scan.${NC}"
else
    cd frontend
    
    # Check if node_modules exists, if not, install dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
        npm install
    fi

    # Run npm audit
    if npm audit --audit-level=moderate; then
        echo -e "${GREEN}✅ No Node.js vulnerabilities found${NC}"
    else
        echo -e "${RED}❌ Node.js vulnerabilities detected!${NC}"
        VULN_FOUND=1
    fi
    cd ..
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Final summary
if [ $VULN_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ Security scan completed: No vulnerabilities found${NC}"
    exit 0
else
    echo -e "${RED}❌ Security scan completed: Vulnerabilities detected${NC}"
    echo ""
    echo "To fix vulnerabilities:"
    echo "  Python: Review pip-audit output and update packages in backend/requirements.txt"
    echo "  Node.js: Run 'npm audit fix' in frontend/ directory (or update packages manually)"
    exit 1
fi
