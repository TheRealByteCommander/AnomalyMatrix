export const HEATMAP_DISPLAY_PATH = '/heatmap';
export const HEATMAP_DISPLAY_PATHS = ['/heatmap', '/display/heatmap'];

export function normalizePath(pathname) {
  const path = String(pathname || '/').replace(/\/+$/, '');
  return path || '/';
}

/** Dedicated operator display (second monitor), not a main HMI tab. */
export function isHeatmapDisplayPath(pathname) {
  const path = normalizePath(
    pathname ?? (typeof window !== 'undefined' ? window.location.pathname : '/')
  );
  return HEATMAP_DISPLAY_PATHS.includes(path);
}

export function wantsFullscreen(search) {
  const query = search ?? (typeof window !== 'undefined' ? window.location.search : '');
  const params = new URLSearchParams(query);
  if (!params.has('fullscreen') && !params.has('fs')) return false;
  const value = params.get('fullscreen') ?? params.get('fs');
  return value === '' || value === '1' || value === 'true';
}
