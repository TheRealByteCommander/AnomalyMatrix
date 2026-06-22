import * as de from './helpContent.de.js';
import * as en from './helpContent.en.js';

const PACKS = { de, en };

export function getHelpPack(locale = 'de') {
  return PACKS[locale] || PACKS.de;
}

export function getHelpCategories(locale) {
  return getHelpPack(locale).HELP_CATEGORIES;
}

export function getHelpArticles(locale) {
  return getHelpPack(locale).HELP_ARTICLES;
}

export function getArticleById(id, locale) {
  return getHelpArticles(locale).find((a) => a.id === id) || null;
}

export function getArticlesByCategory(categoryId, locale) {
  return getHelpArticles(locale).filter((a) => a.category === categoryId);
}

export function getFeaturedArticles(locale) {
  return getHelpArticles(locale).filter((a) => a.featured);
}

export function getApplicationOverviewArticles(locale) {
  return getHelpArticles(locale).filter((a) => a.category === 'application');
}
