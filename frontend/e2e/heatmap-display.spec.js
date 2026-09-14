import { test, expect } from '@playwright/test';
import {
  CUSTOM_RECIPE_ID,
  SAMPLE_HEATMAP_URI,
  inspectionDto,
  mockHmiApi,
} from './hmiApi.js';

async function useGerman(page) {
  await page.addInitScript(() => {
    window.localStorage.setItem('amx-locale', 'de');
  });
}

test('heatmap display is chrome-free and waits without an inspection', async ({ page }) => {
  await useGerman(page);
  await mockHmiApi(page);
  await page.goto('/heatmap');

  await expect(page.getByTestId('heatmap-display')).toBeVisible();
  await expect(page.getByTestId('nav-dashboard')).toHaveCount(0);
  await expect(page.getByTestId('heatmap-display-empty')).toContainText('Warte auf Inspektion');
  await expect(page.getByTestId('heatmap-display-score')).toContainText('—');
  await expect(page.getByTestId('heatmap-display-recipe')).toBeVisible();
  await expect(page.getByTestId('heatmap-display-fullscreen')).toHaveText('Vollbild');
});

test('alias /display/heatmap serves the same operator view', async ({ page }) => {
  await useGerman(page);
  await mockHmiApi(page);
  await page.goto('/display/heatmap');
  await expect(page.getByTestId('heatmap-display')).toBeVisible();
  await expect(page.getByTestId('nav-dashboard')).toHaveCount(0);
});

test('heatmap display shows score, recipe name, and image from the latest inspection', async ({ page }) => {
  await useGerman(page);
  await mockHmiApi(page, {
    inspections: [
      inspectionDto({
        id: 'INSP-HEAT-9',
        recipeId: CUSTOM_RECIPE_ID,
        score: 0.91,
        decision: 'red',
        heatmapUri: SAMPLE_HEATMAP_URI,
        heatmapPlaceholder: false,
      }),
    ],
  });
  await page.goto('/heatmap');

  await expect(page.getByTestId('heatmap-display-score')).toContainText('0.91');
  await expect(page.getByTestId('heatmap-display-score')).toHaveAttribute('data-decision', 'red');
  await expect(page.getByTestId('heatmap-display-recipe')).toHaveText('Custom Seam');
  await expect(page.getByTestId('heatmap-display-image')).toHaveAttribute('src', SAMPLE_HEATMAP_URI);
  await expect(page.getByTestId('heatmap-display-empty')).toHaveCount(0);
});

test('dashboard opens the heatmap monitor and live state follows a new inspection', async ({ page, context }) => {
  await useGerman(page);
  const api = await mockHmiApi(page, { runHeatmapUri: SAMPLE_HEATMAP_URI, runHeatmapPlaceholder: false });
  await page.goto('/');
  await expect(page.getByTestId('dashboard-heatmap-display')).toHaveAttribute('href', '/heatmap');

  await page.getByTestId('dashboard-recipe').selectOption(CUSTOM_RECIPE_ID);
  const display = await context.newPage();
  await useGerman(display);
  await mockHmiApi(display, { state: api });
  await display.goto('/heatmap');
  await expect(display.getByTestId('heatmap-display-empty')).toContainText('Warte auf Inspektion');
  await expect(display.getByTestId('heatmap-display-score')).toContainText('—');
  await expect(display.getByTestId('heatmap-display-recipe')).toHaveText('Custom Seam');

  await page.getByTestId('dashboard-run').click();
  await expect.poll(() => api.runRequests.length).toBe(1);

  await expect(display.getByTestId('heatmap-display-score')).toContainText('0.12', { timeout: 8000 });
  await expect(display.getByTestId('heatmap-display-recipe')).toHaveText('Custom Seam');
  await expect(display.getByTestId('heatmap-display-image')).toBeVisible();
  await expect(display.getByTestId('heatmap-display')).toHaveAttribute('data-inspection-id', 'INSP-E2E-1');
});
