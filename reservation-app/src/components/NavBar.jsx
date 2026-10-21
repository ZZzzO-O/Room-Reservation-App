// file: src/components/NavBar.jsx
// purpose: Top navigation bar with role badges, authentication controls, and theme toggle
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import {
  Calendar,
  Sun,
  Moon,
  Menu,
  RotateCcw,
  LogIn,
  LogOut,
  Shield,
  GraduationCap,
  CalendarDays,
} from 'lucide-react';

const NAV_TITLE = 'CMKL Reserve';

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
 * @param {function} props.onResetSeed - Handler to reset database to official seed data.
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

  const handleToggleMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);

  return (
    <nav className="bg-slate-900 text-white shadow-lg sticky top-0 z-40 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo / Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shadow-md shadow-blue-500/20">
              <Calendar className="h-5 w-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight block leading-tight">
                {NAV_TITLE}
              </span>
              <span className="text-[10px] text-blue-300 font-medium tracking-wide uppercase">
                Team Vibranium
              </span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <div className="hidden md:flex items-center space-x-1 lg:space-x-2">
            <button
              id="nav-browse"
              onClick={() => onNavigate('browse')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'browse'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              Browse Rooms
            </button>
            <button
              id="nav-my-reservations"
              onClick={() => onNavigate('my-reservations')}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'my-reservations'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              Reservations
            </button>
            <button
              id="nav-schedule"
              onClick={() => onNavigate('schedule')}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeView === 'schedule'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <CalendarDays className="w-4 h-4" />
              Schedule
            </button>

            {/* Reset to Test Seed Button */}
            <button
              id="btn-reset-seed"
              onClick={onResetSeed}
              title="Reset database to official test plan seed data"
              className="flex items-center gap-1 px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-medium transition-colors border border-slate-700 ml-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">Reset Seed</span>
            </button>

            {/* Dark Mode Toggle */}
            <button
              id="toggle-dark-mode"
              onClick={toggleDarkMode}
              className="p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-lg transition-colors ml-1"
              aria-label="Toggle Dark Mode"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* User Profile / Auth State */}
            {currentUser ? (
              <div className="ml-2 flex items-center gap-3 pl-3 border-l border-slate-800">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-xs">
                    {currentUser.name ? currentUser.name.slice(0, 2).toUpperCase() : 'US'}
                  </div>
                  <div className="text-left hidden lg:block">
                    <p className="text-xs font-medium text-white leading-tight">
                      {currentUser.name || currentUser.email}
                    </p>
                    <span
                      className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.2 rounded ${
                        currentUser.role === 'Staff'
                          ? 'bg-blue-900/60 text-blue-300'
                          : 'bg-indigo-900/60 text-indigo-300'
                      }`}
                    >
                      {currentUser.role === 'Staff' ? (
                        <Shield className="w-2.5 h-2.5" />
                      ) : (
                        <GraduationCap className="w-2.5 h-2.5" />
                      )}
                      {currentUser.role}
                    </span>
                  </div>
                </div>
                <button
                  id="btn-sign-out"
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                id="btn-sign-in"
                onClick={onOpenLogin}
                className="ml-2 flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                Sign In
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center md:hidden gap-2">
            <button
              onClick={toggleDarkMode}
              className="p-2 text-slate-300 hover:text-white rounded-lg"
              aria-label="Toggle Dark Mode"
            >
              {isDarkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
            </button>
            <button
              onClick={handleToggleMenu}
              className="text-slate-300 hover:text-white p-2 rounded-lg"
              aria-label="Open menu"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Dropdown */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-slate-800/95 border-t border-slate-700 pb-3 px-4 pt-2 space-y-2">
          <button
            onClick={() => {
              onNavigate('browse');
              setIsMobileMenuOpen(false);
            }}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-white hover:bg-slate-700"
          >
            Browse Rooms
          </button>
          <button
            onClick={() => {
              onNavigate('my-reservations');
              setIsMobileMenuOpen(false);
            }}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-700"
          >
            Reservations
          </button>
          <button
            onClick={() => {
              onNavigate('schedule');
              setIsMobileMenuOpen(false);
            }}
            className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-700"
          >
            Weekly Schedule
          </button>
          <button
            onClick={() => {
              onResetSeed();
              setIsMobileMenuOpen(false);
            }}
            className="block w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-amber-300 hover:bg-slate-700"
          >
            Reset Seed Data
          </button>
          {currentUser ? (
            <button
              onClick={() => {
                onLogout();
                setIsMobileMenuOpen(false);
              }}
              className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-rose-300 hover:bg-slate-700"
            >
              Sign Out ({currentUser.name})
            </button>
          ) : (
            <button
              onClick={() => {
                onOpenLogin();
                setIsMobileMenuOpen(false);
              }}
              className="block w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-blue-300 hover:bg-slate-700"
            >
              Sign In
            </button>
          )}
        </div>
      )}
    </nav>
  );
}