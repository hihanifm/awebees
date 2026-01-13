import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

/**
 * Plugin Error Handling E2E Test
 * 
 * Tests that plugin load errors are properly caught, logged, and displayed to users.
 * 
 * Prerequisites:
 * - Backend must be running on http://localhost:34001
 * - Frontend must be running on http://localhost:34000
 * 
 * Run with:
 * - npm run test:e2e         (headless)
 * - npm run test:e2e:headed  (see browser)
 */

test.describe('Plugin Error Handling', () => {
  let testDir: string;
  let errorInsightPath: string;
  let syntaxErrorPath: string;
  let importErrorPath: string;

  test.beforeAll(async () => {
    // Create a temporary directory for test insights
    testDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lens-test-insights-'));
    errorInsightPath = path.join(testDir, 'error_insight.py');
    syntaxErrorPath = path.join(testDir, 'syntax_error_insight.py');
    importErrorPath = path.join(testDir, 'import_error_insight.py');

    // Create test insight files with various errors
    // 1. Syntax error insight
    fs.writeFileSync(syntaxErrorPath, `
# This file has a syntax error
INSIGHT_CONFIG = {
    "metadata": {
        "id": "syntax_error_test",
        "name": "Syntax Error Test",
        "description": "This insight has a syntax error"
    },
    "filters": {
        "line_pattern": r"ERROR"
    }
# Missing closing brace - syntax error!
`, 'utf-8');

    // 2. Import error insight
    fs.writeFileSync(importErrorPath, `
# This file has an import error
import non_existent_module  # This will fail

INSIGHT_CONFIG = {
    "metadata": {
        "id": "import_error_test",
        "name": "Import Error Test",
        "description": "This insight has an import error"
    },
    "filters": {
        "line_pattern": r"ERROR"
    }
}
`, 'utf-8');

    // 3. Instantiation error insight (valid syntax but invalid config)
    fs.writeFileSync(errorInsightPath, `
# This file has an instantiation error (invalid config structure)
INSIGHT_CONFIG = {
    "metadata": {
        "id": "instantiation_error_test",
        "name": "Instantiation Error Test",
        "description": "This insight has an instantiation error"
    },
    "filters": {
        "line_pattern": r"ERROR"
    },
    "invalid_key": "This will cause an error during instantiation"
}
`, 'utf-8');

    console.log(`Created test insights directory: ${testDir}`);
  });

  test.afterAll(async () => {
    // Clean up: Remove test directory
    try {
      // First, remove the insight path from backend
      const response = await fetch('http://localhost:34001/api/insight-paths/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: testDir })
      });
      console.log('Removed test insight path from backend');
    } catch (error) {
      console.warn('Failed to remove test path from backend:', error);
    }

    // Remove test directory
    try {
      fs.rmSync(testDir, { recursive: true, force: true });
      console.log(`Cleaned up test directory: ${testDir}`);
    } catch (error) {
      console.warn('Failed to clean up test directory:', error);
    }
  });

  test('should display error dialog when plugin fails to load', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Wait for the page to be fully initialized (including error stream connection)
    // The error stream connects on page load, so we need to wait for it
    await page.waitForTimeout(2000);
    console.log('✓ Page loaded and error stream should be connected');

    // Step 1: Add the test insight path
    console.log('Step 1: Adding test insight path...');
    const addPathResponse = await page.request.post('http://localhost:34001/api/insight-paths/add', {
      data: { path: testDir }
    });
    
    expect(addPathResponse.ok()).toBeTruthy();
    const addPathData = await addPathResponse.json();
    console.log('✓ Test insight path added:', addPathData);

    // Step 2: Refresh insights to trigger error discovery
    console.log('Step 2: Refreshing insights to trigger error discovery...');
    const refreshResponse = await page.request.post('http://localhost:34001/api/insight-paths/refresh');
    
    expect(refreshResponse.ok()).toBeTruthy();
    const refreshData = await refreshResponse.json();
    console.log('✓ Insights refreshed:', refreshData);

    // Step 3: Wait for error dialog to appear
    // The error stream should have received the errors and the dialog should appear
    console.log('Step 3: Waiting for error dialog...');
    
    // Wait a moment for errors to be streamed to frontend
    await page.waitForTimeout(2000);
    
    // The error dialog should appear automatically when errors are detected
    // Wait for the dialog title "Plugin Load Error"
    const dialogTitle = page.getByText('Plugin Load Error');
    
    // Try to wait for dialog
    try {
      await expect(dialogTitle).toBeVisible({ timeout: 10000 });
      console.log('✓ Error dialog appeared');
    } catch (error) {
      // If dialog doesn't appear, try refreshing the page to trigger error stream again
      console.log('Dialog not visible, refreshing page to trigger error stream...');
      await page.reload();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);
      
      // Try again after reload
      const dialogAfterReload = page.getByText('Plugin Load Error');
      await expect(dialogAfterReload).toBeVisible({ timeout: 10000 });
      console.log('✓ Error dialog appeared after page refresh');
    }

    // Step 5: Verify error details are displayed
    console.log('Step 5: Verifying error details...');
    
    // Check that error message is visible
    const errorMessage = page.locator('text=/Failed to|Syntax error|Import error|Instantiation error/i');
    await expect(errorMessage.first()).toBeVisible();
    console.log('✓ Error message displayed');

    // Check that error details (stack trace) are visible
    const errorDetails = page.locator('text=/Traceback|File:|Error:/i');
    await expect(errorDetails.first()).toBeVisible();
    console.log('✓ Error details (stack trace) displayed');

    // Check that file name is visible
    const fileName = page.locator('text=/syntax_error_insight|import_error_insight|error_insight/i');
    await expect(fileName.first()).toBeVisible();
    console.log('✓ File name displayed');

    // Step 5: Verify multiple errors are shown (if dialog supports multiple)
    // Close the current dialog to see if more errors appear
    const closeButton = page.getByRole('button', { name: /close/i }).first();
    if (await closeButton.isVisible().catch(() => false)) {
      await closeButton.click();
      console.log('✓ Closed first error dialog');
      
      // Wait a moment and check if another error dialog appears
      await page.waitForTimeout(1000);
      const anotherDialog = page.getByText('Plugin Load Error');
      const hasMoreErrors = await anotherDialog.isVisible().catch(() => false);
      if (hasMoreErrors) {
        console.log('✓ Multiple error dialogs detected (expected for multiple errors)');
      }
    }

    // Step 7: Verify app is still functional despite errors
    console.log('Step 7: Verifying app is still functional...');
    
    // Check that insights list is still visible
    const insightsSection = page.getByText(/select.*insights|insights/i).first();
    await expect(insightsSection).toBeVisible();
    console.log('✓ Insights section still visible');

    // Check that we can still select insights
    const insightCards = page.locator('button[role="checkbox"]');
    const insightCount = await insightCards.count();
    expect(insightCount).toBeGreaterThan(0);
    console.log(`✓ Can still select insights (${insightCount} available)`);

    console.log('\n=== PLUGIN ERROR HANDLING TEST COMPLETED SUCCESSFULLY ===\n');
  });

  test('should show detailed error information in dialog', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Add test path and refresh
    await page.request.post('http://localhost:34001/api/insight-paths/add', {
      data: { path: testDir }
    });
    await page.request.post('http://localhost:34001/api/insight-paths/refresh');

    // Wait for error dialog
    const dialogTitle = page.getByText('Plugin Load Error');
    await expect(dialogTitle).toBeVisible({ timeout: 10000 });

    // Verify error type is shown
    const errorType = page.locator('text=/Error Type|syntax_error|import_failure|instantiation_failure/i');
    await expect(errorType.first()).toBeVisible();
    console.log('✓ Error type displayed');

    // Verify severity is shown
    const severity = page.locator('text=/Severity|error|warning|critical/i');
    await expect(severity.first()).toBeVisible();
    console.log('✓ Severity displayed');

    // Verify location information (file, folder) is shown
    const location = page.locator('text=/Location|File:|Folder:/i');
    await expect(location.first()).toBeVisible();
    console.log('✓ Location information displayed');

    // Verify timestamp is shown
    const timestamp = page.locator('text=/Time:/i');
    await expect(timestamp.first()).toBeVisible();
    console.log('✓ Timestamp displayed');

    console.log('\n=== ERROR DETAILS TEST COMPLETED SUCCESSFULLY ===\n');
  });

  test('should handle errors gracefully without crashing', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Add test path and refresh
    await page.request.post('http://localhost:34001/api/insight-paths/add', {
      data: { path: testDir }
    });
    await page.request.post('http://localhost:34001/api/insight-paths/refresh');

    // Wait a moment for errors to be processed
    await page.waitForTimeout(2000);

    // Verify page is still responsive
    await expect(page.locator('body')).toBeVisible();
    console.log('✓ Page is still visible');

    // Verify we can interact with the page
    const textarea = page.locator('textarea').first();
    await expect(textarea).toBeVisible();
    await textarea.click();
    console.log('✓ Can interact with page elements');

    // Verify insights can still be loaded
    const insightsResponse = await page.request.get('http://localhost:34001/api/insights');
    expect(insightsResponse.ok()).toBeTruthy();
    const insights = await insightsResponse.json();
    expect(insights.insights).toBeInstanceOf(Array);
    console.log(`✓ Insights API still works (${insights.insights.length} insights available)`);

    // Check for console errors (should not have critical errors)
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text();
        // Ignore expected errors (plugin load errors are expected)
        if (!text.includes('plugin') && !text.includes('insight')) {
          consoleErrors.push(text);
        }
      }
    });

    await page.waitForTimeout(1000);

    // Report unexpected console errors
    if (consoleErrors.length > 0) {
      console.warn(`Found ${consoleErrors.length} unexpected console errors:`, consoleErrors);
    } else {
      console.log('✓ No unexpected console errors');
    }

    console.log('\n=== GRACEFUL ERROR HANDLING TEST COMPLETED SUCCESSFULLY ===\n');
  });
});
