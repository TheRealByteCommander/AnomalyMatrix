import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  RECIPE_SELECTION_KEY,
  readStoredRecipeId,
  resolveRecipeSelection,
  writeStoredRecipeId,
} from './recipeSelection.js';

function memoryStorage(initial = {}) {
  const data = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      data[key] = String(value);
    },
    removeItem(key) {
      delete data[key];
    },
    snapshot() {
      return { ...data };
    },
  };
}

const recipes = [
  { recipe_id: 'recipe-default', name: 'Default', active: true, status: 'active' },
  { recipe_id: 'recipe-custom', name: 'Custom', active: false, status: 'inactive' },
];

describe('resolveRecipeSelection', () => {
  it('keeps the operator selection when the recipe still exists', () => {
    assert.equal(resolveRecipeSelection(recipes, 'recipe-custom'), 'recipe-custom');
  });

  it('falls back to the active recipe when the selection was deleted', () => {
    assert.equal(resolveRecipeSelection(recipes, 'recipe-gone'), 'recipe-default');
  });

  it('falls back to the first recipe when none is marked active', () => {
    const inactive = [
      { recipe_id: 'recipe-a', active: false },
      { recipe_id: 'recipe-b', active: false },
    ];
    assert.equal(resolveRecipeSelection(inactive, 'missing'), 'recipe-a');
  });

  it('returns empty when there are no recipes', () => {
    assert.equal(resolveRecipeSelection([], 'recipe-custom'), '');
    assert.equal(resolveRecipeSelection(null, ''), '');
  });
});

describe('recipe selection session storage', () => {
  it('round-trips the selected recipe id', () => {
    const storage = memoryStorage();
    writeStoredRecipeId('recipe-custom', storage);
    assert.equal(storage.snapshot()[RECIPE_SELECTION_KEY], 'recipe-custom');
    assert.equal(readStoredRecipeId(storage), 'recipe-custom');
  });

  it('clears storage when the selection is empty', () => {
    const storage = memoryStorage({ [RECIPE_SELECTION_KEY]: 'recipe-custom' });
    writeStoredRecipeId('', storage);
    assert.equal(readStoredRecipeId(storage), '');
    assert.equal(storage.snapshot()[RECIPE_SELECTION_KEY], undefined);
  });
});
