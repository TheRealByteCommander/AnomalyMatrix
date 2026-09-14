import { resolveRecipeSelection } from './recipeSelection.js';

export const HEATMAP_POLL_MS = 1500;

function isRenderableHeatmapUri(uri) {
  if (!uri || typeof uri !== 'string') return false;
  if (uri.startsWith('synthetic:') || uri.startsWith('placeholder:')) return false;
  return (
    uri.startsWith('/') ||
    uri.startsWith('http://') ||
    uri.startsWith('https://') ||
    uri.startsWith('data:')
  );
}

export function formatAnomalyScore(score, empty = '—') {
  if (score == null || score === '') return empty;
  const n = Number(score);
  if (!Number.isFinite(n)) return empty;
  return n.toFixed(2);
}

export function recipeDisplayLabel(recipes, recipeId) {
  const id = String(recipeId || '').trim();
  if (!id) return '';
  const match = Array.isArray(recipes) ? recipes.find((item) => item?.recipe_id === id) : null;
  const name = String(match?.name || '').trim();
  return name || id;
}

export function resolveDisplayRecipeId({ selectedRecipeId, recipes, inspectionRecipeId } = {}) {
  const fromSelection = resolveRecipeSelection(recipes, selectedRecipeId);
  if (fromSelection) return fromSelection;
  return String(inspectionRecipeId || selectedRecipeId || '').trim();
}

export function canShowHeatmapImage(inspection) {
  if (!inspection || inspection.heatmapPlaceholder) return false;
  return isRenderableHeatmapUri(inspection.heatmapUri);
}
