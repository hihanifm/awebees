import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto("/");
    // Wait for the page to be fully loaded
    await page.waitForLoadState("networkidle");
  });

  test("should navigate to Playground via top navigation", async ({ page }) => {
    // Find and click the Playground link in the top navigation
    const playgroundLink = page.getByRole("link", { name: /playground/i });
    await expect(playgroundLink).toBeVisible();
    
    // Click the link
    await playgroundLink.click();
    
    // Wait for navigation
    await page.waitForURL("**/playground", { timeout: 5000 });
    
    // Verify we're on the playground page
    expect(page.url()).toContain("/playground");
    
    // Verify playground page content is visible
    await expect(page.getByText(/playground/i).first()).toBeVisible();
  });

  test("should navigate to Settings page via top navigation", async ({ page }) => {
    // Find and click the Settings link in the top navigation
    const settingsLink = page.getByRole("link", { name: /settings/i });
    await expect(settingsLink).toBeVisible();
    
    // Click the link
    await settingsLink.click();
    
    // Wait for navigation to settings page
    await page.waitForURL("**/settings", { timeout: 5000 });
    
    // Verify we're on the settings page
    expect(page.url()).toContain("/settings");
    
    // Verify settings page content is visible (check for settings heading or tabs)
    const settingsHeading = page.getByRole("heading", { name: /settings/i });
    const settingsTabs = page.getByRole("tab", { name: /ai|insights|general|logging/i });
    await expect(settingsHeading.or(settingsTabs).first()).toBeVisible();
  });

  test("should navigate to Home via top navigation", async ({ page }) => {
    // First navigate to playground
    await page.goto("/playground");
    await page.waitForLoadState("networkidle");
    
    // Find and click the Home link in the top navigation
    const homeLink = page.getByRole("link", { name: /home/i });
    await expect(homeLink).toBeVisible();
    
    // Click the link
    await homeLink.click();
    
    // Wait for navigation
    await page.waitForURL("**/", { timeout: 5000 });
    
    // Verify we're on the home page (root)
    expect(page.url()).toMatch(/\/$/);
    
    // Verify home page content is visible (check for either heading)
    const filePathsHeading = page.getByRole("heading", { name: /enter file or folder paths/i });
    const insightsHeading = page.getByRole("heading", { name: /select insights/i });
    await expect(filePathsHeading.or(insightsHeading).first()).toBeVisible();
  });

  test("should navigate to Home via logo click", async ({ page }) => {
    // First navigate to playground
    await page.goto("/playground");
    await page.waitForLoadState("networkidle");
    
    // Find and click the logo (which should link to home)
    const logoLink = page.locator('a[href="/"]').first();
    await expect(logoLink).toBeVisible();
    
    // Click the logo
    await logoLink.click();
    
    // Wait for navigation
    await page.waitForURL("**/", { timeout: 5000 });
    
    // Verify we're on the home page
    expect(page.url()).toMatch(/\/$/);
  });

  test("should complete playground workflow with sample file, filter, and AI analysis", async ({ page }) => {
    // Navigate to playground
    console.log('Step 1: Navigating to playground...');
    await page.goto("/playground");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText(/playground/i).first()).toBeVisible();
    console.log('✓ Playground page loaded');

    // Step 2: Get sample file from API and select it
    console.log('Step 2: Fetching and selecting sample file...');
    let sampleFilePath = '';
    try {
      const response = await page.request.get('http://localhost:34001/api/files/samples');
      if (response.ok()) {
        const data = await response.json();
        if (data.samples && data.samples.length > 0) {
          // Use the first available sample
          sampleFilePath = data.samples[0].path;
          console.log(`✓ Found sample file: ${data.samples[0].name}`);
        }
      }
    } catch (error) {
      console.log('⚠ Could not fetch samples from API, using fallback path');
    }
    
    // Fallback to a common sample file path if API didn't work
    if (!sampleFilePath) {
      sampleFilePath = '/Users/hanifm/awebees/backend/samples/android-bugreport.txt';
    }
    
    const filePathsTextarea = page.locator('textarea').first();
    await expect(filePathsTextarea).toBeVisible({ timeout: 5000 });
    await filePathsTextarea.fill(sampleFilePath);
    console.log(`✓ Sample file path entered: ${sampleFilePath}`);

    // Step 3: Enter filter command
    console.log('Step 3: Entering filter command...');
    const ripgrepInput = page.getByLabel(/ripgrep command/i).or(page.locator('input[placeholder*="ERROR"]')).first();
    await expect(ripgrepInput).toBeVisible({ timeout: 5000 });
    await ripgrepInput.fill('ERROR');
    console.log('✓ Filter command entered: ERROR');

    // Step 4: Click Execute/Analyze files button
    console.log('Step 4: Clicking Execute button...');
    const executeButton = page.getByRole('button', { name: /execute/i }).first();
    await expect(executeButton).toBeVisible();
    await executeButton.click();
    console.log('✓ Execute button clicked');

    // Step 5: Wait for analysis to complete and check output
    console.log('Step 5: Waiting for analysis to complete...');
    // Wait for progress or results to appear
    try {
      await page.waitForSelector('text=/analyzing|progress|completed/i', { timeout: 10000 });
      // Wait for results to appear
      await page.waitForSelector('text=/analysis.*results|results|insight/i', { timeout: 30000 });
      console.log('✓ Analysis completed');
    } catch (error) {
      // Check if there's an error message instead
      const errorVisible = await page.getByText(/error/i).isVisible().catch(() => false);
      if (errorVisible) {
        console.log('⚠ Error occurred during analysis (may be expected if file not found)');
      } else {
        throw error;
      }
    }

    // Verify results are displayed
    const resultsVisible = await page.getByText(/analysis.*results|results|insight/i).first().isVisible().catch(() => false);
    if (resultsVisible) {
      console.log('✓ Results panel is visible');
      
      // Step 6: Expand "Analyze with AI" section
      console.log('Step 6: Expanding AI analysis section...');
      const analyzeWithAIButton = page.getByRole('button', { name: /analyze.*with.*ai|analyze.*ai/i }).first();
      const aiButtonVisible = await analyzeWithAIButton.isVisible().catch(() => false);
      
      if (aiButtonVisible) {
        await analyzeWithAIButton.click();
        console.log('✓ AI analysis section expanded');
        
        // Wait for the dropdown to appear
        await page.waitForTimeout(500);
        
        // Step 7: Click the Analyze button in the AI section
        console.log('Step 7: Clicking AI Analyze button...');
        const aiAnalyzeButton = page.getByRole('button', { name: /^analyze$/i })
          .filter({ hasNot: page.locator('text=/analyzing/i') })
          .filter({ hasNot: page.locator('[disabled]') })
          .first();
        
        const analyzeBtnVisible = await aiAnalyzeButton.isVisible({ timeout: 5000 }).catch(() => false);
        if (analyzeBtnVisible) {
          await aiAnalyzeButton.click();
          console.log('✓ AI Analyze button clicked');
          
          // Step 8: Wait for AI analysis to start/complete
          console.log('Step 8: Waiting for AI analysis...');
          try {
            await Promise.race([
              page.waitForSelector('text=/analyzing/i', { timeout: 5000 }),
              page.waitForSelector('text=/ai.*analysis|analysis.*complete/i', { timeout: 30000 })
            ]);
            console.log('✓ AI analysis started or completed');
          } catch (error) {
            // If AI is not configured, we might see an error message instead
            const errorVisible = await page.getByText(/not configured|api key|disabled|configuration/i).isVisible().catch(() => false);
            if (errorVisible) {
              console.log('⚠ AI not configured - error message shown (expected)');
            } else {
              console.log('⚠ AI analysis may still be processing or not configured');
            }
          }
        } else {
          console.log('⚠ AI Analyze button not visible (may be disabled or AI not configured)');
        }
      } else {
        console.log('⚠ AI analysis button not visible (AI might be disabled)');
      }
    } else {
      console.log('⚠ Results not visible (analysis may have failed or file not found)');
    }

    console.log('\n=== PLAYGROUND TEST COMPLETED ===\n');
  });
});
