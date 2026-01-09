#!/usr/bin/env python3
"""
Analyze version bump commits and generate changelog entries.
"""

import subprocess
import re
from collections import defaultdict
from datetime import datetime

def run_git_command(cmd):
    """Run a git command and return output."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd='/Users/hanifm/awebees'
    )
    return result.stdout.strip()

def get_version_bump_commits():
    """Get all version bump commits in chronological order."""
    output = run_git_command(
        "git log --format='%H|%ai|%s' --all --reverse | grep -i 'bump version' | grep -v 'WIP\\|index'"
    )
    commits = []
    for line in output.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 3:
            commit_hash = parts[0]
            date_str = parts[1]
            message = '|'.join(parts[2:])
            # Extract version number
            version_match = re.search(r'(\d+\.\d+\.\d+)', message)
            if version_match:
                version = version_match.group(1)
                commits.append({
                    'hash': commit_hash,
                    'date': date_str.split()[0],  # Just the date part
                    'version': version,
                    'message': message
                })
    return commits

def get_commits_between(start_hash, end_hash):
    """Get all commits between two hashes (excluding start, including end)."""
    if start_hash:
        cmd = f"git log --format='%s' '{start_hash}^..{end_hash}'"
    else:
        # First version - get all commits up to this one
        cmd = f"git log --format='%s' '{end_hash}'"
    
    output = run_git_command(cmd)
    commits = [line.strip() for line in output.split('\n') if line.strip()]
    # Filter out version bump commits themselves
    commits = [c for c in commits if not re.search(r'bump version to \d+\.\d+\.\d+', c, re.I)]
    return commits

def categorize_commit(message):
    """Categorize a commit message into Added/Changed/Fixed/Removed."""
    message_lower = message.lower()
    
    # Keywords for categorization
    if any(word in message_lower for word in ['add', 'new', 'create', 'implement', 'introduce', 'support']):
        return 'Added'
    elif any(word in message_lower for word in ['fix', 'bug', 'error', 'issue', 'correct', 'resolve']):
        return 'Fixed'
    elif any(word in message_lower for word in ['remove', 'delete', 'deprecate', 'drop']):
        return 'Removed'
    elif any(word in message_lower for word in ['update', 'change', 'modify', 'improve', 'refactor', 'enhance', 'optimize']):
        return 'Changed'
    else:
        return 'Changed'  # Default

def analyze_version_changes(commits):
    """Analyze changes for each version."""
    version_changes = []
    
    for i, version_commit in enumerate(commits):
        version = version_commit['version']
        date = version_commit['date']
        hash_val = version_commit['hash']
        
        # Get previous version hash
        prev_hash = commits[i-1]['hash'] if i > 0 else None
        
        # Get commits between previous version and this one
        change_commits = get_commits_between(prev_hash, hash_val)
        
        # Categorize changes
        categorized = defaultdict(list)
        for commit_msg in change_commits:
            category = categorize_commit(commit_msg)
            # Clean up commit message for changelog
            clean_msg = commit_msg.strip()
            # Remove common prefixes
            clean_msg = re.sub(r'^(feat|fix|chore|docs|style|refactor|perf|test):\s*', '', clean_msg, flags=re.I)
            categorized[category].append(clean_msg)
        
        version_changes.append({
            'version': version,
            'date': date,
            'changes': dict(categorized)
        })
    
    return version_changes

def generate_changelog(version_changes):
    """Generate changelog markdown."""
    lines = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),",
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).",
        ""
    ]
    
    # Sort by version (newest first for changelog)
    for version_info in reversed(version_changes):
        version = version_info['version']
        date = version_info['date']
        changes = version_info['changes']
        
        lines.append(f"## [{version}] - {date}")
        lines.append("")
        
        # Add sections in order: Added, Changed, Fixed, Removed
        for category in ['Added', 'Changed', 'Fixed', 'Removed']:
            if category in changes and changes[category]:
                lines.append(f"### {category}")
                for change in changes[category][:10]:  # Limit to 10 items per category
                    lines.append(f"- {change}")
                lines.append("")
        
        # Add release link
        lines.append(f"[{version}]: https://github.com/hihanifm/awebees/releases/tag/v{version}")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    print("Collecting version bump commits...")
    commits = get_version_bump_commits()
    print(f"Found {len(commits)} version bump commits")
    
    print("Analyzing changes for each version...")
    version_changes = analyze_version_changes(commits)
    
    print("Generating changelog...")
    changelog = generate_changelog(version_changes)
    
    print("\n" + "="*80)
    print("Generated CHANGELOG.md content:")
    print("="*80)
    print(changelog)
    
    # Write to file
    with open('/Users/hanifm/awebees/CHANGELOG.md', 'w') as f:
        f.write(changelog)
    
    print("\n" + "="*80)
    print("CHANGELOG.md has been updated!")

if __name__ == '__main__':
    main()
