import { test, expect } from '@playwright/test';

/**
 * Demo Script: Ripgrep Banner - Platform-Specific Messages
 * 
 * This script demonstrates what users see on different platforms.
 * It simulates different user agents to show platform-specific installation commands.
 * 
 * Run with:
 * - npm run test:e2e:headed -- demo-ripgrep-banner-platforms.spec.ts
 */

const platforms = [
  {
    name: 'Windows',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    expectedCommand: 'winget install BurntSushi.ripgrep.MSVC'
  },
  {
    name: 'macOS',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    expectedCommand: 'brew install ripgrep'
  },
  {
    name: 'Linux',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    expectedCommand: 'sudo apt install ripgrep'
  }
];

test.describe('Ripgrep Banner - Platform Detection', () => {
  for (const platform of platforms) {
    test(`should show correct command for ${platform.name}`, async ({ browser }) => {
      const context = await browser.newContext({
        userAgent: platform.userAgent,
      });
      const page = await context.newPage();
      
      // Navigate with demo parameter
      await page.goto('/?demo-ripgrep-banner=true');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
      
      // Check if banner is visible
      const banner = page.locator('text=Install Ripgrep for 10x-100x Faster Search');
      await banner.waitFor({ state: 'visible', timeout: 5000 });
      
      // Check for the platform-specific command
      const commandText = page.locator('text=' + platform.expectedCommand);
      await expect(commandText).toBeVisible();
      
      console.log(`✓ ${platform.name} users see: "${platform.expectedCommand}"`);
      
      // Keep open for a few seconds to see the result
      await page.waitForTimeout(3000);
      
      await context.close();
    });
  }

  test('should display all platform information', async ({ page }) => {
    await page.goto('/?demo-ripgrep-banner=true');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Check banner is visible
    const banner = page.locator('text=Install Ripgrep for 10x-100x Faster Search');
    await banner.waitFor({ state: 'visible', timeout: 5000 });
    
    // Get the detected platform info
    const detectedCommand = await page.locator('code, .font-mono').first().textContent();
    const detectedPlatform = await page.evaluate(() => {
      return {
        platform: navigator.platform,
        userAgent: navigator.userAgent,
      };
    });
    
    console.log('\n=== Detected Platform Info ===');
    console.log(`Platform: ${detectedPlatform.platform}`);
    console.log(`User Agent: ${detectedPlatform.userAgent.substring(0, 80)}...`);
    console.log(`Shown Command: ${detectedCommand}`);
    console.log('================================\n');
    
    await page.waitForTimeout(5000);
  });
});
