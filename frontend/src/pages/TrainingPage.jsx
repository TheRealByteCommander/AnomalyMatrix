import { useEffect, useState } from 'react';
import ContextHelp from '../components/ContextHelp';
import ModelTraining from '../components/ModelTraining';
import { fetchAuthMe, fetchCameras, fetchRecipes } from '../services';
import { resolveRecipeSelection } from '../recipeSelection';
import { useI18n } from '../i18n/I18nProvider';

export default function TrainingPage({
  openHelp,
  selectedRecipeId = '',
  setSelectedRecipeId = () => {},
}) {
  const { t } = useI18n();
  const [recipes, setRecipes] = useState([]);
  const [cameraId, setCameraId] = useState('');
  const [canTrain, setCanTrain] = useState(false);
  const [canPromote, setCanPromote] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [recipeData, cameraData, me] = await Promise.all([
          fetchRecipes().catch(() => ({ items: [] })),
          fetchCameras().catch(() => ({ cameras: [], selection: { camera_ids: [] } })),
          fetchAuthMe().catch(() => null),
        ]);
        if (cancelled) return;
        const items = recipeData.items || [];
        setRecipes(items);
        if (items.length) {
          setSelectedRecipeId((prev) => resolveRecipeSelection(items, prev));
        }
        const selected =
          cameraData.selection?.camera_ids?.[0] ||
          (cameraData.cameras || []).find((c) => c.selected)?.camera_id ||
          (cameraData.cameras || [])[0]?.camera_id ||
          '';
        setCameraId(selected);
        const role = me?.role_id || me?.role || '';
        const permissions = Array.isArray(me?.permissions) ? me.permissions : null;
        setCanTrain(permissions ? permissions.includes('models.train') : role === 'admin' || role === 'process_engineer');
        setCanPromote(permissions ? permissions.includes('models.promote') : role === 'admin' || role === 'process_engineer');
      } catch {
        if (!cancelled) setRecipes([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [setSelectedRecipeId]);

  const recipeId = resolveRecipeSelection(recipes, selectedRecipeId) || selectedRecipeId;

  return (
    <section className="page-grid">
      <header className="page-intro">
        <p className="eyebrow">{t('training.eyebrow')}</p>
        <h2>{t('training.title')}</h2>
        <p className="muted">{t('training.hint')}</p>
        <ContextHelp articleId="good-part-training" onOpen={openHelp} />
      </header>
      <ModelTraining
        recipes={recipes}
        selectedRecipeId={recipeId}
        selectedCameraId={cameraId}
        canTrain={canTrain}
        canPromote={canPromote}
        openHelp={openHelp}
        onSelectRecipe={setSelectedRecipeId}
      />
    </section>
  );
}
