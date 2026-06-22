import { useI18n } from '../i18n/I18nProvider';

export default function ContextHelp({ label, onOpen, articleId }) {
  const { t } = useI18n();
  const text = label || t('common.contextHelp');

  return (
    <button
      type="button"
      className="context-help-link"
      onClick={() => onOpen(articleId)}
      aria-label={text}
    >
      <span className="context-help-icon" aria-hidden="true">?</span>
      {text}
    </button>
  );
}
