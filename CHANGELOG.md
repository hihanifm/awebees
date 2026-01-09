# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.13.0] - 2026-01-09

### Added
- Add version bump commit message guideline to engineering rules
- Add HEAD method support for Next.js prefetching
- Add Windows packages for v4.12.0

### Changed
- Update GitHub Pages to v4.12.0

### Fixed
- Fix version detection in Windows production mode

[4.13.0]: https://github.com/hihanifm/awebees/releases/tag/v4.13.0

## [4.12.0] - 2026-01-07

### Added
- Add proper error handling for AI auto-analysis failures

### Changed
- Polish AI buttons with gradient styling and bold all action buttons

### Fixed
- Fix AI settings reset and auto-trigger issues
- Fix excessive network requests when typing in Base URL field
- Fix version showing as 0.0.0 in Windows production mode

[4.12.0]: https://github.com/hihanifm/awebees/releases/tag/v4.12.0

## [4.11.0] - 2026-01-07

### Added
- Update e2e tests for new UI structure
- Add E2E tests with Playwright

### Changed
- Revert: Keep accordion folder structure for insights

### Fixed
- Fix insight text click selection

### Removed
- Simplify insight selection UI - remove folder accordion

[4.11.0]: https://github.com/hihanifm/awebees/releases/tag/v4.11.0

## [4.10.0] - 2026-01-07

### Added
- Add dynamic model fetching with hybrid direct/proxy approach
- Add comprehensive AI server interaction logging and error detection
- Add accessible logging settings feature

### Fixed
- Fix Test Connection to use current form values instead of saved config
- Fix playground not working in production mode

### Removed
- Remove redundant 'Available Insights' header

[4.10.0]: https://github.com/hihanifm/awebees/releases/tag/v4.10.0

## [4.9.0] - 2026-01-07

### Added
- Add Korean language support with full UI translation

[4.9.0]: https://github.com/hihanifm/awebees/releases/tag/v4.9.0

## [4.8.0] - 2026-01-07

### Fixed
- Improve regex error handling in playground filter

[4.8.0]: https://github.com/hihanifm/awebees/releases/tag/v4.8.0

## [4.7.0] - 2026-01-07

### Added
- Add command display and copy button to main page insight results
- Prepare release v4.6.0: Add Windows packages and update download page

### Fixed
- Fix Windows setup SSL certificate errors (UNABLE_TO_GET_ISSUER_CERT_LOCALLY)

[4.7.0]: https://github.com/hihanifm/awebees/releases/tag/v4.7.0

## [4.6.0] - 2026-01-07

### Changed
- Consolidate playground with tabs: Filter Mode and Quick Text

[4.6.0]: https://github.com/hihanifm/awebees/releases/tag/v4.6.0

## [4.5.0] - 2026-01-07

### Added
- Add text input page to playground with shared prompt configuration

[4.5.0]: https://github.com/hihanifm/awebees/releases/tag/v4.5.0

## [4.4.0] - 2026-01-07

### Added
- Add execution time to auto-triggered AI analysis and improve manual AI time visibility
- Add execution time display to AI analysis results cards

[4.4.0]: https://github.com/hihanifm/awebees/releases/tag/v4.4.0

## [4.3.0] - 2026-01-07

### Changed
- Make frontend localStorage source of truth once user saves settings, backend config for initial load

### Fixed
- Fix AI config check to trust backend is_configured flag
- Fix frontend AI analyze error handling and SSE parsing

[4.3.0]: https://github.com/hihanifm/awebees/releases/tag/v4.3.0

## [4.2.0] - 2026-01-07

### Added
- Fix GitHub Pages workflow: add required environment

### Changed
- Refine InsightList UI spacing and sizing
- Rebrand from Lens to LensAI - update all user-facing references
- Trigger GitHub Pages rebuild
- Prepare Windows packages v4.1.0 and update download page

[4.2.0]: https://github.com/hihanifm/awebees/releases/tag/v4.2.0

## [4.1.0] - 2026-01-07

