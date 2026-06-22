import { getHelpArticles } from './helpContent';

function normalize(text) {
  return String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function articleHaystack(article) {
  const sectionText = (article.sections || [])
    .flatMap((s) => [s.heading, ...(s.paragraphs || [])])
    .join(' ');
  return normalize(
    [article.title, article.summary, ...(article.keywords || []), sectionText].join(' ')
  );
}

/**
 * @param {string} query
 * @param {{ categoryId?: string, locale?: string }} options
 */
export function searchHelpArticles(query, options = {}) {
  const { categoryId, locale = 'de' } = options;
  let pool = getHelpArticles(locale);
  if (categoryId) {
    pool = pool.filter((a) => a.category === categoryId);
  }
  const q = normalize(query.trim());
  if (!q) {
    return pool.map((article) => ({ article, score: 0 }));
  }

  const tokens = q.split(/\s+/).filter(Boolean);

  return pool
    .map((article) => {
      const hay = articleHaystack(article);
      let score = 0;
      for (const token of tokens) {
        if (normalize(article.title).includes(token)) score += 10;
        if ((article.keywords || []).some((k) => normalize(k).includes(token))) score += 6;
        if (hay.includes(token)) score += 2;
      }
      return { article, score };
    })
    .filter((r) => r.score > 0)
    .sort((a, b) => b.score - a.score);
}
