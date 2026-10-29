// file: src/api/reservationApi.js
// purpose: Handles reservation creation, edits, deletion, conflict checks, and schedule exports
// author: Zin Zin Zaw Win
// date: 2026-10-20

import { getAuthHeaders } from './authApi';

const API_BASE_URL = '/api';

const RESERVATIONS_STORAGE_KEY = 'vibranium_reservations_store';

export const SEMESTER_START = '2026-08-17';
export const SEMESTER_END = '2026-12-01';

/**
 * Seed reservations from the Vibranium Functional Test Plan.
 */
export const SEED_RESERVATIONS = [
  {
    reservation_id: 'RES-1',
    competency: 'SEN-201',
    group_size: 35,
    room_id: '301',
    start_date: '2026-10-12',
    end_date: '2026-12-01',
    start_time: '10:00',
    end_time: '12:00',
    day_of_week: 'Monday',
    repetition: 'Weekly',
  },
  {
    reservation_id: 'RES-2',
    competency: 'AIC-101',
    group_size: 25,
    room_id: 'LAB-1',
    start_date: '2026-10-12',
    end_date: '2026-12-01',
    start_time: '13:00',
    end_time: '15:00',
    day_of_week: 'Monday',
    repetition: 'Weekly',
  },
  {
    reservation_id: 'RES-3',
    competency: 'MTH-110',
    group_size: 18,
    room_id: '302',
    start_date: '2026-10-13',
    end_date: '2026-12-01',
    start_time: '09:00',
    end_time: '11:00',
    day_of_week: 'Tuesday',
    repetition: 'Weekly',
  },
];

/**
 * Check if two time slots overlap using the half-open interval rule [start, end).
 * An existing slot 10:00-12:00 does NOT conflict with 12:00-14:00.
 * @param {string} start1 - HH:MM
 * @param {string} end1 - HH:MM
 * @param {string} start2 - HH:MM
 * @param {string} end2 - HH:MM
 * @returns {boolean} True if the slots overlap.
 */
export function doSlotsOverlap(start1, end1, start2, end2) {
  return start1 < end2 && start2 < end1;
}

/**
 * Load offline reservations from localStorage.
 * @returns {Object[]} List of reservation objects.
 */
function getLocalReservations() {
  const raw = localStorage.getItem(RESERVATIONS_STORAGE_KEY);
  if (!raw) {
    localStorage.setItem(
      RESERVATIONS_STORAGE_KEY,
      JSON.stringify(SEED_RESERVATIONS)
    );
    return SEED_RESERVATIONS;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return SEED_RESERVATIONS;
  }
}

/**
 * Save reservations to localStorage.
 * @param {Object[]} list - Array of reservations.
 */
function saveLocalReservations(list) {
  localStorage.setItem(RESERVATIONS_STORAGE_KEY, JSON.stringify(list));
}

/**
 * Fetch all reservations from the server, with offline fallback.
 * @param {string} [roomId] - Optional room filter.
 * @returns {Promise<Object[]>} List of reservations.
 */
export async function fetchReservations(roomId) {
  try {
    const url = roomId
      ? `${API_BASE_URL}/reservations?room_id=${encodeURIComponent(roomId)}`
      : `${API_BASE_URL}/reservations`;

    const response = await fetch(url, { headers: getAuthHeaders() });
    if (response.ok) {
      const data = await response.json();
      const list = data.reservations || [];
      if (!roomId) saveLocalReservations(list);
      return list;
    }
    throw new Error(`Server responded with ${response.status}`);
  } catch {
    const list = getLocalReservations();
    return roomId ? list.filter((r) => r.room_id === roomId) : list;
  }
}

/**
 * Submit a new classroom reservation request.
 * @param {Object} candidate - Reservation details.
 * @returns {Promise<Object>} Created reservation.
 */
export async function createReservation(candidate) {
  // Validate time order
  if (candidate.start_time >= candidate.end_time) {
    throw new Error('End time must be strictly after start time.');
  }

  // Validate semester boundaries
  if (candidate.start_date < SEMESTER_START || candidate.start_date > SEMESTER_END) {
    throw new Error(
      `Reservation date must fall within semester (${SEMESTER_START} to ${SEMESTER_END}).`
    );
  }

  try {
    const response = await fetch(`${API_BASE_URL}/reservations`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(candidate),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to create reservation.');
    }
    return data.reservation;
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }

    // Local fallback conflict check
    const current = getLocalReservations();
    const conflict = current.find(
      (r) =>
        r.room_id === candidate.room_id &&
        r.start_date === candidate.start_date &&
        doSlotsOverlap(
          candidate.start_time,
          candidate.end_time,
          r.start_time,
          r.end_time
        )
    );

    if (conflict) {
      throw new Error(
        `Time conflict: Room ${candidate.room_id} is already reserved for ${conflict.competency} from ${conflict.start_time} to ${conflict.end_time}.`
      );
    }

    const newRes = {
      ...candidate,
      reservation_id: `RES-${Date.now().toString().slice(-4)}`,
    };
    current.push(newRes);
    saveLocalReservations(current);
    return newRes;
  }
}