### Added
- Add AI configuration validation and user guidance
- Add launch Lens option on installer finish page
- Add option to launch Lens at the end of Windows setup
- Fix GitHub Pages workflow: add github-pages environment
- Add automatic installation for Python and Node.js in setup.sh
- Add proper error handling for npm and pip install in setup.sh
- Add detailed OS detection and logging to shell scripts
- Add Git Bash alternative to Windows setup guide
- Add progress output and better error handling for production mode backend startup
- Add theme switcher and improve Windows setup consistency

### Changed
- Update Pages to v4.0.0
- Make shell scripts work on Windows via Git Bash (cross-platform venv activation)
- Make win-start continue even if PID detection fails (check port instead)
- Update download page to v4.0.0
- Make win-start backend/frontend PID detection more reliable

### Fixed
- Fix workflow to properly handle missing packages in release
- Fix production build: use npx next build instead of npm run build
- Fix Windows installer workflow: authenticate gh CLI and allow fallback to repo packages
- Fix production mode: change to frontend dir and check node_modules before build
- Fix win-start logging redirection quoting on Windows
- Fix win-start.bat parenthesis parsing error on Windows
- Build Windows packages for v4.0.0 and fix Next.js config

[4.1.0]: https://github.com/hihanifm/awebees/releases/tag/v4.1.0

## [4.0.0] - 2026-01-07

### Added
- Update Lens screenshots with new comprehensive workflow images
- Add second Playground screenshot showing AI configuration and analysis sections
- Add CC BY-NC-SA 4.0 license
- Add Playground feature for interactive ripgrep and AI experimentation
- Add Badge UI component for AI analysis display
- Implement AI auto-trigger for insights

### Changed
- Move Lens main interface screenshot to the top of README
- Update Playground screenshot to show complete workflow with all 5 sections
- Use consistent blue background for all AI analysis results

[4.0.0]: https://github.com/hihanifm/awebees/releases/tag/v4.0.0

## [3.9.0] - 2026-01-06

### Added
- Add AI auto-trigger support to config_insight_runner
- Add 300-line limit for AI analysis to control costs

### Changed
- Make ripgrep respect case sensitivity based on regex flags

### Fixed
- Fix RuntimeWarning in ripgrep subprocess
- Fix bug in config_insight_runner: interactive mode now works correctly

[3.9.0]: https://github.com/hihanifm/awebees/releases/tag/v3.9.0

## [3.8.0] - 2026-01-06

### Added
- Add OpenAI API key validation script
- Add context_before and context_after support for config-based insights
- Add toast notification components and fix npm install in setup.sh
- Add AI settings persistence to .env file
- Update insights: simplify fast_error_detector and error_detector implementations
- added new system_insights folder
- Add AI Processing Integration with OpenAI API support
- Add analysis statistics card with timing information

### Changed
- Tone down flashy selected state for insight cards
- Improve visual clarity of insight grid widgets
- Apply consistent muted background styling to file path input and activity history
- Make insight results scrollable with max height of ~30 lines

### Fixed
- Fix Next.js workspace root and Tailwind CSS resolution issue
- Fix AI service error handling for streaming responses

### Removed
- remove the duplicated
- Clean up insights: remove __main__ blocks

[3.8.0]: https://github.com/hihanifm/awebees/releases/tag/v3.8.0

## [3.7.0] - 2026-01-06

### Added
- Add ripgrep reading mode for 10-100x faster pattern matching
- Add 3D effect and colorful backgrounds to insight cards

### Changed
- Auto-update download page during Windows package build
- Update download page to v3.6.0
- Build and update Windows packages for v3.6.0

[3.7.0]: https://github.com/hihanifm/awebees/releases/tag/v3.7.0

## [3.6.0] - 2026-01-06

### Added
- Add bold title bar appearance to main Lens heading

### Changed
- Connect title bar to top edge with no margin
- Simplify title to clean title bar with background only
- Transform insights to compact grid layout with warm hover effects

### Fixed
- Fix grid overlapping issue in insights layout
- Fix win-start.bat: Use delayed expansion properly and improve .env parsing
- Fix win-start.bat error with environment variable parsing

