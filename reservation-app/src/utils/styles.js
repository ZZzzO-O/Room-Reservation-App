// file: src/utils/styles.js
// purpose: Shared Tailwind class strings for form fields and buttons
// author: Zin Zin Zaw Win
// date: 2026-10-29

export const LABEL =
  'block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1';

export const INPUT =
  'w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md text-sm text-slate-900 dark:text-white tabular-nums outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30';

export const BTN_PRIMARY =
  'inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white transition-colors disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500';

export const BTN_SECONDARY =
  'inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors disabled:opacity-60';

export const BTN_DANGER =
  'inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-60';

export const ERROR_BOX =
  'p-3 rounded-md border border-red-200 dark:border-red-800/60 bg-red-50 dark:bg-red-900/30 text-sm text-red-700 dark:text-red-300';
