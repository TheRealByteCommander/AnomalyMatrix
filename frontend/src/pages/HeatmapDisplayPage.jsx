import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { wantsFullscreen } from '../displayRoute';
import {
  HEATMAP_POLL_MS,
  canShowHeatmapImage,
  formatAnomalyScore,
  recipeDisplayLabel,
  resolveDisplayRecipeId,
} from '../heatmapDisplay';
import { useI18n } from '../i18n/I18nProvider';
import { RECIPE_SELECTION_KEY, readSharedRecipeId, readStoredRecipeId } from '../recipeSelection';
import { fetchRecentInspections, fetchRecipes } from '../services';

function currentRecipeId() {
  return readStoredRecipeId() || readSharedRecipeId();
}

async function enterFullscreen(el) {
  if (!el) return false;
  const request = el.requestFullscreen || el.webkitRequestFullscreen || el.msRequestFullscreen;
  if (!request) return false;
  try {
    await request.call(el);
    return true;
  } catch {
    return false;
  }
}

async function exitFullscreen() {
  const exit = document.exitFullscreen || document.webkitExitFullscreen || document.msExitFullscreen;
  if (!exit) return;
  try {
    await exit.call(document);
  } catch {
    // ignore
  }
}

function isDocumentFullscreen() {
  return Boolean(document.fullscreenElement || document.webkitFullscreenElement || document.msFullscreenElement);
}

export default function HeatmapDisplayPage() {
  const { t } = useI18n();
  const rootRef = useRef(null);
  const [inspection, setInspection] = useState(null);
  const [recipes, setRecipes] = useState([]);
  const [selectedRecipeId, setSelectedRecipeId] = useState(() => currentRecipeId());
  const [fullscreen, setFullscreen] = useState(false);

  const refreshLiveState = useCallback(async () => {
    setSelectedRecipeId(currentRecipeId());
    const [latest, recipeData] = await Promise.all([
      fetchRecentInspections(1).catch(() => []),
      fetchRecipes().catch(() => ({ items: [] })),
    ]);
    setRecipes(recipeData.items || []);
    setInspection(latest[0] || null);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await refreshLiveState();
      } catch {
        if (!cancelled) {
          setInspection(null);
        }
      }
    })();

    const timer = window.setInterval(() => {
      refreshLiveState().catch(() => {});
    }, HEATMAP_POLL_MS);

    function onVisible() {
      if (document.visibilityState === 'visible') refreshLiveState().catch(() => {});
    }
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [refreshLiveState]);

  useEffect(() => {
    function onStorage(event) {
      if (event.key && event.key !== RECIPE_SELECTION_KEY) return;
      setSelectedRecipeId(currentRecipeId());
    }
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  useEffect(() => {
    function syncFullscreen() {
      setFullscreen(isDocumentFullscreen());
    }
    document.addEventListener('fullscreenchange', syncFullscreen);
    document.addEventListener('webkitfullscreenchange', syncFullscreen);
    return () => {
      document.removeEventListener('fullscreenchange', syncFullscreen);
      document.removeEventListener('webkitfullscreenchange', syncFullscreen);
    };
  }, []);

  useEffect(() => {
    if (!wantsFullscreen()) return undefined;
    const el = rootRef.current;
    if (!el) return undefined;
    let cancelled = false;
    enterFullscreen(el).then((ok) => {
      if (!cancelled) setFullscreen(ok || isDocumentFullscreen());
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const recipeId = resolveDisplayRecipeId({
    selectedRecipeId,
    recipes,
    inspectionRecipeId: inspection?.recipeId,
  });
  const recipeLabel = recipeDisplayLabel(recipes, recipeId);
  const showImage = canShowHeatmapImage(inspection);
  const waiting = !inspection;
  const scoreText = waiting ? '—' : formatAnomalyScore(inspection.score);
  const decision = waiting ? '' : inspection.decision || 'green';

  const ariaHeatmap = useMemo(() => t('inspectionDetail.heatmapAria'), [t]);

  async function toggleFullscreen() {
    if (isDocumentFullscreen()) {
      await exitFullscreen();
      setFullscreen(false);
      return;
    }
    const ok = await enterFullscreen(rootRef.current);
    setFullscreen(ok || isDocumentFullscreen());
  }

  return (
    <div
      ref={rootRef}
      className="heatmap-display"
      data-testid="heatmap-display"
      data-inspection-id={inspection?.id || ''}
    >
      {showImage ? (
        <img
          className="heatmap-display-image"
          src={inspection.heatmapUri}
          alt={ariaHeatmap}
          data-testid="heatmap-display-image"
        />
      ) : (
        <div className="heatmap-display-empty" data-testid="heatmap-display-empty">
          <p>{waiting ? t('heatmapDisplay.waiting') : t('heatmapDisplay.noHeatmap')}</p>
        </div>
      )}

      <div
        className={`heatmap-display-score heatmap-display-score-${decision || 'idle'}`}
        data-testid="heatmap-display-score"
        data-decision={decision || 'idle'}
      >
        <span className="heatmap-display-score-label">{t('heatmapDisplay.scoreLabel')}</span>
        <strong>{scoreText}</strong>
      </div>

      <div className="heatmap-display-recipe" data-testid="heatmap-display-recipe">
        {recipeLabel || t('heatmapDisplay.noRecipe')}
      </div>

      <button
        type="button"
        className="heatmap-display-fs"
        data-testid="heatmap-display-fullscreen"
        onClick={toggleFullscreen}
      >
        {fullscreen ? t('heatmapDisplay.exitFullscreen') : t('heatmapDisplay.fullscreen')}
      </button>
    </div>
  );
}
