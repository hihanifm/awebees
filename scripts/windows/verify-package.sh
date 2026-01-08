#!/bin/bash

# Verify Windows package structure
# Usage: verify-package.sh <package_dir> <variant>
# Variant: "with-python" or "requires-python"

set -e

PACKAGE_DIR=$1
VARIANT=$2

if [ -z "$PACKAGE_DIR" ] || [ -z "$VARIANT" ]; then
    echo "Usage: verify-package.sh <package_dir> <variant>"
    exit 1
fi

if [ "$VARIANT" != "with-python" ] && [ "$VARIANT" != "requires-python" ]; then
    echo "Error: Variant must be 'with-python' or 'requires-python'"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

echo "Verifying package: $VARIANT"
echo "Package directory: $PACKAGE_DIR"
echo ""

# Check if package directory exists
if [ ! -d "$PACKAGE_DIR" ]; then
    echo -e "${RED}✗ ERROR: Package directory not found: $PACKAGE_DIR${NC}"
    exit 1
fi

# Verify frontend structure
echo "Checking frontend structure..."
if [ ! -d "$PACKAGE_DIR/frontend" ]; then
    echo -e "${RED}✗ ERROR: frontend/ directory not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    if [ ! -d "$PACKAGE_DIR/frontend/out" ]; then
        echo -e "${RED}✗ ERROR: frontend/out/ directory not found${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ frontend/out/ directory exists${NC}"
        
        if [ ! -f "$PACKAGE_DIR/frontend/out/index.html" ]; then
            echo -e "${RED}✗ ERROR: frontend/out/index.html not found${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}✓ frontend/out/index.html exists${NC}"
        fi
        
        if [ ! -d "$PACKAGE_DIR/frontend/out/_next" ]; then
            echo -e "${YELLOW}⚠ WARNING: frontend/out/_next/ directory not found (static assets may be missing)${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}✓ frontend/out/_next/ directory exists${NC}"
        fi
    fi
fi

# Verify backend structure
echo ""
echo "Checking backend structure..."
if [ ! -d "$PACKAGE_DIR/backend" ]; then
    echo -e "${RED}✗ ERROR: backend/ directory not found${NC}"
    ERRORS=$((ERRORS + 1))
else
    if [ ! -d "$PACKAGE_DIR/backend/app" ]; then
        echo -e "${RED}✗ ERROR: backend/app/ directory not found${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ backend/app/ directory exists${NC}"
        
        if [ ! -f "$PACKAGE_DIR/backend/app/main.py" ]; then
            echo -e "${RED}✗ ERROR: backend/app/main.py not found${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}✓ backend/app/main.py exists${NC}"
        fi
        
        # Check for duplicate files at wrong locations
        if [ -f "$PACKAGE_DIR/backend/main.py" ]; then
            echo -e "${RED}✗ ERROR: Duplicate file found: backend/main.py (should be in backend/app/)${NC}"
            ERRORS=$((ERRORS + 1))
        fi
        
        if [ -d "$PACKAGE_DIR/backend/insights" ] && [ "$PACKAGE_DIR/backend/insights" != "$PACKAGE_DIR/backend/app/insights" ]; then
            echo -e "${RED}✗ ERROR: Duplicate directory found: backend/insights/ (should be in backend/app/)${NC}"
            ERRORS=$((ERRORS + 1))
        fi
        
        if [ -d "$PACKAGE_DIR/backend/core" ] && [ "$PACKAGE_DIR/backend/core" != "$PACKAGE_DIR/backend/app/core" ]; then
            echo -e "${RED}✗ ERROR: Duplicate directory found: backend/core/ (should be in backend/app/)${NC}"
            ERRORS=$((ERRORS + 1))
        fi
        
        if [ -d "$PACKAGE_DIR/backend/api" ] && [ "$PACKAGE_DIR/backend/api" != "$PACKAGE_DIR/backend/app/api" ]; then
            echo -e "${RED}✗ ERROR: Duplicate directory found: backend/api/ (should be in backend/app/)${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    fi
    
    if [ ! -f "$PACKAGE_DIR/backend/requirements.txt" ]; then
        echo -e "${RED}✗ ERROR: backend/requirements.txt not found${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ backend/requirements.txt exists${NC}"
    fi
fi

# Verify VERSION file
echo ""
echo "Checking VERSION file..."
if [ ! -f "$PACKAGE_DIR/VERSION" ]; then
    echo -e "${RED}✗ ERROR: VERSION file not found in package root${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ VERSION file exists${NC}"
    # Read and display version
    VERSION_CONTENT=$(cat "$PACKAGE_DIR/VERSION" | tr -d '[:space:]')
    if [ -z "$VERSION_CONTENT" ]; then
        echo -e "${YELLOW}⚠ WARNING: VERSION file is empty${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}  Version: $VERSION_CONTENT${NC}"
    fi
fi

# Verify launcher scripts
echo ""
echo "Checking launcher scripts..."
REQUIRED_SCRIPTS=("lens-start.bat" "lens-stop.bat" "lens-status.bat" "lens-logs.bat")
for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ ! -f "$PACKAGE_DIR/$script" ]; then
        echo -e "${RED}✗ ERROR: $script not found${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ $script exists${NC}"
    fi
done

# Verify Python (only for with-python variant)
if [ "$VARIANT" = "with-python" ]; then
    echo ""
    echo "Checking embedded Python..."
    if [ ! -d "$PACKAGE_DIR/python" ]; then
        echo -e "${RED}✗ ERROR: python/ directory not found (required for with-python variant)${NC}"
        ERRORS=$((ERRORS + 1))
    else
        if [ ! -f "$PACKAGE_DIR/python/python.exe" ]; then
            echo -e "${RED}✗ ERROR: python/python.exe not found${NC}"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${GREEN}✓ python/python.exe exists${NC}"
        fi
    fi
fi

# Summary
echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Package verification PASSED${NC}"
    echo "  No errors or warnings found"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Package verification PASSED with warnings${NC}"
    echo "  Errors: $ERRORS"
    echo "  Warnings: $WARNINGS"
    exit 0
else
    echo -e "${RED}✗ Package verification FAILED${NC}"
    echo "  Errors: $ERRORS"
    echo "  Warnings: $WARNINGS"
    exit 1
fi

