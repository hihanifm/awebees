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

  test("should open Settings dialog via top navigation", async ({ page }) => {
    // Find and click the Settings button in the top navigation
    const settingsButton = page.getByRole("button", { name: /settings/i });
    await expect(settingsButton).toBeVisible();
    
    // Click the button
    await settingsButton.click();
    
    // Wait for settings dialog to appear
    const settingsDialog = page.getByRole("dialog", { name: /settings/i });
    await expect(settingsDialog).toBeVisible({ timeout: 2000 });
    
    // Verify settings dialog content (use heading to avoid multiple matches)
    await expect(settingsDialog.getByRole("heading", { name: /settings/i })).toBeVisible();
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
});
