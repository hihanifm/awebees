import { test } from '@playwright/test';

/**
 * Demo Script: Ripgrep Banner - Windows User Experience
 * 
 * This script shows what Windows users see when they visit the app.
 * It simulates a Windows user agent to show the Windows-specific installation command.
 * 
 * Run with:
 * - npm run test:e2e:headed -- demo-ripgrep-banner-windows.spec.ts
 */

test('Demo: What Windows Users See', async ({ browser }) => {
  // Create context with Windows user agent
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1280, height: 720 }
  });
  
  const page = await context.newPage();
  
  // Navigate with demo parameter
  await page.goto('/?demo-ripgrep-banner=true');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);
  
  // Check if banner is visible
  const banner = page.locator('text=Install Ripgrep for 10x-100x Faster Search');
  await banner.waitFor({ state: 'visible', timeout: 5000 });
  
  // Get the actual command shown
  const commandElement = page.locator('.font-mono').first();
  const commandText = await commandElement.textContent();
  
  // Verify it's the Windows command
  const expectedCommand = 'winget install BurntSushi.ripgrep.MSVC';
  
  console.log('\n=== What Windows Users See ===');
  console.log(`Platform detected: Windows`);
  console.log(`Installation command shown: "${commandText?.trim()}"`);
  console.log(`Expected: "${expectedCommand}"`);
  console.log(`Match: ${commandText?.trim() === expectedCommand ? '✓ YES' : '✗ NO'}`);
  console.log('================================\n');
  
  console.log('The banner displays:');
  console.log('  Title: ⚡ Install Ripgrep for 10x-100x Faster Search');
  console.log('  Description: Ripgrep makes pattern matching significantly faster. Install it now for better performance.');
  console.log(`  Command: ${commandText?.trim()}`);
  console.log('  Button: Installation Guide (links to GitHub)');
  console.log('  Dismiss: X button in top-right\n');
  
  // Keep open for 15 seconds so user can see it
  console.log('Keeping browser open for 15 seconds so you can see the banner...');
  await page.waitForTimeout(15000);
  
  await context.close();
});
