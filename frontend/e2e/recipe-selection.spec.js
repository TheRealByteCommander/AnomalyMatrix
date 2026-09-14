import { test, expect } from '@playwright/test';
import { CUSTOM_RECIPE_ID, DEFAULT_RECIPE_ID, mockHmiApi } from './hmiApi.js';

test('recipe selection survives inspection, detail, and configuration', async ({ page }) => {
  const api = await mockHmiApi(page);
  await page.goto('/');

  const recipeSelect = page.getByTestId('dashboard-recipe');
  await expect(recipeSelect).toBeVisible();
  await expect(recipeSelect).toHaveValue(DEFAULT_RECIPE_ID);

  await recipeSelect.selectOption(CUSTOM_RECIPE_ID);
  await expect(recipeSelect).toHaveValue(CUSTOM_RECIPE_ID);

  await page.getByTestId('dashboard-run').click();
  await expect.poll(() => api.runRequests.length).toBe(1);
  await expect(page.getByTestId('dashboard-recipe')).toHaveValue(CUSTOM_RECIPE_ID);
  expect(api.runRequests[0].recipe_id).toBe(CUSTOM_RECIPE_ID);
  expect(api.runRequests[0].trigger_source).toBe('hmi');

  await page.getByTestId('dashboard-open-detail').click();
  await expect(page.getByTestId('inspection-id')).toHaveText('INSP-E2E-1');
  await expect(page.getByTestId('inspection-recipe')).toContainText(CUSTOM_RECIPE_ID);
  await expect(page.getByTestId('inspection-score')).toBeVisible();
  await expect(page.getByTestId('qa-feedback-form')).toBeVisible();

  await page.getByTestId('nav-dashboard').click();
  await expect(page.getByTestId('dashboard-recipe')).toHaveValue(CUSTOM_RECIPE_ID);

  await page.getByTestId('nav-configuration').click();
  await expect(page.getByTestId(`recipe-row-${CUSTOM_RECIPE_ID}`)).toHaveClass(/active/);
  await expect(page.getByTestId('training-recipe')).toHaveValue(CUSTOM_RECIPE_ID);
  await expect(page.getByTestId('thresholds-recipe')).toContainText('Custom Seam');
  await expect(page.getByTestId('license-billing')).toBeVisible();
  await expect(page.getByTestId('vision-setup')).toBeVisible();
  await expect(page.getByTestId('storage-endurance')).toBeVisible();

  await page.getByTestId('nav-dashboard').click();
  await page.getByTestId('dashboard-run').click();
  await expect.poll(() => api.runRequests.length).toBe(2);
  expect(api.runRequests[1].recipe_id).toBe(CUSTOM_RECIPE_ID);
});

test('recipe selection is restored from sessionStorage after reload', async ({ page }) => {
  await mockHmiApi(page);
  await page.goto('/');
  await page.getByTestId('dashboard-recipe').selectOption(CUSTOM_RECIPE_ID);
  await expect(page.getByTestId('dashboard-recipe')).toHaveValue(CUSTOM_RECIPE_ID);

  await page.reload();
  await expect(page.getByTestId('dashboard-recipe')).toHaveValue(CUSTOM_RECIPE_ID);
  await page.getByTestId('nav-configuration').click();
  await expect(page.getByTestId(`recipe-row-${CUSTOM_RECIPE_ID}`)).toHaveClass(/active/);
});

test('QA confirm marks inspection n.i.O. in the detail view', async ({ page }) => {
  await mockHmiApi(page);
  await page.goto('/');
  await page.getByTestId('dashboard-run').click();
  await expect.poll(() => page.getByTestId('dashboard-open-detail').isEnabled()).toBeTruthy();
  await page.getByTestId('dashboard-open-detail').click();
  await expect(page.getByTestId('inspection-id')).toHaveText('INSP-E2E-1');
  await page.getByTestId('qa-verdict').selectOption('confirm_anomaly');
  await page.getByTestId('qa-submit').click();
  await expect(page.getByTestId('qa-nio-banner')).toBeVisible();
});
