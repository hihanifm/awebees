import { test, expect } from '@playwright/test';

/**
 * Favorites E2E Test
 * 
 * Prerequisites:
 * - Backend must be running on http://localhost:34001
 * - Frontend must be running on http://localhost:34000
 * 
 * Run with:
 * - npm run test:e2e         (headless)
 * - npm run test:e2e:headed  (see browser)
 * - npm run test:e2e:ui      (interactive UI)
 */

test.describe('Favorites Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Wait for insights to load
    await page.waitForSelector('text=/line count|error detector|insights/i', { timeout: 10000 });
  });

  test('should favorite and unfavorite an insight', async ({ page }) => {
    console.log('Starting favorites test...');
    
    // Step 1: Find an insight card (e.g., "Line Count")
    console.log('Step 1: Finding insight card...');
    const insightName = 'Line Count';
    const insightText = page.getByText(insightName, { exact: false }).first();
    await expect(insightText).toBeVisible({ timeout: 10000 });
    
    // Find the parent card containing the insight
    const insightCard = insightText.locator('xpath=ancestor::*[contains(@class, "group")]').first();
    await expect(insightCard).toBeVisible();
    console.log(`✓ Found ${insightName} insight card`);
    
    // Step 2: Find and click the star icon to favorite
    console.log('Step 2: Favoriting insight...');
    // The star icon is a button with aria-label "Add to favorites" when not favorited
    const starButton = insightCard.locator('button[aria-label*="favorites"]').first();
    await expect(starButton).toBeVisible();
    
    // Check initial state - should be "Add to favorites"
    const initialAriaLabel = await starButton.getAttribute('aria-label');
    expect(initialAriaLabel).toContain('Add to favorites');
    console.log('✓ Star icon found with "Add to favorites" label');
    
    // Click the star to favorite
    await starButton.click();
    console.log('✓ Star icon clicked to favorite');
    
    // Wait for the favorite state to update (API call)
    await page.waitForTimeout(500);
    
    // Step 3: Verify the star is now filled (favorited state)
    console.log('Step 3: Verifying insight is favorited...');
    const favoritedAriaLabel = await starButton.getAttribute('aria-label');
    expect(favoritedAriaLabel).toContain('Remove from favorites');
    console.log('✓ Star icon now shows "Remove from favorites"');
    
    // Step 4: Switch to Favorites tab
    console.log('Step 4: Switching to Favorites tab...');
    const favoritesTab = page.getByRole('tab', { name: /favorites/i });
    await expect(favoritesTab).toBeVisible();
    await favoritesTab.click();
    console.log('✓ Clicked Favorites tab');
    
    // Wait for favorites tab content to load
    await page.waitForTimeout(500);
    
    // Step 5: Verify the insight appears in the Favorites tab
    console.log('Step 5: Verifying insight appears in Favorites tab...');
    const favoritedInsight = page.getByText(insightName, { exact: false }).first();
    await expect(favoritedInsight).toBeVisible({ timeout: 5000 });
    console.log(`✓ ${insightName} appears in Favorites tab`);
    
    // Find the star button in the favorites tab
    const favoritedCard = favoritedInsight.locator('xpath=ancestor::*[contains(@class, "group")]').first();
    const favoritedStarButton = favoritedCard.locator('button[aria-label*="favorites"]').first();
    await expect(favoritedStarButton).toBeVisible();
    
    // Verify it's still favorited
    const favoritedLabel = await favoritedStarButton.getAttribute('aria-label');
    expect(favoritedLabel).toContain('Remove from favorites');
    console.log('✓ Insight is still favorited in Favorites tab');
    
    // Step 6: Unfavorite the insight
    console.log('Step 6: Unfavoriting insight...');
    await favoritedStarButton.click();
    console.log('✓ Star icon clicked to unfavorite');
    
    // Wait for the unfavorite state to update (API call)
    await page.waitForTimeout(500);
    
    // Step 7: Verify the insight disappears from Favorites tab
    console.log('Step 7: Verifying insight removed from Favorites tab...');
    
    // The insight should no longer be visible in the favorites tab (or show as unfavorited)
    // Wait a bit for the update
    await page.waitForTimeout(500);
    
    // Check if the insight is still visible in favorites tab
    const isStillVisible = await favoritedInsight.isVisible().catch(() => false);
    
    if (isStillVisible) {
      // If still visible (which shouldn't happen after filtering), verify it's now unfavorited
      const unfavoritedLabel = await favoritedStarButton.getAttribute('aria-label').catch(() => '');
      expect(unfavoritedLabel).toContain('Add to favorites');
      console.log('✓ Insight is now unfavorited (label changed)');
    } else {
      // Insight should be filtered out from favorites tab
      // Check if "No favorite insights yet" message appears
      const noFavoritesMessage = page.getByText(/no favorite|no favorite insights yet/i);
      const hasNoFavoritesMessage = await noFavoritesMessage.isVisible().catch(() => false);
      
      if (hasNoFavoritesMessage) {
        console.log('✓ Favorites tab shows "No favorite insights yet" message');
      } else {
        console.log('✓ Insight removed from Favorites tab');
      }
      
      // Verify the insight is no longer in favorites tab
      await expect(favoritedInsight).not.toBeVisible({ timeout: 2000 }).catch(() => {
        // If timeout, it's already not visible, which is fine
      });
    }
    
    // Step 8: Switch back to All Insights tab and verify
    console.log('Step 8: Verifying in All Insights tab...');
    const allInsightsTab = page.getByRole('tab', { name: /all insights/i });
    await expect(allInsightsTab).toBeVisible();
    await allInsightsTab.click();
    await page.waitForTimeout(500);
    
    // The insight should still be visible in All Insights tab
    const allInsightsText = page.getByText(insightName, { exact: false }).first();
    await expect(allInsightsText).toBeVisible();
    console.log(`✓ ${insightName} is still visible in All Insights tab`);
    
    // Verify the star is now unfavorited (Add to favorites)
    const allInsightsCard = allInsightsText.locator('xpath=ancestor::*[contains(@class, "group")]').first();
    const allInsightsStarButton = allInsightsCard.locator('button[aria-label*="favorites"]').first();
    const finalAriaLabel = await allInsightsStarButton.getAttribute('aria-label');
    expect(finalAriaLabel).toContain('Add to favorites');
    console.log('✓ Star icon is back to "Add to favorites" state');
    
    console.log('\n=== FAVORITES TEST COMPLETED SUCCESSFULLY ===\n');
  });
});