/**
 * Update an existing reservation.
 * @param {string} reservationId - Identifier of reservation to update.
 * @param {Object} updateData - Modified fields.
 * @returns {Promise<Object>} Updated reservation.
 */
export async function editReservation(reservationId, updateData) {
  try {
    const response = await fetch(`${API_BASE_URL}/reservations/${reservationId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(updateData),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to edit reservation.');
    }
    return data.reservation;
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    const current = getLocalReservations();
    const idx = current.findIndex((r) => r.reservation_id === reservationId);
    if (idx === -1) {
      throw new Error('Reservation not found or already deleted.');
    }
    current[idx] = { ...current[idx], ...updateData };
    saveLocalReservations(current);
    return current[idx];
  }
}

/**
 * Delete a reservation following the Activity Diagram workflow.
 * @param {string} reservationId - ID of reservation to remove.
 * @returns {Promise<void>}
 */
export async function deleteReservation(reservationId) {
  try {
    const response = await fetch(`${API_BASE_URL}/reservations/${reservationId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Reservation could not be found or has already been deleted.');
    }
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    const current = getLocalReservations();
    const exists = current.some((r) => r.reservation_id === reservationId);
    if (!exists) {
      throw new Error('The reservation could not be found or has already been deleted.');
    }
    const filtered = current.filter((r) => r.reservation_id !== reservationId);
    saveLocalReservations(filtered);
  }
}

/**
 * Fetch timetable schedule for a given week.
 * @param {string} weekStart - ISO date (YYYY-MM-DD).
 * @param {string} [roomId] - Optional room filter.
 * @returns {Promise<Object[]>} List of reservations in that week.
 */
export async function fetchSchedule(weekStart, roomId) {
  try {
    let url = `${API_BASE_URL}/reservations/schedule?week_start=${weekStart}`;
    if (roomId) url += `&room_id=${encodeURIComponent(roomId)}`;

    const response = await fetch(url, { headers: getAuthHeaders() });
    if (response.ok) {
      const data = await response.json();
      return data.schedule || [];
    }
  } catch {
    // Local fallback
  }

  // Filter local reservations by room and week range
  const current = getLocalReservations();
  return current.filter((r) => {
    if (roomId && r.room_id !== roomId) return false;
    return true;
  });
}

/**
 * Download exported weekly timetable as a text report.
 * @param {string} weekStart - ISO date (YYYY-MM-DD).
 * @param {string} [roomId] - Optional room filter.
 */
export async function exportScheduleReport(weekStart, roomId) {
  let url = `${API_BASE_URL}/reservations/export?week_start=${weekStart}`;
  if (roomId) url += `&room_id=${encodeURIComponent(roomId)}`;

  try {
    const response = await fetch(url, { headers: getAuthHeaders() });
    if (response.ok) {
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `schedule_${weekStart}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      return;
    }
  } catch {
    // Generate text report on client side if offline
  }

  // Fallback client-side report generator
  const reservations = await fetchSchedule(weekStart, roomId);
  let text = `========================================================\n`;
  text += `CMKL UNIVERSITY - WEEKLY CLASSROOM SCHEDULE\n`;
  text += `Week starting: ${weekStart}\n`;
  if (roomId) text += `Filter: Room ${roomId}\n`;
  text += `Generated: ${new Date().toLocaleString()}\n`;
  text += `========================================================\n\n`;

  if (reservations.length === 0) {
    text += `No reservations found for this week.\n`;
  } else {
    reservations.forEach((r, idx) => {
      text += `${idx + 1}. [${r.competency}] Room: ${r.room_id}\n`;
      text += `   Date: ${r.start_date} | Time: ${r.start_time} - ${r.end_time}\n`;
      text += `   Group Size: ${r.group_size} | Repetition: ${r.repetition || 'Weekly'}\n\n`;
    });
  }

  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `schedule_${weekStart}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Reset the local reservation store back to the seed reservations.
 */
export function resetReservationsToSeed() {
  localStorage.setItem(
    RESERVATIONS_STORAGE_KEY,
    JSON.stringify(SEED_RESERVATIONS)
  );
  return SEED_RESERVATIONS;
}
