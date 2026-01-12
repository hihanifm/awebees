import { test } from '@playwright/test';

/**
 * Demo Script: Ripgrep Banner
 * 
 * This script opens the app with the ripgrep banner visible for demo purposes.
 * Even if ripgrep is installed, the banner will show.
 * 
 * Run with:
 * - npm run test:e2e:headed -- demo-ripgrep-banner.spec.ts
 * - npm run test:e2e:ui -- demo-ripgrep-banner.spec.ts (for interactive mode)
 */

test('Demo: Show Ripgrep Banner', async ({ page }) => {
  // Navigate with demo parameter to force-show the banner
  await page.goto('/?demo-ripgrep-banner=true');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Wait a bit for banner to render
  await page.waitForTimeout(1000);
  
  // Check if banner is visible
  const banner = page.locator('text=Install Ripgrep for 10x-100x Faster Search');
  await banner.waitFor({ state: 'visible', timeout: 5000 });
  
  console.log('✓ Ripgrep banner is visible!');
  console.log('✓ You can now interact with the banner in the browser.');
  console.log('✓ The page will stay open for 30 seconds for demo purposes.');
  
  // Keep the page open for demo (30 seconds)
  await page.waitForTimeout(30000);
});
