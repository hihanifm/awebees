# Lens Features

**Version:** 3.4.0  
**Last Updated:** January 6, 2026

A comprehensive overview of Lens capabilities, both implemented and planned.

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

#### 🔍 File Analysis Engine
- **Multi-file processing**: Analyze multiple log files simultaneously
- **Folder scanning**: Recursive scanning of directories
- **Large file support**: Optimized for files 250MB+
- **Memory-efficient processing**: Line-by-line and chunked reading modes
- **Real-time progress tracking**: Live updates during analysis
- **Cancellation support**: Stop analysis mid-flight
- **Path normalization**: Auto-strips quotes and handles spaces

#### 📊 Insight System
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

#### 🎯 Sample Files
- **Pre-loaded Android bugreport**: 54.6MB real-world sample
  - 650,402 total lines
  - 1,808 ERROR/FATAL lines
  - Auto-extracted on first startup
- **One-click testing**: "Load Sample File" button in UI
- **CLI support**: Test insights via command line with samples

### Insights System

#### Config-Based Insights (v3.3.0+)
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

#### Class-Based Insights
- Full control over analysis logic
- Custom state management
- Multi-pass analysis support
- Complex transformations and aggregations
- Perfect for non-filtering operations

#### Insight Features
- **File filtering**: Regex-based file filtering for folders
- **Line filtering**: Powerful regex pattern matching
- **Multiple reading modes**:
  - Line-by-line (memory efficient)
  - Chunked (faster for large files, 1MB chunks)
- **Regex flags**: Support for IGNORECASE, MULTILINE, DOTALL, etc.
- **Progress events**: Emits events for file opening, processing, completion
- **Error handling**: Graceful error handling with detailed logging
- **Result formatting**: Flexible text, JSON, or custom formats

### User Interface

#### 🖥️ Web Interface (Next.js + TypeScript)
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

#### 📱 Responsive Design
- **90% screen width**: Makes optimal use of screen space
- **Adaptive layouts**: Works on desktop and tablet
- **Accessible**: Keyboard navigation and screen reader support

### Performance & Optimization

#### ⚡ File Processing
- **Chunked reading**: 1MB chunks for large files
- **Line-by-line mode**: Memory-efficient for smaller files
- **Generator-based**: Lazy evaluation for memory efficiency
- **Cancellation checks**: Frequent checks to enable quick cancellation
- **Memory-mapped files**: For extremely large files
- **Binary mode reading**: True byte-level chunking

#### 🚀 Progress & Responsiveness
- **Server-Sent Events (SSE)**: Real-time progress streaming
- **Async/await**: Non-blocking I/O operations
- **Thread-based analysis**: CPU-bound work in separate threads
- **Thread-safe callbacks**: Safe progress updates from worker threads
- **Event loop yielding**: `asyncio.sleep(0)` for immediate SSE flushing
- **CORS preflight caching**: 1-hour cache to reduce OPTIONS requests

#### 🔧 Profiling & Debugging
- **cProfile integration**: Built-in performance profiling
- **Environment variable control**: `ENABLE_PROFILING=true`
- **Profiling decorator**: Reusable `@profile` for functions/generators
- **Profiling wrapper script**: `scripts/run_python.sh` with cProfile
- **Top consumers**: Shows top 10 CPU-intensive operations
- **Regex search stats**: Filters `re.Pattern.search` profiling data

### Cross-Platform Support

#### 🐧 Linux/Mac
- **Bash scripts**: Full automation (setup, start, stop, logs, version)
- **Virtual environment management**: Automatic venv creation and activation
- **Development & production modes**: Separate configurations
- **Log management**: Rotating logs with tail support

#### 🪟 Windows
- **Batch scripts**: CMD-based (no PowerShell policy issues)
- **Automatic installation**: `winget` integration for Python/Node.js
- **Installer packages**:
  - Self-contained (with Python): 100% portable
  - Python-required (smaller size): Uses system Python
- **NSIS installers**: Professional Windows installers
- **Auto-extraction**: Sample files extracted on first run
- **Log viewing**: `lens-logs.bat` for easy log access
- **Path handling**: Robust handling of paths with spaces/parentheses

#### 🌐 Web API (FastAPI)
- **RESTful API**: Clean, documented endpoints
- **OpenAPI/Swagger**: Auto-generated API docs at `/docs`
- **SSE streaming**: Real-time progress and error streaming
- **CORS support**: Configurable cross-origin access
- **Health checks**: `/api/health` for monitoring
- **Version endpoint**: `/api/version` for version info
- **Profiling status**: `/api/profiling` to check profiling state

### Developer Experience

#### 🛠️ Development Tools
- **Hot reload**: Frontend auto-reloads on changes
- **Separate dev servers**: Frontend (34000) + Backend (34001)
- **Environment variables**: `.env` files for configuration
- **Comprehensive logging**: DEBUG, INFO, WARNING, ERROR levels
- **Linting**: Zero linter errors policy
- **Type safety**: TypeScript for frontend

#### 📚 Documentation
- **Main README**: Comprehensive setup and usage guide
- **Insights README**: Detailed insight creation guide (`backend/app/insights/README.md`)
- **Sample README**: Sample file documentation (`backend/samples/README.md`)
- **Windows guides**: Dedicated Windows setup and troubleshooting docs
- **Code examples**: Real-world examples (error_detector, line_count)
- **Inline documentation**: Docstrings and comments throughout

#### 🧪 Testing & Debugging
- **Standalone insight execution**: Run insights directly via CLI
- **Test runner script**: `scripts/run_insight.py` for easy testing
- **Interactive mode**: Prompts for file paths if not provided
- **Verbose logging**: `--verbose` flag for detailed output
- **Sample files**: Pre-loaded samples for immediate testing
- **Error streaming**: Real-time error notifications
- **Progress tracking**: Visual feedback during analysis

#### 🔄 Version Management
- **Unified versioning**: Single `VERSION` file as source of truth
- **Auto-sync**: Syncs to `package.json` automatically
- **Version scripts**: Easy bump commands (major/minor/patch)
- **Git workflow**: Integrated with tagging and releases

#### 📦 Package Management
- **Requirements.txt**: Python dependencies with versions
- **Package.json**: Node.js dependencies
- **Virtual environment**: Isolated Python dependencies
- **Node modules**: Isolated Node.js dependencies

---

## Upcoming Features

### High Priority

#### 📁 Collections for Insights
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

### Medium Priority

#### ⭐ Favorites System
**Status:** Planned  
**Description:** Mark frequently-used insights as favorites for quick access

**Features:**
- Star/favorite button per insight
- Favorites section at the top of insight list
- Persist favorites in local storage
- Quick toggle on/off

#### 🔍 Insight Search
**Status:** Planned  
**Description:** Search functionality to quickly find insights

**Features:**
- Real-time search as you type
- Search by name, description, or tags
- Keyboard shortcuts (Ctrl/Cmd+F)
- Fuzzy matching support
- Highlight search matches

#### 🤖 AI/ML Insight Prediction
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

#### 📂 Session Management
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

#### 💾 Frontend Caching
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

#### 📊 Offline Result Storage
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

#### 🕐 Recent Inputs
**Status:** Planned  
**Description:** Quick access to recently-used file paths

**Features:**
- Show last 10 file/folder inputs
- Dropdown menu for quick selection
- Clear history option
- Persistent across sessions
- Smart deduplication

#### 📈 Analysis Summary Card
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

---

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

### v3.4.0 (Current)
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

**Maintained by:** Lens Team  
**Repository:** https://github.com/hihanifm/awebees  
**License:** See LICENSE file

