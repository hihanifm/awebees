import { Page, expect } from '@playwright/test';

/**
 * Test helper functions for E2E tests
 */

/**
 * Load the sample file in the application
 */
export async function loadSampleFile(page: Page): Promise<void> {
  // Click the "Load Sample File" button
  await page.getByRole('button', { name: /load sample/i }).click();
  
  // Wait for the file path to populate in textarea
  await page.waitForSelector('textarea[value*="android-bugreport"], textarea:has-text("android-bugreport")', { timeout: 10000 });
  
  // Verify the file path is shown
  const fileTextarea = page.locator('textarea').first();
  await expect(fileTextarea).toBeVisible();
  
  // Verify it has content
  const textareaValue = await fileTextarea.inputValue();
  expect(textareaValue).toContain('android-bugreport');
}

/**
 * Select an insight by name
 * Now simplified - just click the insight card directly (no accordion)
 */
export async function selectInsight(page: Page, insightName: string): Promise<void> {
  // Find the label containing the insight name and click its parent card
  const label = page.locator(`label:has-text("${insightName}")`).first();
  await label.scrollIntoViewIfNeeded();
  
  // Click the label (which will trigger the card's onClick)
  await label.click();
  
  // Wait for the state to update
  await page.waitForTimeout(300);
  
  // Verify it's selected by checking for the selected card styling or aria-checked
  const labelFor = await label.getAttribute('for');
  if (labelFor) {
    const checkbox = page.locator(`#${labelFor}`);
    await expect(checkbox).toHaveAttribute('aria-checked', 'true');
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
  // Find all result sections
  const results = await page.locator('[data-testid*="result"], .result-section, [class*="result"]').allTextContents();
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
    
    // Click "Analyze with AI" button
    const aiButton = page.getByRole('button', { name: /analyze.*ai|ai.*analysis/i });
    await expect(aiButton).toBeVisible();
    await aiButton.click();
    
    // Wait for AI analysis to complete (up to 60 seconds)
    try {
      await page.waitForSelector('text=/ai.*analysis|analysis.*summary/i', { timeout: 60000 });
      
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

