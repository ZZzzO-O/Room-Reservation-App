// file: src/App.jsx
// purpose: Root application component — orchestrates views, global stores, and backend sync
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useEffect, useCallback } from 'react';

import NavBar from './components/NavBar';
import LoginModal from './components/LoginModal';
import ReservationModal from './components/ReservationModal';
import BrowsePage from './pages/BrowsePage';
import MyReservationsPage from './pages/MyReservationsPage';
import SchedulePage from './pages/SchedulePage';

import {
  fetchCurrentUser,
  logoutUser,
  getStoredUser,
} from './api/authApi';
import { fetchRooms } from './api/roomApi';
import { fetchReservations } from './api/reservationApi';

// Each page has its own URL, so links and refresh open the same page (TC-DEP-06).
const VIEW_PATHS = {
  browse: '/',
  'my-reservations': '/my-reservations',
  schedule: '/schedule',
};

/**
 * Find the page that matches the current browser URL.
 * @returns {string} View key ('browse' | 'my-reservations' | 'schedule').
 */
function viewFromPath() {
  const match = Object.entries(VIEW_PATHS).find(
    ([, path]) => path === window.location.pathname
  );
  return match ? match[0] : 'browse';
}

/**
 * Root component of the Classroom Reservation Application.
 * Manages user authentication, room catalog, reservation state, and active page views.
 * @returns {JSX.Element} The App component.
 */
export default function App() {
  const [activeView, setActiveView] = useState(viewFromPath);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Global domain state
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [rooms, setRooms] = useState([]);
  const [reservations, setReservations] = useState([]);

  // Modals state: auto-prompt login if no active session
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(!getStoredUser());
  const [selectedRoomForBooking, setSelectedRoomForBooking] = useState(null);

  /**
   * Forget the user and their data, then ask them to sign in again.
   * Used after sign-out and whenever the server rejects the token (1.5, TC-DEP-07).
   */
  const endSession = useCallback(() => {
    setCurrentUser(null);
    setRooms([]);
    setReservations([]);
    setSelectedRoomForBooking(null);
    setIsLoginModalOpen(true);
  }, []);

  const reloadData = useCallback(async () => {
    try {
      const [fetchedRooms, fetchedReservations] = await Promise.all([
        fetchRooms(),
        fetchReservations(),
      ]);
      setRooms(fetchedRooms);
      setReservations(fetchedReservations);
    } catch {
      // A failed load may mean the session expired: check once with the server.
      const user = await fetchCurrentUser();
      if (!user) endSession();
    }
  }, [endSession]);

  // On start: confirm the stored session is still valid before showing data.
  useEffect(() => {
    fetchCurrentUser().then((u) => {
      if (u) {
        setCurrentUser(u);
        reloadData();
      } else {
        endSession();
      }
    });
  }, [reloadData, endSession]);

  // Reload when switching pages or returning to the tab, so other users'
  // changes on the shared server show up without a manual refresh.
  useEffect(() => {
    if (currentUser) reloadData();
  }, [activeView]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onFocus = () => {
      if (getStoredUser()) reloadData();
    };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [reloadData]);

  // Browser Back/Forward moves between pages.
  useEffect(() => {
    const onPopState = () => setActiveView(viewFromPath());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = (view) => {
    setActiveView(view);
    const path = VIEW_PATHS[view] || '/';
    if (window.location.pathname !== path) {
      window.history.pushState({}, '', path);
    }
  };

  const toggleDarkMode = () => setIsDarkMode((prev) => !prev);

  const handleLogout = async () => {
    await logoutUser();
    endSession();
  };

  const handleBookClick = (room) => {
    if (!room.isAvailable) return;
    setSelectedRoomForBooking(room);
  };

  return (
    <div className={isDarkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
        <NavBar
          activeView={activeView}
          onNavigate={navigate}
          isDarkMode={isDarkMode}
          toggleDarkMode={toggleDarkMode}
          currentUser={currentUser}
          onOpenLogin={() => setIsLoginModalOpen(true)}
          onLogout={handleLogout}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeView === 'browse' && (
            <BrowsePage
              rooms={rooms}
              reservations={reservations}
              currentUser={currentUser}
              onBookClick={handleBookClick}
              onRefreshRooms={reloadData}
            />
          )}

          {activeView === 'my-reservations' && (
            <MyReservationsPage
              reservations={reservations}
              rooms={rooms}
              onRefresh={reloadData}
              onNavigateToBrowse={() => navigate('browse')}
            />
          )}

          {activeView === 'schedule' && (
            <SchedulePage
              reservations={reservations}
              rooms={rooms}
            />
          )}
        </main>

        <LoginModal
          isOpen={isLoginModalOpen}
          onClose={() => setIsLoginModalOpen(false)}
          onLoginSuccess={(user) => {
            setCurrentUser(user);
            setIsLoginModalOpen(false);
            reloadData();
          }}
        />

        {selectedRoomForBooking && (
          <ReservationModal
            room={selectedRoomForBooking}
            rooms={rooms}
            onClose={() => setSelectedRoomForBooking(null)}
            onSuccess={reloadData}
          />
        )}
      </div>
    </div>
  );
}
