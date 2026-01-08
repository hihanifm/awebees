# Logging Configuration Feature

## Overview

Added user-configurable logging settings accessible through the Settings dialog, allowing control of log levels for both backend (Python) and frontend (JavaScript) even in production environments.

## Features

### Backend Logging
- **Dynamic log level control** via API endpoints
- **Persistence** to `.env` file for permanent configuration
- **Supported levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Smart defaults**: DEBUG in development, INFO in production
- **No restart required** - changes take effect immediately

### Frontend Logging
- **Centralized logger utility** with level filtering
- **Persistence** to localStorage
- **Supported levels**: DEBUG, INFO, WARN, ERROR, NONE
- **Smart defaults**: DEBUG in development, INFO in production
- **Automatic filtering** - console output respects configured level

### Settings UI
- New **"Logging" tab** in Settings dialog
- Separate controls for backend and frontend
- Real-time updates with toast notifications
- Visual indicators showing current log levels
- Helpful descriptions for each log level

## Implementation Details

### Backend Changes

1. **`backend/app/core/config.py`**
   - Added `AppConfig.update_log_level()` method
   - Added `AppConfig.get_log_level()` method
   - Added `_persist_to_env()` for saving to `.env` file
   - Dynamic root logger level updates

2. **`backend/app/api/routes/logging.py`** (NEW)
   - `GET /api/logging/config` - Get current backend log level
   - `PUT /api/logging/config` - Update backend log level
   - Validation and error handling

3. **`backend/app/main.py`**
   - Updated to use `AppConfig.LOG_LEVEL` instead of hardcoded `logging.INFO`
   - Registered logging router

### Frontend Changes

1. **`frontend/lib/logger.ts`** (NEW)
   - Centralized `Logger` class with level filtering
   - Methods: `debug()`, `info()`, `warn()`, `error()`
   - Singleton instance exported as `logger`

2. **`frontend/lib/logging-storage.ts`** (NEW)
   - `loadLogLevel()` - Read from localStorage
   - `saveLogLevel()` - Save to localStorage
   - Default: INFO in production, DEBUG in development

3. **`frontend/lib/api-client.ts`**
   - Added `getLoggingConfig()` method
   - Added `updateLoggingConfig()` method
   - Replaced console calls with logger

4. **`frontend/components/settings/SettingsDialog.tsx`**
   - Added "Logging" tab with backend and frontend controls
   - State management for both log levels
   - Handlers for updating log levels
   - Replaced console calls with logger

5. **`frontend/app/page.tsx`**
   - Replaced console calls with logger

## Usage

### For Users

1. Open Settings dialog (gear icon in status bar)
2. Navigate to "Logging" tab
3. Select desired log level for backend and/or frontend
4. Changes take effect immediately

### For Developers

**Frontend:**
```typescript
import { logger } from "@/lib/logger";

logger.debug("Detailed diagnostic info");
logger.info("General information");
logger.warn("Warning message");
logger.error("Error occurred", error);
```

**Backend:**
```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed diagnostic info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)
```

## Log Level Reference

### Backend (Python)
- **DEBUG** - Detailed diagnostic information (default in development)
- **INFO** - General informational messages (default in production)
- **WARNING** - Warning messages only
- **ERROR** - Error messages only
- **CRITICAL** - Critical errors only

### Frontend (JavaScript)
- **DEBUG** - All console output (default in development)
- **INFO** - Info, warnings, and errors (default in production)
- **WARN** - Warnings and errors only
- **ERROR** - Errors only
- **NONE** - No console output

## Benefits

✅ **Debug in production** without redeployment  
✅ **Reduce noise** by filtering unnecessary logs  
✅ **Persistent settings** across sessions  
✅ **No restart required** for changes  
✅ **User-friendly UI** with clear descriptions  
✅ **Standard logging practices** - no reinventing the wheel

## Files Modified

### Backend
- `backend/app/core/config.py`
- `backend/app/main.py`
- `backend/app/api/routes/logging.py` (NEW)

### Frontend
- `frontend/lib/logger.ts` (NEW)
- `frontend/lib/logging-storage.ts` (NEW)
- `frontend/lib/api-client.ts`
- `frontend/components/settings/SettingsDialog.tsx`
- `frontend/app/page.tsx`

## Environment Detection

The backend detects the environment using the `ENVIRONMENT` environment variable:
- **Development mode**: `ENVIRONMENT=development` or `ENVIRONMENT=dev` (or not set) → defaults to DEBUG
- **Production mode**: `ENVIRONMENT=production` or `ENVIRONMENT=prod` → defaults to INFO

To explicitly set production mode, add to your `.env` file:
```bash
ENVIRONMENT=production
```

## Testing

To test the feature:

1. Start the application (defaults to DEBUG in dev)
2. Open Settings → Logging tab
3. Verify current log levels are shown
4. Change backend log level to INFO
5. Check backend terminal for reduced verbosity
6. Change frontend log level to ERROR
7. Check browser console - only errors should appear
8. Restart application - settings should persist

