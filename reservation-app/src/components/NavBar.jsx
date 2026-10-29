// file: src/components/NavBar.jsx
// purpose: Top navigation bar with role badges, authentication controls, and theme toggle
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import { Sun, Moon, Menu, X } from 'lucide-react';

const NAV_ITEMS = [
  { key: 'browse', id: 'nav-browse', label: 'Rooms' },
  { key: 'my-reservations', id: 'nav-my-reservations', label: 'Reservations' },
  { key: 'schedule', id: 'nav-schedule', label: 'Weekly schedule' },
];

/**
 * Main application navigation header.
 * @param {Object} props
 * @param {string} props.activeView - Currently active view key ('browse' | 'my-reservations' | 'schedule').
 * @param {function} props.onNavigate - View switch handler.
 * @param {boolean} props.isDarkMode - Active theme flag.
 * @param {function} props.toggleDarkMode - Theme switch handler.
 * @param {Object|null} props.currentUser - Authenticated user profile.
 * @param {function} props.onOpenLogin - Handler to open login modal.
 * @param {function} props.onLogout - Handler to sign out.
 * @param {function} props.onResetSeed - Handler to reset local data to the test plan seed.
 * @returns {JSX.Element} The NavBar component.
 */
export default function NavBar({
  activeView,
  onNavigate,
  isDarkMode,
  toggleDarkMode,
  currentUser,
  onOpenLogin,
  onLogout,
  onResetSeed,
}) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const runAndClose = (action) => () => {
    action();
    setIsMobileMenuOpen(false);
  };

  const themeLabel = isDarkMode ? 'Switch to light mode' : 'Switch to dark mode';
  const ThemeIcon = isDarkMode ? Sun : Moon;

  return (
    <nav className="bg-slate-900 text-white sticky top-0 z-40 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-stretch h-14">
          <div className="flex items-stretch gap-8">
            <span className="flex items-center gap-2 font-semibold tracking-tight">
              <span className="text-brand-300">CMKL</span>
              <span>Rooms</span>
            </span>

            <div className="hidden md:flex items-stretch gap-1">
              {NAV_ITEMS.map((item) => {
                const isActive = activeView === item.key;
                return (
                  <button
                    key={item.key}
                    id={item.id}
                    onClick={() => onNavigate(item.key)}
                    aria-current={isActive ? 'page' : undefined}
                    className={`px-3 text-sm font-medium border-b-2 transition-colors ${
                      isActive
                        ? 'border-brand-300 text-white'
                        : 'border-transparent text-slate-400 hover:text-white'
                    }`}
                  >
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="hidden md:flex items-center gap-1 text-sm">
            <button
              id="btn-reset-seed"
              onClick={onResetSeed}
              title="Restore the rooms and reservations from the test plan"
              className="px-3 py-2 rounded-md text-xs text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              Reset demo data
            </button>

            <button
              id="toggle-dark-mode"
              onClick={toggleDarkMode}
              aria-label={themeLabel}
              title={themeLabel}
              className="p-2.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ThemeIcon className="w-4 h-4" aria-hidden="true" />
            </button>

            {currentUser ? (
              <div className="ml-2 pl-3 flex items-center gap-3 border-l border-slate-700">
                <span className="text-right leading-tight">
                  <span className="block text-xs text-white">
                    {currentUser.name || currentUser.email}
                  </span>
                  <span className="block text-[11px] text-slate-400">{currentUser.role}</span>
                </span>
                <button
                  id="btn-sign-out"
                  onClick={onLogout}
                  className="px-3 py-2 rounded-md text-xs text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <button
                id="btn-sign-in"
                onClick={onOpenLogin}
                className="ml-2 px-3 py-1.5 rounded-md text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white transition-colors"
              >
                Sign in
              </button>
            )}
          </div>

          <div className="flex items-center md:hidden gap-1">
            <button
              onClick={toggleDarkMode}
              aria-label={themeLabel}
              className="p-2.5 rounded-md text-slate-300 hover:text-white"
            >
              <ThemeIcon className="w-5 h-5" aria-hidden="true" />
            </button>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={isMobileMenuOpen}
              className="p-2.5 rounded-md text-slate-300 hover:text-white"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" aria-hidden="true" />
              ) : (
                <Menu className="w-5 h-5" aria-hidden="true" />
              )}
            </button>
          </div>
        </div>
      </div>

      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-slate-800 px-4 py-2 space-y-1">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              onClick={runAndClose(() => onNavigate(item.key))}
              aria-current={activeView === item.key ? 'page' : undefined}
              className={`block w-full text-left px-3 py-2.5 rounded-md text-sm font-medium hover:bg-slate-800 ${
                activeView === item.key ? 'text-white' : 'text-slate-400'
              }`}
            >
              {item.label}
            </button>
          ))}
          <div className="pt-1 mt-1 border-t border-slate-800">
            <button
              onClick={runAndClose(onResetSeed)}
              className="block w-full text-left px-3 py-2.5 rounded-md text-xs text-slate-400 hover:bg-slate-800"
            >
              Reset demo data
            </button>
            {currentUser ? (
              <button
                onClick={runAndClose(onLogout)}
                className="block w-full text-left px-3 py-2.5 rounded-md text-sm text-slate-300 hover:bg-slate-800"
              >
                Sign out ({currentUser.name || currentUser.email})
              </button>
            ) : (
              <button
                onClick={runAndClose(onOpenLogin)}
                className="block w-full text-left px-3 py-2.5 rounded-md text-sm text-brand-300 hover:bg-slate-800"
              >
                Sign in
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
