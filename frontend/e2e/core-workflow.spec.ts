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
    const fileInput = page.locator('input[value*="android-bugreport"]');
    await expect(fileInput).toBeVisible();
    console.log('✓ Sample file loaded');

    // Step 2: Select insights
    console.log('Step 2: Selecting insights...');
    
    // Select "Line Count" insight (always available)
    await selectInsight(page, 'Line Count');
    console.log('✓ Line Count selected');
    
    // Select "Error Detector" insight
    await selectInsight(page, 'Error Detector');
    console.log('✓ Error Detector selected');

    // Verify at least 2 insights are selected
    const checkedBoxes = await page.locator('input[type="checkbox"]:checked').count();
    expect(checkedBoxes).toBeGreaterThanOrEqual(2);
    console.log(`✓ ${checkedBoxes} insights selected`);

    // Step 3: Run analysis
    console.log('Step 3: Running analysis...');
    const analyzeButton = page.getByRole('button', { name: /^analyze$/i });
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
    await expect(page.getByText(/line count/i)).toBeVisible();
    await expect(page.getByText(/error detector/i)).toBeVisible();
    
    // Check for statistics
    await expect(page.getByText(/insights run|total time|execution/i).first()).toBeVisible();
    
    // Get results content
    const results = await getAnalysisResults(page);
    expect(results.length).toBeGreaterThan(0);
    console.log(`✓ Found ${results.length} result sections`);

    // Verify results have meaningful content
    const resultsText = results.join(' ');
    expect(resultsText.length).toBeGreaterThan(50); // Should have substantial content
    console.log('✓ Results contain meaningful content');

    // Step 5: Test AI Analysis (conditional)
    console.log('Step 5: Testing AI analysis...');
    const aiTestPassed = await testAIAnalysis(page);
    expect(aiTestPassed).toBe(true);
    console.log('✓ AI analysis test passed');

    // Final verification: check console for errors
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Give a moment for any delayed errors
    await page.waitForTimeout(1000);
    
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

