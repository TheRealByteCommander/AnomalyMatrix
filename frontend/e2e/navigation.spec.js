import { test, expect } from '@playwright/test';

test('HMI shell and primary navigation', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('nav-dashboard')).toBeVisible();
  await expect(page.getByTestId('nav-inspectionDetail')).toBeVisible();
  await expect(page.getByTestId('nav-training')).toBeVisible();
  await expect(page.getByTestId('nav-configuration')).toBeVisible();
  await expect(page.getByTestId('skip-to-content')).toBeAttached();
  await expect(page.getByTestId('nav-dashboard')).toHaveClass(/active/);

  await page.getByTestId('nav-training').click();
  await expect(page.getByTestId('nav-training')).toHaveClass(/active/);
  await expect(page.getByTestId('training-panel')).toBeVisible();

  await page.getByTestId('nav-configuration').click();
  await expect(page.getByTestId('nav-configuration')).toHaveClass(/active/);
  await expect(page.getByTestId('settings-recipes')).toBeVisible();
  await expect(page.getByTestId('settings-license')).toBeVisible();

  await page.getByTestId('settings-recipes').click();
  await expect(page.getByTestId('recipe-manager')).toBeVisible();
  await page.getByTestId('settings-back').click();

  await page.getByTestId('settings-thresholds').click();
  await expect(page.getByTestId('decision-thresholds')).toBeVisible();
  await page.getByTestId('settings-back').click();

  await page.getByTestId('settings-vision').click();
  await expect(page.getByTestId('vision-setup')).toBeVisible();
  await page.getByTestId('settings-back').click();

  await page.getByTestId('settings-storage').click();
  await expect(page.getByTestId('storage-endurance')).toBeVisible();
  await page.getByTestId('settings-back').click();

  await page.getByTestId('settings-license').click();
  await expect(page.getByTestId('license-panel')).toBeVisible();
  await page.getByTestId('settings-back').click();

  await page.getByTestId('nav-trends').click();
  await expect(page.getByTestId('trends-page')).toBeVisible();

  await page.getByTestId('nav-configuration').click();
  await page.getByTestId('nav-help').click();
  await expect(page.getByTestId('help-page')).toBeVisible();
});

test('dashboard run button visible', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('dashboard-run')).toBeVisible();
  await expect(page.getByTestId('dashboard-training')).toBeVisible();
  await page.getByTestId('dashboard-training').click();
  await expect(page.getByTestId('training-panel')).toBeVisible();
  await page.getByTestId('nav-configuration').click();
  await page.getByTestId('settings-recipes').click();
  await expect(page.getByTestId('recipe-manager')).toBeVisible();
});
