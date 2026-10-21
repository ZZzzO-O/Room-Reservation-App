// file: HomePage.jsx
// purpose: Main dashboard for browsing and filtering rooms
// author: Zin Zin Zaw Win
// date: 2026-10-16

import React, { useState, useEffect } from 'react';

import { fetchRooms } from '../api/roomApi.js';
import NavBar from '../components/NavBar';
import RoomCard from '../components/RoomCard';

/**
 * Main page displaying the room list with filtering and navigation.
 * Loads rooms asynchronously and applies projector filter logic.
 * @returns {JSX.Element} The home page dashboard element.
 */
export default function HomePage() {
  const [rooms, setRooms] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [filterProjector, setFilterProjector] = useState(false);

  useEffect(() => {
    const loadRooms = async () => {
      const fetchedRooms = await fetchRooms();
      setRooms(fetchedRooms);
      setIsLoading(false);
    };

    loadRooms();
  }, []);

  /** Toggle between light and dark mode. */
  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
  };

  /**
   * Handle a room reservation request.
   * @param {{id: string, name: string}} selectedRoom - The room the user wants to reserve.
   */
  const handleReserveClick = (selectedRoom) => {
    alert(`Reservation requested for Room ${selectedRoom.id}`);
    console.log('Reserving room: ', selectedRoom.id);
  };

  /** Apply filtering logic: optionally show only rooms with a projector. */
  const filteredRooms = filterProjector
    ? rooms.filter((room) => room.hasProjector === true)
    : rooms;

  if (isLoading === true) {
    return <div className="loading">Loading rooms...</div>;
  }

  return (
    <div className={isDarkMode === true ? 'app dark-mode' : 'app'}>
      <NavBar isDarkMode={isDarkMode} onToggleDarkMode={handleToggleDarkMode} />

      <div className="filter-bar">
        <label htmlFor="filter-projector">
          <input
            id="filter-projector"
            type="checkbox"
            checked={filterProjector}
            onChange={() => setFilterProjector(!filterProjector)}
          />
          Show only rooms with projector
        </label>
      </div>

      <div className="room-list">
        {filteredRooms.length === 0 ? (
          <p className="no-results">No rooms match the current filter.</p>
        ) : (
          filteredRooms.map((room) => (
            <RoomCard
              key={room.id}
              room={room}
              onReserveClick={handleReserveClick}
            />
          ))
        )}
      </div>
    </div>
  );
}