# LensAI Features

**Version:** 3.6.0  
**Last Updated:** January 6, 2026

A comprehensive overview of LensAI capabilities, both implemented and planned.

---

## 📋 Table of Contents

- [Current Features](#current-features)
  - [Core Functionality](#core-functionality)
  - [Insights System](#insights-system)
  - [User Interface](#user-interface)
  - [Performance & Optimization](#performance--optimization)
  - [Cross-Platform Support](#cross-platform-support)
  - [Developer Experience](#developer-experience)
- [Upcoming Features](#upcoming-features)
  - [High Priority](#high-priority)
  - [Medium Priority](#medium-priority)
  - [Low Priority](#low-priority)

---

## Current Features

### Core Functionality

<details><summary><b>🔍 File Analysis Engine</b></summary>

- **Multi-file processing**: Analyze multiple log files simultaneously
- **Folder scanning**: Recursive scanning of directories
- **Large file support**: Optimized for files 250MB+
- **Memory-efficient processing**: Line-by-line and chunked reading modes
- **Real-time progress tracking**: Live updates during analysis
- **Cancellation support**: Stop analysis mid-flight
- **Path normalization**: Auto-strips quotes and handles spaces

</details>


<details><summary><b>📊 Insight System</b></summary>

- **Pluggable architecture**: Dynamic discovery and registration of insights
- **Two implementation approaches**:
  - **Config-based insights** (New!): 70% less code, declarative configuration
  - **Class-based insights**: Full control for complex logic
- **Built-in insights**:
  - **Error Detector**: Finds ERROR and FATAL log lines (config-based)
  - **Line Count**: Counts total, empty, and non-empty lines (class-based)
- **Folder organization**: Insights can be organized in subdirectories
- **Standalone execution**: Run insights independently from CLI
- **Progress callbacks**: Real-time progress updates per insight
- **Cancellation aware**: Respects cancellation events

</details>


<details><summary><b>🎯 Sample Files</b></summary>

- **Pre-loaded Android bugreport**: 54.6MB real-world sample
  - 650,402 total lines
  - 1,808 ERROR/FATAL lines
  - Auto-extracted on first startup
- **One-click testing**: "Load Sample File" button in UI
- **CLI support**: Test insights via command line with samples

</details>


### Insights System

<details><summary><b>Config-Based Insights (v3.3.0+)</b></summary>

```python
# Simple declarative approach
INSIGHT_CONFIG = {
    "metadata": {"id": "...", "name": "...", "description": "..."},
    "filters": {
        "file_patterns": [...],  # Optional file filtering
        "line_pattern": r"...",  # Required regex
        "regex_flags": "IGNORECASE",
        "reading_mode": "lines"  # or "chunks"
    }
}

# Optional post-processing
def process_results(filter_result):
    return {"content": "...", "metadata": {...}}
```

**Benefits:**
- 70% code reduction vs class-based
- Declarative configuration
- Automatic progress tracking
- Built-in cancellation support
- Standalone execution ready

</details>


<details><summary><b>Class-Based Insights</b></summary>

- Full control over analysis logic
- Custom state management
- Multi-pass analysis support
- Complex transformations and aggregations
- Perfect for non-filtering operations

</details>


<details><summary><b>Insight Features</b></summary>

- **File filtering**: Regex-based file filtering for folders
- **Line filtering**: Powerful regex pattern matching
- **Multiple reading modes**:
  - Line-by-line (memory efficient)
  - Chunked (faster for large files, 1MB chunks)
- **Regex flags**: Support for IGNORECASE, MULTILINE, DOTALL, etc.
- **Progress events**: Emits events for file opening, processing, completion
- **Error handling**: Graceful error handling with detailed logging
- **Result formatting**: Flexible text, JSON, or custom formats

</details>


### User Interface

<details><summary><b>🖥️ Web Interface (Next.js + TypeScript)</b></summary>

- **Modern, responsive design**: Tailwind CSS + shadcn/ui components
- **Dark mode support**: Full dark/light theme support
- **File path input**: Multi-line textarea with auto-save
- **Insight selection**: Organized by folders with accordions
- **"Load Sample File" button**: Quick access to pre-loaded sample
- **Real-time progress widget**:
  - Live event stream (SSE)
  - Shows all events with scrolling
  - File-by-file progress
  - Lines processed counter
  - Cancel button
- **Results panel**: Formatted, syntax-highlighted output
- **Error notifications**: Dismissible error banners
- **Backend error streaming**: Real-time error alerts from server
- **Status footer**:
  - Version number
  - Environment (DEV/PROD)
  - API status (Online/Offline)
  - Profiling indicator

</details>


<details><summary><b>📱 Responsive Design</b></summary>

- **90% screen width**: Makes optimal use of screen space
- **Adaptive layouts**: Works on desktop and tablet
- **Accessible**: Keyboard navigation and screen reader support

</details>


### Performance & Optimization

<details><summary><b>⚡ File Processing</b></summary>

- **Chunked reading**: 1MB chunks for large files
- **Line-by-line mode**: Memory-efficient for smaller files
- **Generator-based**: Lazy evaluation for memory efficiency
- **Cancellation checks**: Frequent checks to enable quick cancellation
- **Memory-mapped files**: For extremely large files
- **Binary mode reading**: True byte-level chunking

</details>


<details><summary><b>🚀 Progress & Responsiveness</b></summary>

- **Server-Sent Events (SSE)**: Real-time progress streaming
- **Async/await**: Non-blocking I/O operations
- **Thread-based analysis**: CPU-bound work in separate threads
- **Thread-safe callbacks**: Safe progress updates from worker threads
- **Event loop yielding**: `asyncio.sleep(0)` for immediate SSE flushing
- **CORS preflight caching**: 1-hour cache to reduce OPTIONS requests

</details>


<details><summary><b>🔧 Profiling & Debugging</b></summary>

- **cProfile integration**: Built-in performance profiling
- **Environment variable control**: `ENABLE_PROFILING=true`
- **Profiling decorator**: Reusable `@profile` for functions/generators
- **Profiling wrapper script**: `scripts/run_python.sh` with cProfile
- **Top consumers**: Shows top 10 CPU-intensive operations
- **Regex search stats**: Filters `re.Pattern.search` profiling data

</details>


### Cross-Platform Support

<details><summary><b>🐧 Linux/Mac</b></summary>

- **Bash scripts**: Full automation (setup, start, stop, logs, version)
- **Virtual environment management**: Automatic venv creation and activation
- **Development & production modes**: Separate configurations
- **Log management**: Rotating logs with tail support

</details>


<details><summary><b>🪟 Windows</b></summary>

- **Batch scripts**: CMD-based (no PowerShell policy issues)
- **Automatic installation**: `winget` integration for Python/Node.js
- **Installer packages**:
  - Self-contained (with Python): 100% portable
  - Python-required (smaller size): Uses system Python
- **NSIS installers**: Professional Windows installers
- **Auto-extraction**: Sample files extracted on first run
- **Log viewing**: `lens-logs.bat` for easy log access
- **Path handling**: Robust handling of paths with spaces/parentheses

</details>


<details><summary><b>🌐 Web API (FastAPI)</b></summary>

- **RESTful API**: Clean, documented endpoints
- **OpenAPI/Swagger**: Auto-generated API docs at `/docs`
- **SSE streaming**: Real-time progress and error streaming
- **CORS support**: Configurable cross-origin access
- **Health checks**: `/api/health` for monitoring
- **Version endpoint**: `/api/version` for version info
- **Profiling status**: `/api/profiling` to check profiling state

</details>


### Developer Experience

<details><summary><b>🛠️ Development Tools</b></summary>

- **Hot reload**: Frontend auto-reloads on changes
- **Separate dev servers**: Frontend (34000) + Backend (34001)
- **Environment variables**: `.env` files for configuration
- **Comprehensive logging**: DEBUG, INFO, WARNING, ERROR levels
- **Linting**: Zero linter errors policy
- **Type safety**: TypeScript for frontend

</details>


<details><summary><b>📚 Documentation</b></summary>

- **Main README**: Comprehensive setup and usage guide
- **Insights README**: Detailed insight creation guide (`backend/app/insights/README.md`)
- **Sample README**: Sample file documentation (`backend/samples/README.md`)
- **Windows guides**: Dedicated Windows setup and troubleshooting docs
- **Code examples**: Real-world examples (error_detector, line_count)
- **Inline documentation**: Docstrings and comments throughout

</details>


<details><summary><b>🧪 Testing & Debugging</b></summary>

- **Standalone insight execution**: Run insights directly via CLI
- **Test runner script**: `scripts/run_insight.py` for easy testing
- **Interactive mode**: Prompts for file paths if not provided
- **Verbose logging**: `--verbose` flag for detailed output
- **Sample files**: Pre-loaded samples for immediate testing
- **Error streaming**: Real-time error notifications
- **Progress tracking**: Visual feedback during analysis

</details>


<details><summary><b>🔄 Version Management</b></summary>

- **Unified versioning**: Single `VERSION` file as source of truth
- **Auto-sync**: Syncs to `package.json` automatically
- **Version scripts**: Easy bump commands (major/minor/patch)
- **Git workflow**: Integrated with tagging and releases

</details>


<details><summary><b>📦 Package Management</b></summary>

- **Requirements.txt**: Python dependencies with versions
- **Package.json**: Node.js dependencies
- **Virtual environment**: Isolated Python dependencies
- **Node modules**: Isolated Node.js dependencies

---

</details>


## Upcoming Features

### High Priority

<details><summary><b>📁 Collections for Insights</b></summary>

**Status:** Planned  
**Description:** Group related insights into collections for better organization

**Features:**
- Store collections as configuration files
- Users can create custom collections
- Local storage on user's PC
- Optional GitHub upload for sharing
- Collection management UI

**Use Cases:**
- Android analysis collection (error detector, crash analyzer, ANR detector)
- Performance analysis collection
- Security audit collection
- Custom domain-specific collections

---


</details>

### Medium Priority

<details><summary><b>⭐ Favorites System</b></summary>

**Status:** Planned  
**Description:** Mark frequently-used insights as favorites for quick access

**Features:**
- Star/favorite button per insight
- Favorites section at the top of insight list
- Persist favorites in local storage
- Quick toggle on/off


</details>

<details><summary><b>🔍 Insight Search</b></summary>

**Status:** Planned  
**Description:** Search functionality to quickly find insights

**Features:**
- Real-time search as you type
- Search by name, description, or tags
- Keyboard shortcuts (Ctrl/Cmd+F)
- Fuzzy matching support
- Highlight search matches


</details>

<details><summary><b>🤖 AI/ML Insight Prediction</b></summary>

**Status:** Planned (Research phase)  
**Description:** Use vector database and ML to predict relevant insights

**Features:**
- Build vector database of insight descriptions and use cases
- Analyze file content patterns
- Suggest relevant insights automatically
- Learn from user selections
- Confidence scores for suggestions

**Technology:**
- Vector database (e.g., Pinecone, Weaviate, ChromaDB)
- Embeddings (OpenAI, Sentence Transformers)
- Pattern recognition
- Collaborative filtering


</details>

<details><summary><b>📂 Session Management</b></summary>

**Status:** Planned  
**Description:** Store and manage analysis sessions

**Features:**
- Save analysis results per session
- Session tabs on left sidebar
- Reopen past sessions
- Session history
- Delete old sessions

**Storage Structure:**
```
sessions/
  session-{id}/
    metadata.json
    insights/
      error_detector/
        file1.log.txt
        file2.log.txt
      line_count/
        file1.log.txt
```

</details>


<details><summary><b>💾 Frontend Caching</b></summary>

**Status:** Planned  
**Description:** Local database for frontend to cache data

**Features:**
- Cache collection lists
- Cache insight metadata
- Reduce API calls
- Faster UI responsiveness
- IndexedDB or localStorage

**Benefits:**
- Faster page loads
- Offline capability (partial)
- Reduced server load
- Better UX

</details>


<details><summary><b>📊 Offline Result Storage</b></summary>

**Status:** Planned  
**Description:** Store analysis results in files for offline access

**Features:**
- Save results to disk automatically
- Structured folder hierarchy per session
- "Open Output Folder" button in UI
- Export results as HTML/PDF
- Share results easily

**File Structure:**
```
output/
  session-{timestamp}/
    {insight-name}/
      {filename}/
        result.txt
        metadata.json
```

</details>


<details><summary><b>🕐 Recent Inputs</b></summary>

**Status:** Planned  
**Description:** Quick access to recently-used file paths

**Features:**
- Show last 10 file/folder inputs
- Dropdown menu for quick selection
- Clear history option
- Persistent across sessions
- Smart deduplication

</details>


<details><summary><b>📈 Analysis Summary Card</b></summary>

**Status:** Planned  
**Description:** Overview card showing analysis statistics

**Features:**
- Number of insights executed
- Time per insight
- Total analysis time
- Files processed count
- Lines processed count
- Success/failure status
- Visual timeline chart

**Example:**
```
Analysis Summary
━━━━━━━━━━━━━━━━━━━━━
Total Time: 2.5s
Insights: 2/2 successful

Timeline:
  Error Detector ████░░ 1.2s
  Line Count     ██████ 1.3s
  
Files: 3
Lines: 650,402
```

</details>


<details><summary><b>⚙️ Settings Page</b></summary>

**Status:** Planned  
**Description:** Centralized settings page for controlling application behavior

**Features:**
- **Backend Configuration**: API endpoints, timeouts, retry settings
- **AI Configuration**: Model selection, API keys, temperature settings
- **Path Settings**: Default file paths, recent paths limit, path validation rules
- **Theme Settings**: Dark/light mode, custom color schemes, font sizes
- **Language Settings**: Multi-language support, locale preferences
- **Upgrade Options**: Auto-update checks, version notifications, upgrade paths
- **Performance Settings**: Chunk size, memory limits, thread count
- **Privacy Settings**: Telemetry, usage analytics, error reporting

**UI Components:**
- Tabbed interface for different setting categories
- Real-time preview of changes
- Import/export settings as JSON
- Reset to defaults option
- Save confirmation with validation

</details>


<details><summary><b>🎮 Playground Mode</b></summary>

**Status:** Planned  
**Description:** Interactive environment for testing filters and insights

**Features:**
- **Dynamic Filter Creation**: Build regex patterns with live preview
- **File Upload**: Upload sample files directly to server
- **Live Testing**: Test filters against uploaded files in real-time
- **Pattern Library**: Save and reuse common patterns
- **Regex Helper**: Visual regex builder with syntax highlighting
- **Match Preview**: See matching lines instantly
- **Performance Metrics**: Show processing time and resource usage
- **Export to Insight**: Convert playground filter to full insight

**Use Cases:**
- Test regex patterns before creating insights
- Prototype new insights quickly
- Share filter patterns with team
- Learn regex and pattern matching
- Debug existing filters

**UI:**
```
┌─────────────────────────────────────────┐
│ Playground                               │
├─────────────────────────────────────────┤
│ Upload File: [Browse...] sample.log     │
│                                          │
│ Filter Pattern: \b(ERROR|FATAL)\b       │
│ Flags: ☑ IGNORECASE  ☐ MULTILINE       │
│                                          │
│ [Test Filter]  [Save]  [Export]         │
│                                          │
│ Results: 125 matches in 0.3s            │
│ ┌─────────────────────────────────────┐ │
│ │ 2024-01-06 ERROR: Connection failed │ │
│ │ 2024-01-06 FATAL: System crash     │ │
│ │ ...                                  │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

</details>


<details><summary><b>📦 Insight Marketplace</b></summary>

**Status:** Planned  
**Description:** Download and share insights from community repository

**Features:**
- **Browse Insights**: Searchable catalog of community insights
- **Categories**: Organized by domain (Android, iOS, Web, Security, etc.)
- **Ratings & Reviews**: User feedback and ratings
- **Version Management**: Track insight versions and updates
- **Auto-Updates**: Notify when insights have updates
- **One-Click Install**: Download and install with single click
- **Contribution**: Upload your own insights to share
- **Security Scanning**: Validate insights before installation

**Marketplace Structure:**
```
Insight Repository
├── Featured (Staff picks)
├── Most Popular (By downloads)
├── Recently Added (New insights)
├── Categories
│   ├── Android
│   ├── iOS
│   ├── Web Server Logs
│   ├── Security & Compliance
│   ├── Performance Analysis
│   └── Custom/Other
└── My Insights (Downloaded)
```

**Metadata:**
- Author information
- Download count
- Last updated date
- Compatibility version
- Dependencies
- License
- Documentation link
- Example outputs

</details>


<details><summary><b>🎨 Rich Output Support</b></summary>

**Status:** Planned  
**Description:** Enhanced visualization options for insight results

**Current State:**
- Plain text output only
- Limited formatting options
- No visual representations

**Planned Features:**

**Color Support:**
- Syntax highlighting for code/logs
- Color-coded severity levels (ERROR=red, WARNING=yellow, INFO=blue)
- Custom color schemes
- ANSI color support in terminal output
- CSS-based coloring in web UI

**Tables:**
- Formatted data tables with sortable columns
- CSV export functionality
- Compact and expanded views
- Column filtering and search
- Auto-sizing columns

**Graphs & Charts:**
- Line charts (trends over time)
- Bar charts (comparisons)
- Pie charts (distributions)
- Scatter plots (correlations)
- Heatmaps (patterns)
- Interactive zoom and pan

**Timeline Visualizations:**
- Event timeline with markers
- Time-series data visualization
- Duration bars for operations
- Concurrent event tracks
- Zoom to time ranges
- Click to see event details

**Interactive Elements:**
- Collapsible sections
- Expandable details
- Tooltips on hover
- Click-to-filter
- Drill-down navigation

**Example Outputs:**

**Colored Error Log:**
```
🔴 ERROR: Connection timeout at 10:30:45
🟡 WARNING: Retry attempt 1/3
🟢 INFO: Connection restored at 10:30:47
```

**Table Output:**
```
┌──────────────┬───────┬──────────┬──────────┐
│ File         │ Lines │ Errors   │ Duration │
├──────────────┼───────┼──────────┼──────────┤
│ app.log      │ 1.2M  │ 156      │ 2.3s     │
│ system.log   │ 850K  │ 89       │ 1.8s     │
│ crash.log    │ 450K  │ 1,203    │ 1.2s     │
└──────────────┴───────┴──────────┴──────────┘
```

**Timeline Output:**
```
10:00 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 11:00
      │         │            │
      ◆ Start   ⚠ Warning   ✖ Crash
      10:15     10:42        10:58
```

**Chart (ASCII for terminal):**
```
Errors by Hour
 50 ┤     ╭╮
 40 ┤   ╭╯╰╮
 30 ┤  ╭╯  ╰╮
 20 ┤╭╯     ╰╮
 10 ┼╯       ╰
    └─────────────
    08 10 12 14
```

**Technology Stack:**
- **Frontend**: D3.js, Chart.js, or Recharts for graphs
- **Terminal**: Rich (Python library) for colored terminal output
- **Tables**: TanStack Table (React) for web, tabulate (Python) for CLI
- **Syntax Highlighting**: Prism.js or Highlight.js
- **Color Management**: Chalk (Node.js), Colorama (Python)

**Result Types:**
```python
class InsightResult:
    result_type: str  # "text", "table", "chart", "timeline", "html"
    content: Any
    metadata: Dict
    visualization_config: Optional[Dict]  # Chart/table settings
```

**Benefits:**
- Better data comprehension
- Faster pattern recognition
- More engaging user experience
- Professional presentation
- Export-ready formats

---

</details>


### Low Priority

*No items currently planned*

---

## Feature Status Legend

- ✅ **Implemented**: Feature is live and available
- 🚧 **In Progress**: Currently being developed
- 📋 **Planned**: Designed and scheduled
- 💡 **Proposed**: Idea under consideration
- 🔬 **Research**: Exploring feasibility

---

## Contributing

Have ideas for new features? We'd love to hear them!

1. Check if it's already in this document
2. Open an issue on GitHub with the `feature-request` label
3. Describe the use case and expected behavior
4. If you can implement it, submit a PR!

---

## Version History

### v3.6.0 (Current)
- ✅ Compact grid layout for insights
- ✅ Auto-responsive columns (1-5 based on screen width)
- ✅ Warm peachy hover effects on insight cards
- ✅ Enhanced tooltips with warm styling
- ✅ Bold title bar with gradient background
- ✅ Title bar connects to top edge

### v3.5.0
- ✅ Warm pastel color scheme (peach, coral, amber)
- ✅ OKLCH color space with warm hues
- ✅ Gradient backgrounds and enhanced UI
- ✅ WCAG AA accessibility maintained
- ✅ Pleasant visual experience in both modes

### v3.4.0
- ✅ Config-based insights system
- ✅ Android bugreport sample file (54.6MB)
- ✅ "Load Sample File" button
- ✅ Auto-extraction of samples
- ✅ Sample files API endpoint
- ✅ Enhanced button visibility

### v3.3.0
- ✅ Config-based insights architecture
- ✅ ConfigBasedInsight class
- ✅ Config insight runner
- ✅ Migrated error_detector to config-based
- ✅ Comprehensive documentation

### v3.0.0
- ✅ Major architecture improvements
- ✅ Filter-based insight template
- ✅ Improved file handler performance
- ✅ Enhanced error handling

### v2.x
- ✅ Real-time progress tracking (SSE)
- ✅ Cancellation support
- ✅ Insight folders/organization
- ✅ Backend error streaming
- ✅ Windows installer packages
- ✅ Production frontend serving

### v1.x
- ✅ Initial release
- ✅ Basic insight system
- ✅ Web UI
- ✅ File analysis engine

---

**Maintained by:** LensAI Team  
**Repository:** https://github.com/hihanifm/awebees  
**License:** See LICENSE file

