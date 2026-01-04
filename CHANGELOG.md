# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-XX

### Added
- Initial project setup with Next.js frontend and FastAPI backend
- Environment-based configuration for ports and URLs
- Development and production mode support
- Scripts for setup, start, stop, status, and log viewing
- Version management system with unified VERSION file
- API version endpoint (`/api/version`)
- Health check endpoint (`/health`)
- CORS middleware configuration
- Logging infrastructure with logs stored in `logs/` directory
- Python virtual environment setup
- Node.js dependency management
- Git repository with initial commit

### Configuration
- Frontend port: 34000 (configurable via `PORT` environment variable)
- Backend port: 34001 (configurable via `PORT` environment variable)
- Logs directory: `logs/` at project root

[0.1.0]: https://github.com/hihanifm/awebees/releases/tag/v0.1.0

