export const RECIPE_SELECTION_KEY = 'amx_selected_recipe_id';

function defaultStorage() {
  try {
    if (typeof sessionStorage !== 'undefined') return sessionStorage;
  } catch {
    // private mode / blocked storage
  }
  return null;
}

export function readStoredRecipeId(storage = defaultStorage()) {
  if (!storage || typeof storage.getItem !== 'function') return '';
  try {
    return storage.getItem(RECIPE_SELECTION_KEY) || '';
  } catch {
    return '';
  }
}

export function writeStoredRecipeId(recipeId, storage = defaultStorage()) {
  if (!storage) return;
  try {
    const value = String(recipeId || '').trim();
    if (value) storage.setItem(RECIPE_SELECTION_KEY, value);
    else if (typeof storage.removeItem === 'function') storage.removeItem(RECIPE_SELECTION_KEY);
  } catch {
    // ignore storage errors
  }
}

/** Keep the operator's recipe when it still exists; otherwise active, then first. */
export function resolveRecipeSelection(recipes, preferredId) {
  const items = Array.isArray(recipes) ? recipes : [];
  const preferred = String(preferredId || '').trim();
  if (preferred && items.some((item) => item?.recipe_id === preferred)) {
    return preferred;
  }
  const active = items.find((item) => item?.active === true || item?.status === 'active');
  return active?.recipe_id || items[0]?.recipe_id || '';
}
