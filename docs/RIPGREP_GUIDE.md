# Ripgrep Quick Reference

Ripgrep (`rg`) is a fast, recursive grep replacement. Syntax aligns with grep but optimized for speed.

## Common Flags

- `-i` / `--ignore-case` - Case insensitive
- `-n` / `--line-number` - Show line numbers
- `-A N` - Show N lines after match
- `-B N` - Show N lines before match
- `-C N` / `--context N` - Show N lines before and after
- `-v` / `--invert-match` - Invert match
- `-c` / `--count` - Count matches
- `-e PATTERN` - Specify pattern (allows multiple patterns)
- `-g GLOB` - Include files matching glob
- `-t TYPE` - Filter by file type (e.g., `-t log`, `-t py`)
- `--type-not TYPE` - Exclude file type
- `--color always` - Force color output
- `-w` / `--word-regexp` - Match whole words
- `-F` / `--fixed-strings` - Literal string match (no regex)
- `-E` / `--regexp` - Extended regex (default)

## Log Analysis Examples

### 1. Find all errors
```bash
rg -i "error|exception|fatal" log.txt
```

### 2. Errors with 5 lines of context
```bash
rg -i "error" -C 5 log.txt
```

### 3. Stack traces (multi-line context)
```bash
rg -A 20 "Exception\|Traceback" log.txt
```

### 4. Case-insensitive search
```bash
rg -i "debug" log.txt
```

### 5. Show line numbers
```bash
rg -n "ERROR" log.txt
```

### 6. Count matches
```bash
rg -c "timeout" log.txt
```

### 7. Multiple patterns (OR)
```bash
rg -e "ERROR" -e "WARN" -e "FATAL" log.txt
```

### 8. Invert match (exclude pattern)
```bash
rg -v "DEBUG" log.txt
```

### 9. Word boundaries (exact word match)
```bash
rg -w "error" log.txt
```

### 10. Find IP addresses
```bash
rg "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b" log.txt
```

### 11. Timestamp patterns
```bash
rg "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}" log.txt
```

### 12. UUIDs or request IDs
```bash
rg "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" log.txt
```

### 13. Errors excluding DEBUG lines
```bash
rg -i "error" -v "debug" log.txt
```

### 14. Search specific file types
```bash
rg "ERROR" -t log
```

### 15. Exclude file types
```bash
rg "ERROR" --type-not log
```

### 16. Glob pattern (specific files)
```bash
rg "ERROR" -g "*.log"
```

### 17. Combined: case-insensitive, line numbers, context
```bash
rg -in -C 3 "error" log.txt
```

### 18. Literal string (no regex)
```bash
rg -F "user.login" log.txt
```

### 19. Errors between timestamps (with context)
```bash
rg -A 2 -B 2 "2024-01-15 14:" log.txt | rg "ERROR"
```

### 20. Count errors per file (recursive)
```bash
rg -c "ERROR" --type log
```

## Block Extraction (Start:End Patterns)

Ripgrep doesn't have native range syntax. Use these approaches:

### Extract block with fixed context after start pattern
```bash
rg -A 50 "START_PATTERN" log.txt
```

### Extract block between patterns (combine with sed)
```bash
rg -n "START_PATTERN\|END_PATTERN" log.txt | sed -n '/START_PATTERN/,/END_PATTERN/p'
```

### Extract block between patterns (combine with awk)
```bash
awk '/START_PATTERN/,/END_PATTERN/' log.txt
```

### Multiline block extraction (requires PCRE2-enabled ripgrep)
```bash
rg --pcre2 -z -o '(?s)START_PATTERN.*?END_PATTERN' log.txt
```