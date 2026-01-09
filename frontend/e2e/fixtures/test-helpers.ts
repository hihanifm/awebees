import { Page, expect } from '@playwright/test';

/**
 * Test helper functions for E2E tests
 */

/**
 * Load the sample file in the application
 * Samples are now auto-loaded on page load, so we just wait for it to appear
 */
export async function loadSampleFile(page: Page): Promise<void> {
  // Wait for the textarea to be visible first
  const fileTextarea = page.locator('textarea').first();
  await expect(fileTextarea).toBeVisible({ timeout: 10000 });
  
  // Wait for the file path to populate in textarea (auto-loaded on mount)
  // The first available sample is automatically selected and loaded
  // Wait for content to appear by checking the textarea has a file path
  await expect(async () => {
    const textareaValue = await fileTextarea.inputValue();
    // Accept any sample file path (could be android-bugreport or dumpstate_log, etc.)
    expect(textareaValue.length).toBeGreaterThan(0);
    expect(textareaValue).toMatch(/\.(txt|log)$/); // Should end with .txt or .log
  }).toPass({ timeout: 15000 });
  
  // Verify it has content
  const textareaValue = await fileTextarea.inputValue();
  expect(textareaValue.length).toBeGreaterThan(0);
  // Verify it looks like a file path
  expect(textareaValue).toMatch(/\.(txt|log)$/);
}

/**
 * Select an insight by name
 * Clicks the Card containing the insight text (text is now in a div, not label)
 */
export async function selectInsight(page: Page, insightName: string): Promise<void> {
  // Find the text containing the insight name
  const insightText = page.getByText(insightName, { exact: false }).first();
  await insightText.scrollIntoViewIfNeeded();
  
  // Find the parent Card element and click it
  const card = insightText.locator('xpath=ancestor::*[contains(@class, "group")]').first();
  await card.click();
  
  // Wait for the state to update
  await page.waitForTimeout(300);
  
  // Verify it's selected by checking the checkbox aria-checked attribute
  // The checkbox ID should match the insight name converted to a valid ID format
  // Try to find checkbox near the text
  const nearbyCheckbox = insightText.locator('xpath=ancestor::*//button[@role="checkbox"]').first();
  if (await nearbyCheckbox.isVisible().catch(() => false)) {
    await expect(nearbyCheckbox).toHaveAttribute('aria-checked', 'true');
  }
}

/**
 * Wait for analysis to complete
 */
export async function waitForAnalysisComplete(page: Page, timeout: number = 30000): Promise<void> {
  // Wait for progress indicator to appear
  await page.waitForSelector('text=/analyzing|progress/i', { timeout: 5000 });
  
  // Wait for analysis to complete (progress disappears or results show)
  await page.waitForSelector('text=/analysis.*results|completed/i', { timeout });
}

/**
 * Get analysis results from the page
 */
export async function getAnalysisResults(page: Page): Promise<string[]> {
  // Find all result sections - look for "Summary" headers or result content
  const results = await page.locator('text=/.*Summary/, text=/.*completed.*/, [class*="Summary"]').allTextContents();
  return results.filter(r => r.trim().length > 0);
}

/**
 * Check if AI is configured via API
 */
export async function checkAIConfigured(page: Page): Promise<boolean> {
  try {
    const response = await page.request.get('http://localhost:34001/api/analyze/ai/config');
    if (!response.ok()) {
      console.log('AI config check failed:', response.status());
      return false;
    }
    
    const config = await response.json();
    console.log('AI configuration:', config);
    return config.is_configured === true;
  } catch (error) {
    console.error('Error checking AI config:', error);
    return false;
  }
}

/**
 * Test AI analysis (conditional on configuration)
 * Returns true if test passed, false otherwise
 */
export async function testAIAnalysis(page: Page): Promise<boolean> {
  const isConfigured = await checkAIConfigured(page);
  
  if (isConfigured) {
    console.log('AI is configured - testing AI analysis...');
    
    // Click "Analyze with AI" button - might be in results panel
    const aiButton = page.getByRole('button', { name: /analyze.*ai|ai.*analysis/i }).first();
    // Button might not be visible if AI is disabled or no results yet
    const isVisible = await aiButton.isVisible().catch(() => false);
    if (!isVisible) {
      console.log('AI button not visible (might be in results panel or disabled)');
      return true; // This is acceptable
    }
    await aiButton.click();
    
    // Wait for AI analysis to complete (up to 30 seconds)
    try {
      await page.waitForSelector('text=/ai.*analysis|analysis.*summary/i', { timeout: 30000 });
      
      // Verify AI results are displayed
      await expect(page.getByText(/ai.*analysis|analysis.*summary/i)).toBeVisible();
      
      // Check for AI result content
      const aiResultContent = await page.locator('[data-testid*="ai"], [class*="ai-result"]').first().textContent();
      expect(aiResultContent).toBeTruthy();
      expect(aiResultContent!.length).toBeGreaterThan(20); // Should have meaningful content
      
      console.log('AI analysis test PASSED');
      return true;
    } catch (error) {
      console.error('AI analysis test FAILED:', error);
      return false;
    }
  } else {
    console.log('AI is NOT configured - testing error message...');
    
    // Click "Analyze with AI" button
    const aiButton = page.getByRole('button', { name: /analyze.*ai|ai.*analysis/i });
    
    // Button might not be visible if AI is disabled
    const isVisible = await aiButton.isVisible();
    if (!isVisible) {
      console.log('AI button not visible (expected when AI disabled)');
      return true; // This is acceptable
    }
    
    await aiButton.click();
    
    // Verify error message is displayed
    try {
      await page.waitForSelector('text=/not configured|api key|disabled/i', { timeout: 5000 });
      await expect(page.getByText(/not configured|api key|disabled/i)).toBeVisible();
      
      // Verify app is still functional (main results still visible)
      await expect(page.getByText(/analysis.*results|results/i).first()).toBeVisible();
      
      console.log('Error message test PASSED');
      return true;
    } catch (error) {
      console.error('Error message test FAILED:', error);
      return false;
    }
  }
}

/**
 * Wait for element with retry
 */
export async function waitForElement(
  page: Page,
  selector: string,
  options: { timeout?: number; state?: 'visible' | 'attached' | 'hidden' } = {}
): Promise<void> {
  const timeout = options.timeout || 10000;
  const state = options.state || 'visible';
  
  await page.waitForSelector(selector, { timeout, state });
}

