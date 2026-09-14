import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  canShowHeatmapImage,
  formatAnomalyScore,
  recipeDisplayLabel,
  resolveDisplayRecipeId,
} from './heatmapDisplay.js';

const recipes = [
  { recipe_id: 'recipe-default', name: 'Default', active: true },
  { recipe_id: 'recipe-custom', name: 'Custom Seam', active: false },
];

describe('formatAnomalyScore', () => {
  it('formats finite scores with two decimals', () => {
    assert.equal(formatAnomalyScore(0.12), '0.12');
    assert.equal(formatAnomalyScore('0.9'), '0.90');
    assert.equal(formatAnomalyScore(0), '0.00');
  });

  it('uses an em dash when no inspection score exists', () => {
    assert.equal(formatAnomalyScore(null), '—');
    assert.equal(formatAnomalyScore(undefined), '—');
    assert.equal(formatAnomalyScore(''), '—');
    assert.equal(formatAnomalyScore(Number.NaN), '—');
  });
});

describe('recipeDisplayLabel', () => {
  it('prefers the recipe name and falls back to the id', () => {
    assert.equal(recipeDisplayLabel(recipes, 'recipe-custom'), 'Custom Seam');
    assert.equal(recipeDisplayLabel(recipes, 'recipe-gone'), 'recipe-gone');
    assert.equal(recipeDisplayLabel(recipes, ''), '');
  });
});

describe('resolveDisplayRecipeId', () => {
  it('keeps the operator selection when the recipe still exists', () => {
    assert.equal(
      resolveDisplayRecipeId({
        selectedRecipeId: 'recipe-custom',
        recipes,
        inspectionRecipeId: 'recipe-default',
      }),
      'recipe-custom'
    );
  });

  it('falls back to the inspection recipe when nothing is selected', () => {
    assert.equal(
      resolveDisplayRecipeId({
        selectedRecipeId: '',
        recipes: [],
        inspectionRecipeId: 'recipe-from-run',
      }),
      'recipe-from-run'
    );
  });
});

describe('canShowHeatmapImage', () => {
  it('requires a renderable non-placeholder URI', () => {
    assert.equal(canShowHeatmapImage(null), false);
    assert.equal(canShowHeatmapImage({ heatmapUri: 'placeholder:none', heatmapPlaceholder: true }), false);
    assert.equal(canShowHeatmapImage({ heatmapUri: 'data:image/png;base64,abc', heatmapPlaceholder: false }), true);
    assert.equal(canShowHeatmapImage({ heatmapUri: '/artifacts/heat.png', heatmapPlaceholder: false }), true);
  });
});
