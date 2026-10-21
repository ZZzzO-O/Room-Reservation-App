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
import {
  fetchRooms,
  resetRoomsToSeed,
} from './api/roomApi';
import {
  fetchReservations,
  resetReservationsToSeed,
} from './api/reservationApi';

/**
 * Root component of the Classroom Reservation Application.
 * Manages user authentication, room catalog, reservation state, and active page views.
 * @returns {JSX.Element} The App component.
 */
export default function App() {
  const [activeView, setActiveView] = useState('browse');
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Global domain state
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const [rooms, setRooms] = useState([]);
  const [reservations, setReservations] = useState([]);

  // Modals state
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [selectedRoomForBooking, setSelectedRoomForBooking] = useState(null);

  /**
   * Refetch rooms and reservations from API / storage.
   */
  const reloadData = useCallback(async () => {
    try {
      const [fetchedRooms, fetchedReservations] = await Promise.all([
        fetchRooms(),
        fetchReservations(),
      ]);
      setRooms(fetchedRooms);
      setReservations(fetchedReservations);
    } catch {
      // Storage fallback handled within API functions
    }
  }, []);

  /**
   * Initial data load on component mount.
   */
  useEffect(() => {
    fetchCurrentUser().then((u) => {
      if (u) setCurrentUser(u);
    });
    reloadData();
  }, [reloadData]);

  /** Toggle dark mode CSS class on root container. */
  const toggleDarkMode = () => setIsDarkMode((prev) => !prev);

  /** Log out current user. */
  const handleLogout = async () => {
    await logoutUser();
    setCurrentUser(null);
  };

  /** Reset everything back to the official test plan seed data. */
  const handleResetSeedData = async () => {
    resetRoomsToSeed();
    resetReservationsToSeed();
    await reloadData();
  };

  /** Open booking modal for a specific room. */
  const handleBookClick = (room) => {
    if (!room.isAvailable) return;
    setSelectedRoomForBooking(room);
  };

  return (
    <div className={isDarkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 font-sans text-slate-900 dark:text-slate-100 transition-colors duration-200">
        <NavBar
          activeView={activeView}
          onNavigate={setActiveView}
          isDarkMode={isDarkMode}
          toggleDarkMode={toggleDarkMode}
          currentUser={currentUser}
          onOpenLogin={() => setIsLoginModalOpen(true)}
          onLogout={handleLogout}
          onResetSeed={handleResetSeedData}
        />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeView === 'browse' && (
            <BrowsePage
              rooms={rooms}
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
              onNavigateToBrowse={() => setActiveView('browse')}
            />
          )}

          {activeView === 'schedule' && (
            <SchedulePage
              reservations={reservations}
              rooms={rooms}
            />
          )}
        </main>

        {/* Global Modals */}
        <LoginModal
          isOpen={isLoginModalOpen}
          onClose={() => setIsLoginModalOpen(false)}
          onLoginSuccess={(user) => {
            setCurrentUser(user);
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