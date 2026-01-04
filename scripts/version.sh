#!/bin/bash

# Version management script for Lens
# Usage: ./scripts/version.sh [command] [version]
# Commands:
#   get     - Show current version (default)
#   set     - Set version (requires version argument, e.g., 0.1.0)
#   bump    - Bump version (major|minor|patch)
#   sync    - Sync version to package.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$PROJECT_ROOT/VERSION"
PACKAGE_JSON="$PROJECT_ROOT/frontend/package.json"

get_current_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE" | tr -d ' \n'
    else
        echo "0.0.0"
    fi
}

set_version() {
    local new_version=$1
    if [ -z "$new_version" ]; then
        echo "Error: Version argument required"
        echo "Usage: $0 set <version>"
        exit 1
    fi
    
    # Validate version format (basic semantic version check)
    if ! echo "$new_version" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$'; then
        echo "Error: Invalid version format. Expected: X.Y.Z or X.Y.Z-label"
        exit 1
    fi
    
    echo "$new_version" > "$VERSION_FILE"
    echo "Version set to: $new_version"
    
    # Sync to package.json
    sync_to_package_json "$new_version"
}

bump_version() {
    local bump_type=$1
    local current_version=$(get_current_version)
    
    # Remove any pre-release suffix for bumping
    local base_version=$(echo "$current_version" | cut -d'-' -f1)
    IFS='.' read -r -a version_parts <<< "$base_version"
    local major=${version_parts[0]:-0}
    local minor=${version_parts[1]:-0}
    local patch=${version_parts[2]:-0}
    
    case "$bump_type" in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
        *)
            echo "Error: Invalid bump type. Use: major|minor|patch"
            exit 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    set_version "$new_version"
}

sync_to_package_json() {
    local version=$1
    if [ -z "$version" ]; then
        version=$(get_current_version)
    fi
    
    if [ -f "$PACKAGE_JSON" ]; then
        # Use a simple sed or node-based approach
        if command -v node > /dev/null; then
            # Use node to update package.json (more reliable for JSON)
            node -e "
                const fs = require('fs');
                const pkg = JSON.parse(fs.readFileSync('$PACKAGE_JSON', 'utf8'));
                pkg.version = '$version';
                fs.writeFileSync('$PACKAGE_JSON', JSON.stringify(pkg, null, 2) + '\n');
            "
            echo "Synced version to frontend/package.json"
        else
            echo "Warning: node not found, skipping package.json sync"
        fi
    fi
}

# Main command handling
COMMAND=${1:-get}

case "$COMMAND" in
    get)
        echo "$(get_current_version)"
        ;;
    set)
        set_version "$2"
        ;;
    bump)
        bump_version "$2"
        ;;
    sync)
        sync_to_package_json
        echo "Version synced to package.json"
        ;;
    *)
        echo "Usage: $0 [get|set|bump|sync] [version|bump_type]"
        echo ""
        echo "Commands:"
        echo "  get              Show current version (default)"
        echo "  set <version>    Set version (e.g., 0.1.0)"
        echo "  bump <type>      Bump version (major|minor|patch)"
        echo "  sync             Sync version to package.json"
        exit 1
        ;;
esac

