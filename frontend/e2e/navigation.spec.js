import { test, expect } from '@playwright/test';

test('HMI shell and tab navigation', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('nav-dashboard')).toBeVisible();
  await expect(page.getByTestId('skip-to-content')).toBeAttached();

  await page.getByTestId('nav-trends').click();
  await expect(page.getByTestId('nav-trends')).toHaveClass(/active/);

  await page.getByTestId('nav-configuration').click();
  await expect(page.getByTestId('nav-configuration')).toHaveClass(/active/);

  await page.getByTestId('nav-help').click();
  await expect(page.getByTestId('nav-help')).toHaveClass(/active/);
});

test('dashboard run button visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('dashboard-run')).toBeVisible();
});
