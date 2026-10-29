// file: src/components/ModalShell.jsx
// purpose: Shared dialog frame (overlay, header, Escape to close) used by every modal
// author: Zin Zin Zaw Win
// date: 2026-10-29

import React, { useEffect, useId } from 'react';
import { X } from 'lucide-react';

const WIDTHS = {
  md: 'max-w-md',
  lg: 'max-w-lg',
};

/**
 * Accessible modal frame. Closes on Escape and on the header close button.
 * @param {Object} props
 * @param {string} props.title - Dialog heading text.
 * @param {function} props.onClose - Dismiss callback.
 * @param {'md'|'lg'} [props.size='md'] - Max width of the panel.
 * @param {React.ReactNode} props.children - Dialog body.
 * @returns {JSX.Element} The modal frame.
 */
export default function ModalShell({ title, onClose, size = 'md', children }) {
  const titleId = useId();

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      className="fixed inset-0 z-50 flex items-start sm:items-center justify-center p-4 bg-slate-900/50 overflow-y-auto"
    >
      <div
        className={`w-full ${WIDTHS[size]} my-8 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700`}
      >
        <div className="flex items-center justify-between gap-4 px-5 py-3.5 border-b border-slate-200 dark:border-slate-700">
          <h2
            id={titleId}
            className="text-base font-semibold text-slate-900 dark:text-white"
          >
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="p-2 -mr-2 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:hover:text-white dark:hover:bg-slate-700 transition-colors"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
