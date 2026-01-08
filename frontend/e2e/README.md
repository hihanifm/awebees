# E2E Tests

End-to-end tests for the Lens application using Playwright.

## Prerequisites

Before running tests, ensure:

1. **Backend is running** on `http://localhost:34001`
2. **Frontend is running** on `http://localhost:34000`
3. **Sample file is available** (`backend/samples/android-bugreport.txt`)

Start the application:
```bash
# From project root
./scripts/start.sh
```

## Running Tests

### Headless Mode (CI)
```bash
cd frontend
npm run test:e2e
```

### Headed Mode (Watch Browser)
```bash
cd frontend
npm run test:e2e:headed
```

### Interactive UI Mode
```bash
cd frontend
npm run test:e2e:ui
```

### Debug Mode
```bash
cd frontend
npm run test:e2e:debug
```

## What Gets Tested

### Core Workflow Test
1. ✅ Load sample file
2. ✅ Select 2+ insights (Line Count, Error Detector)
3. ✅ Run analysis
4. ✅ Verify results appear with content
5. ✅ Test AI analysis (conditional):
   - If AI configured: Verify AI analysis works
   - If AI not configured: Verify error message shown

### Error Handling Test
- ✅ App doesn't crash on errors
- ✅ Graceful error messages

## Test Structure

```
e2e/
├── core-workflow.spec.ts     # Main test file
├── fixtures/
│   └── test-helpers.ts        # Reusable helper functions
└── README.md                  # This file
```

## Helper Functions

Located in `fixtures/test-helpers.ts`:

- `loadSampleFile(page)` - Load the sample file
- `selectInsight(page, name)` - Select an insight by name
- `waitForAnalysisComplete(page)` - Wait for analysis to finish
- `getAnalysisResults(page)` - Extract results data
- `checkAIConfigured(page)` - Check if AI is configured
- `testAIAnalysis(page)` - Test AI analysis (conditional)

## Configuration

See `playwright.config.ts` for:
- Base URL
- Timeouts
- Browser settings
- Reporter options

## Troubleshooting

### Test fails immediately
- Ensure backend and frontend are running
- Check ports: `34001` (backend), `34000` (frontend)

### Test times out
- Check backend logs: `logs/backend.log`
- Check frontend logs: `logs/frontend.log`
- Sample file might be too large (adjust timeout in config)

### AI test fails
- Check AI configuration: `GET http://localhost:34001/api/analyze/ai/config`
- If AI not needed, test will verify error message instead

## Viewing Results

After test run:
```bash
# Open HTML report
npx playwright show-report
```

Reports include:
- Test results
- Screenshots on failure
- Videos on failure
- Traces on retry

## CI Integration

Tests are configured for CI with:
- Retry on failure (2 retries)
- Single worker (no parallel)
- Headless mode
- Full traces on failure

Set `CI=true` environment variable for CI mode.