[3.6.0]: https://github.com/hihanifm/awebees/releases/tag/v3.6.0

## [3.5.0] - 2026-01-06

### Added
- Add warm pastel color scheme to frontend UI
- Add GitHub Actions workflow to build Windows installers and update download links
- Fix FEATURES.md: restore structure and add collapsible sections properly
- Add rich output support to planned features
- Update FEATURES.md with new planned features
- Add new TODO items: settings page, playground, and insight downloads
- Add comprehensive FEATURES.md documentation

### Changed
- Update download page to specify Windows platform
- Update Pages workflow to deploy on master pushes only
- Restore original GitHub Actions workflow
- Release Windows packages v3.4.0
- Update GitHub Pages to version 3.4.0
- Make FEATURES.md consistently collapsible for all subsections
- Make FEATURES.md more readable with collapsible sections

### Fixed
- Fix workflow to trigger on release published event
- Fix Windows startup script and Python SyntaxWarning

### Removed
- Remove environment protection from Pages workflow

[3.5.0]: https://github.com/hihanifm/awebees/releases/tag/v3.5.0

## [3.4.0] - 2026-01-06

### Added
- Add Android bugreport sample file
- Add npm error handling and troubleshooting guide for Windows setup

### Changed
- Make 'Load Sample File' button more visible with gray background
- Update .gitignore with Node.js, Next.js, and temporary file patterns

### Fixed
- Document backend and frontend setup errors
- Improve PID detection in win-start.bat to prevent false startup failures

### Removed
- Remove .DS_Store file from git tracking

[3.4.0]: https://github.com/hihanifm/awebees/releases/tag/v3.4.0

## [3.3.0] - 2026-01-06

### Added
- Add config-based insights system

[3.3.0]: https://github.com/hihanifm/awebees/releases/tag/v3.3.0

## [3.2.0] - 2026-01-06

### Changed
- Enhance Windows setup with automatic Node.js and Python installation
- Update tagline: 'insight' to 'insights from messy data'

### Fixed
- Fix port numbers in README: 5000/5001 -> 34000/34001

[3.2.0]: https://github.com/hihanifm/awebees/releases/tag/v3.2.0

## [3.1.0] - 2026-01-06

### Added
- Add Windows development scripts and documentation
- Add automatic uninstall of previous version in Windows installers
- Add Windows packages for v3.0.0

[3.1.0]: https://github.com/hihanifm/awebees/releases/tag/v3.1.0

## [3.0.0] - 2026-01-06

### Added
- Add package verification script for Windows builds
- Fix frontend/out directory not being created in Windows package

### Fixed
- Fix backend logs not being written to log file

### Removed
- Delete Lens backend installation script

[3.0.0]: https://github.com/hihanifm/awebees/releases/tag/v3.0.0

## [2.7.0] - 2026-01-06

### Added
- Add GitHub Pages download page for Windows installers
- Add GitHub Pages workflow to control deployment frequency
- Add Windows packages for v2.6.0
- Add Windows production package build system
- Add logging support for Windows installation
- Add detailed debug logging to lens-start.bat

### Changed
- Update footer text for consistency with tagline
- Update Windows packages for v2.6.0
- Clean old ZIP files and extracted folders before building
- Handle file paths with surrounding quotes and whitespace
- Update lens-status.bat to use 127.0.0.1 instead of localhost
- Use 127.0.0.1 instead of localhost in launcher
- Rewrite lens-start.bat using goto labels instead of if blocks

### Fixed
- Fix download links to use GitHub raw URLs
- Fix MessageBox syntax error in NSIS script
- Fix NSIS version definition conflict
- Fix NSIS PATH issue in GitHub Actions workflow
- Fix NSIS installation in GitHub Actions workflow
- Fix GitHub Actions workflow syntax error
- Fix backend app directory not being copied to Windows package
- Fix 'no module named app' error in Windows backend startup
- Fix 'unexpected at this time' error with log file operations
- Fix log file redirection for Windows backend
- Simplify lens-start.bat to avoid path parsing issues
- Fix path handling by using relative paths after cd
- Fix if exist check for paths with parentheses
- Fix batch file syntax error for paths with parentheses
- Improve package verification error message in workflow

