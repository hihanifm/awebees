# E2E Testing Guide

This project includes end-to-end (E2E) tests using Playwright to verify the core analysis workflow.

## Quick Start

### 1. Start the Application

```bash
# From project root
./scripts/start.sh
```

This will start both backend (port 34001) and frontend (port 34000).

### 2. Run Tests

```bash
# Navigate to frontend
cd frontend

# Run tests (headless)
npm run test:e2e

# Run tests (watch browser)
npm run test:e2e:headed

# Run tests (interactive UI)
npm run test:e2e:ui

# Debug tests
npm run test:e2e:debug
```

## What Gets Tested

### Core Workflow Test
The main test verifies the complete user workflow:

1. **Load Sample File**
   - Clicks "Load Sample File" button
   - Verifies `android-bugreport.txt` is loaded

2. **Select Insights**
   - Selects "Line Count" insight
   - Selects "Error Detector" insight
   - Verifies at least 2 insights selected

3. **Run Analysis**
   - Clicks "Analyze" button
   - Waits for analysis to complete (up to 30s)
   - Verifies progress indicator

4. **Verify Results**
   - Checks results panel appears
   - Verifies both insights have results
   - Checks for execution statistics
   - Validates meaningful content

5. **AI Analysis (Conditional)**
   - **If AI is configured:**
     - Clicks "Analyze with AI"
     - Waits for AI analysis (up to 60s)
     - Verifies AI results appear
   - **If AI is NOT configured:**
     - Clicks "Analyze with AI"
     - Verifies error message shown
     - Confirms app doesn't crash

### Error Handling Test
Verifies the app handles errors gracefully without crashing.

## Test Architecture

```
frontend/
├── playwright.config.ts        # Playwright configuration
├── e2e/
│   ├── core-workflow.spec.ts  # Main test
│   ├── fixtures/
│   │   └── test-helpers.ts    # Helper functions
│   └── README.md              # Detailed docs
└── package.json               # Test scripts
```

## Configuration

**Base URL:** `http://localhost:34000`  
**API URL:** `http://localhost:34001`  
**Test Timeout:** 60 seconds  
**Expect Timeout:** 10 seconds  
**Browser:** Chromium  

See [`frontend/playwright.config.ts`](frontend/playwright.config.ts) for full configuration.

## Helper Functions

Located in [`frontend/e2e/fixtures/test-helpers.ts`](frontend/e2e/fixtures/test-helpers.ts):

- `loadSampleFile(page)` - Load the sample file
- `selectInsight(page, name)` - Select an insight by name
- `waitForAnalysisComplete(page)` - Wait for analysis to finish
- `getAnalysisResults(page)` - Extract results data
- `checkAIConfigured(page)` - Check if AI is configured via API
- `testAIAnalysis(page)` - Test AI analysis (conditional on config)

## Viewing Test Reports

After running tests:

```bash
# Open HTML report
npx playwright show-report
```

The report includes:
- Test results with pass/fail status
- Screenshots on failure
- Videos on failure
- Execution traces

## CI/CD Integration

Tests are configured for continuous integration:

- **Retries:** 2 retries on failure (CI only)
- **Workers:** Single worker on CI (no parallel)
- **Mode:** Headless by default
- **Artifacts:** Screenshots, videos, and traces on failure

Set `CI=true` environment variable to enable CI mode.

## Troubleshooting

### Tests fail immediately
**Problem:** Can't connect to application  
**Solution:**
- Ensure backend is running: `curl http://localhost:34001/health`
- Ensure frontend is running: `curl http://localhost:34000`
- Check logs in `logs/backend.log` and `logs/frontend.log`

### Tests timeout
**Problem:** Analysis takes too long  
**Solution:**
- Check backend logs for errors
- Verify sample file exists: `backend/samples/android-bugreport.txt`
- Increase timeout in `playwright.config.ts` if needed

### AI test fails
**Problem:** AI analysis fails or hangs  
**Solution:**
- Check AI config: `curl http://localhost:34001/api/analyze/ai/config`
- If AI not needed, test will verify error message instead
- If using LM Studio, ensure it's running and accessible

### Permission errors with npx
**Problem:** `EPERM` errors when running npx  
**Solution:** This is due to sandbox restrictions. The tests should still work in normal execution.

## Running Specific Tests

```bash
# Run only the core workflow test
npx playwright test core-workflow

# Run only error handling test
npx playwright test "should handle errors"

# Run with specific browser
npx playwright test --project=chromium
```

## Development Tips

1. **Use headed mode** during development: `npm run test:e2e:headed`
2. **Use debug mode** to step through: `npm run test:e2e:debug`
3. **Use UI mode** for interactive debugging: `npm run test:e2e:ui`
4. **Update snapshots** if UI changes: `npx playwright test --update-snapshots`

## Test Data

**Sample File:** `backend/samples/android-bugreport.txt`
- Size: ~57MB
- Lines: ~262,000
- Type: Android bugreport
- Automatically extracted on backend startup

## Benefits

✅ **End-to-End Validation** - Tests the entire stack together  
✅ **Real Browser** - Uses actual Chromium browser  
✅ **Reliable** - Waits for elements intelligently  
✅ **Fast** - Runs in ~30-60 seconds  
✅ **Comprehensive** - Covers main user workflow  
✅ **Conditional AI** - Adapts to AI configuration  
✅ **CI Ready** - Works in headless CI environments  
✅ **Great DevX** - Interactive UI and debug modes  

## Next Steps

To add more tests:

1. Create new `.spec.ts` files in `frontend/e2e/`
2. Import helpers from `fixtures/test-helpers.ts`
3. Follow the same pattern as `core-workflow.spec.ts`
4. Run with `npm run test:e2e`

For more information:
- [Playwright Documentation](https://playwright.dev)
- [Test Helpers](frontend/e2e/fixtures/test-helpers.ts)
- [Test Configuration](frontend/playwright.config.ts)

