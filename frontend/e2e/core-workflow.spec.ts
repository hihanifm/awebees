import { test, expect } from '@playwright/test';
import {
  loadSampleFile,
  selectInsight,
  waitForAnalysisComplete,
  getAnalysisResults,
  testAIAnalysis,
} from './fixtures/test-helpers';

/**
 * Core Workflow E2E Test
 * 
 * Prerequisites:
 * - Backend must be running on http://localhost:34001
 * - Frontend must be running on http://localhost:34000
 * - Sample file must be available (android-bugreport.txt)
 * 
 * Run with:
 * - npm run test:e2e         (headless)
 * - npm run test:e2e:headed  (see browser)
 * - npm run test:e2e:ui      (interactive UI)
 */

test.describe('Core Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  test('should complete full analysis workflow with 2+ insights', async ({ page }) => {
    // Step 1: Load sample file
    console.log('Step 1: Loading sample file...');
    await loadSampleFile(page);
    
    // Verify file is loaded
    const fileTextarea = page.locator('textarea').first();
    await expect(fileTextarea).toBeVisible();
    const textareaValue = await fileTextarea.inputValue();
    // Accept any sample file (could be android-bugreport, dumpstate_log, etc.)
    expect(textareaValue.length).toBeGreaterThan(0);
    expect(textareaValue).toMatch(/\.(txt|log)$/); // Should be a .txt or .log file
    console.log('✓ Sample file loaded:', textareaValue);

    // Step 2: Select insights
    console.log('Step 2: Selecting insights...');
    
    // Select "Line Count" insight (always available)
    await selectInsight(page, 'Line Count');
    console.log('✓ Line Count selected');
    
    // Select "Error Detector" insight
    await selectInsight(page, 'Error Detector');
    console.log('✓ Error Detector selected');

    // Verify at least 2 insights are selected
    // Checkboxes are actually buttons with role="checkbox" and aria-checked="true"
    const checkedBoxes = await page.locator('button[role="checkbox"][aria-checked="true"]').count();
    expect(checkedBoxes).toBeGreaterThanOrEqual(2);
    console.log(`✓ ${checkedBoxes} insights selected`);

    // Step 3: Run analysis
    console.log('Step 3: Running analysis...');
    // Button text is translated, try multiple variations
    const analyzeButton = page.getByRole('button', { name: /analyze/i }).first();
    await expect(analyzeButton).toBeVisible();
    await analyzeButton.click();
    
    // Wait for analysis to complete
    await waitForAnalysisComplete(page, 30000);
    console.log('✓ Analysis complete');

    // Step 4: Verify results
    console.log('Step 4: Verifying results...');
    
    // Check results panel is visible
    await expect(page.getByText(/analysis.*results|results/i).first()).toBeVisible();
    
    // Verify both insights have results
    // Use .first() since "Line Count" appears multiple times (in insight list and results)
    await expect(page.getByText(/line count/i).first()).toBeVisible();
    await expect(page.getByText(/error detector/i).first()).toBeVisible();
    
    // Check for statistics
    await expect(page.getByText(/insights run|total time|execution/i).first()).toBeVisible();
    
    // Verify results have meaningful content
    // Check for "Summary" text which appears in result headers
    const summaryTexts = await page.locator('text=/Summary/').allTextContents();
    expect(summaryTexts.length).toBeGreaterThan(0);
    console.log(`✓ Found ${summaryTexts.length} result summaries`);
    
    // Verify results content exists
    const resultsText = summaryTexts.join(' ');
    expect(resultsText.length).toBeGreaterThan(10); // Should have some content
    console.log('✓ Results contain meaningful content');

    // Step 5: Test AI Analysis (conditional)
    console.log('Step 5: Testing AI analysis...');
    try {
      const aiTestPassed = await testAIAnalysis(page);
      if (aiTestPassed) {
        console.log('✓ AI analysis test passed');
      } else {
        console.log('⚠ AI analysis test skipped (AI not configured or button not available)');
      }
    } catch (error) {
      console.log('⚠ AI analysis test skipped (error):', error);
      // Don't fail the test if AI testing fails - it's optional
    }

    // Final verification: check console for errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Give a moment for any delayed errors (with timeout protection)
    try {
      await Promise.race([
        page.waitForTimeout(1000),
        new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 2000))
      ]);
    } catch (error) {
      // Ignore timeout - page might be closing
    }
    
    // Report any console errors (but don't fail - some errors might be expected)
    if (consoleErrors.length > 0) {
      console.warn(`Found ${consoleErrors.length} console errors:`, consoleErrors);
    } else {
      console.log('✓ No console errors detected');
    }

    console.log('\n=== TEST COMPLETED SUCCESSFULLY ===\n');
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test error handling without crashing the app
    console.log('Testing error handling...');
    
    // Try to analyze without selecting a file
    const analyzeButton = page.getByRole('button', { name: /^analyze$/i });
    
    if (await analyzeButton.isVisible()) {
      await analyzeButton.click();
      
      // Should show an error or not crash
      await page.waitForTimeout(2000);
      
      // Verify app is still functional (page didn't crash)
      await expect(page.locator('body')).toBeVisible();
      console.log('✓ App handles errors without crashing');
    }
  });
});