[2.7.0]: https://github.com/hihanifm/awebees/releases/tag/v2.7.0

## [2.6.0] - 2026-01-05

### Added
- Add screenshots and update README with Features section

### Changed
- Serve frontend from FastAPI backend in production mode

### Removed
- Remove profiling code usage from application code

[2.6.0]: https://github.com/hihanifm/awebees/releases/tag/v2.6.0

## [2.5.0] - 2026-01-05

### Added
- Add run_python.sh profiling script with regex search stats filtering
- Add explicit analyze() method to ErrorDetector for progress and cancellation support

### Changed
- Offload analyze to thread with thread-safe progress callbacks
- Reorganize insights folder: move base classes to app/core/

### Fixed
- Update error_detector.py
- Update error_detector.py
- Update ErrorDetector documentation and analyze method

### Removed
- Move run_insight.py to scripts folder and remove backend/scripts directory
- Remove logging inside line-processing loops in filter logic

[2.5.0]: https://github.com/hihanifm/awebees/releases/tag/v2.5.0

## [2.4.0] - 2026-01-04

### Added
- Add filter-based insight template and improve logging
- Add automatic venv detection and PYTHONPATH setup for standalone insight execution

### Changed
- Make insights runnable independently for unit testing

[2.4.0]: https://github.com/hihanifm/awebees/releases/tag/v2.4.0

## [2.3.0] - 2026-01-04

### Added
- Simplify crash detector and add cancellation support to read_file_chunks
- Add reusable profiling decorator and frontend profiling status indicator
- Add streamErrors method to API client
- Add missing backendErrors state and error streaming integration
- Implement SSE streaming for backend errors

### Changed
- Refactor crash_detector to use 2-step chunking approach

### Fixed
- Make error stream error handling less noisy

[2.3.0]: https://github.com/hihanifm/awebees/releases/tag/v2.3.0

## [2.2.0] - 2026-01-04

### Added
- Implement insight folders with accordion UI
- Add file reading and chunk processing progress tracking

### Changed
- Increase main container width to 90% of screen
- Change file paths textarea to 2-line height
- Bump minor version
- Match font size of 'Enter File or Folder Paths' heading with 'Select Insights'
- Show all progress events with scrollable history
- Increase progress widget event history from 5 to 10 events
- Show progress widget immediately for large file processing
- Reduce health check request frequency
- Reduce CORS OPTIONS request frequency
- Reduce progress event display frequency

[2.2.0]: https://github.com/hihanifm/awebees/releases/tag/v2.2.0

## [2.0.0] - 2026-01-04

### Added
- Add real-time progress tracking with SSE and cancellation support

[2.0.0]: https://github.com/hihanifm/awebees/releases/tag/v2.0.0

## [1.1.0] - 2026-01-04

### Added
- Optimize file processing for large files and add comprehensive logging

[1.1.0]: https://github.com/hihanifm/awebees/releases/tag/v1.1.0

## [1.0.0] - 2026-01-04

### Added
- Implement Phase 3: Core analysis feature MVP with plugin system, file handler, API routes, and frontend UI

### Changed
- Update subtitle to: A modular engine for extracting insight from data!
- Rebrand from LogBees to Lens with subtitle: A modular engine for extracting insight from data

[1.0.0]: https://github.com/hihanifm/awebees/releases/tag/v1.0.0

## [0.3.0] - 2026-01-04

### Added
- Add status bar with version, mode, and API status indicators
- Implement unified versioning system with VERSION file, version API endpoint, and version management script
- Move logs to logs/ directory, fix bash compatibility, improve error detection, and add production mode support
- Update ports to 34000/34001, add error handling to start script, and add logs.sh script
- Add environment variable configuration for ports and API URLs
- Add .cursor rules folder to repository
- Add management scripts and update ports to 5000/5001

### Changed
- Sync version in package.json with VERSION file
- Initial commit: Phase 2 - Simple working frontend and backend

[0.3.0]: https://github.com/hihanifm/awebees/releases/tag/v0.3.0
