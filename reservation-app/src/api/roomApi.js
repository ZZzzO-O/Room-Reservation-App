// file: src/api/roomApi.js
// purpose: Handles room data fetching, CRUD operations, room types, and non-classroom exclusions
// author: Zin Zin Zaw Win
// date: 2026-10-20

import { getAuthHeaders } from './authApi';

const API_BASE_URL = '/api';

const ROOMS_STORAGE_KEY = 'vibranium_rooms_store';

/**
 * Official CMKL campus room directory matching the user's campus specification.
 * Note:
 * - Room 608 (Bridge): Water filling station & faculty area — Excluded from bookable classrooms.
 * - Room 706 (Apex SuperComputer): Server facility — Excluded from bookable classrooms.
 */
export const OFFICIAL_SEED_ROOMS = [
  {
    room_id: '601',
    name: 'Pioneer',
    room_type: 'Classroom',
    capacity: 40,
    equipment: { projector: 1, whiteboard: 2 },
    description: 'Lecture classroom with dual whiteboards',
    unavailable_periods: [],
  },
  {
    room_id: '602',
    name: 'Voyager',
    room_type: 'Student Lab',
    capacity: 35,
    equipment: { whiteboard: 2 },
    description: 'Student project & workspace lab',
    unavailable_periods: [],
  },
  {
    room_id: '603',
    name: 'Cube',
    room_type: 'Computer Lab',
    capacity: 30,
    equipment: { computers: 30, projector: 1, whiteboard: 1 },
    description: 'High-performance student computer lab',
    unavailable_periods: [],
  },
  {
    room_id: '604',
    name: 'Victor',
    room_type: 'Classroom',
    capacity: 45,
    equipment: { projector: 1, mic: 1, whiteboard: 2 },
    description: 'Classroom with microphone & AV support',
    unavailable_periods: [],
  },
  {
    room_id: '605',
    name: 'Hero',
    room_type: 'Classroom',
    capacity: 40,
    equipment: { projector: 1, whiteboard: 2 },
    description: 'Standard lecture classroom',
    unavailable_periods: [],
  },
  {
    room_id: '606',
    name: 'Console',
    room_type: 'Meeting Room',
    capacity: 16,
    equipment: { tv_screen: 1, whiteboard: 1 },
    description: 'Discussion and faculty meeting room with TV display',
    unavailable_periods: [],
  },
  {
    room_id: '607',
    name: 'Sandbox',
    room_type: 'Classroom',
    capacity: 50,
    equipment: { projector: 2, mic: 2, whiteboard: 2 },
    description: 'Large interactive lecture classroom',
    unavailable_periods: [],
  },
  {
    room_id: '609',
    name: 'Odyssey',
    room_type: 'Classroom',
    capacity: 45,
    equipment: { projector: 1, whiteboard: 2 },
    description: 'Spacious presentation classroom',
    unavailable_periods: [],
  },
  {
    room_id: '705',
    name: 'Kernel',
    room_type: 'Meeting Room',
    capacity: 35,
    equipment: { projector: 1, whiteboard: 1 },
    description: 'Executive conference & seminar room',
    unavailable_periods: [],
  },
];

/**
 * Known mapping of CMKL room types and descriptions based on campus facilities.
 */
const CMKL_ROOM_METADATA = {
  '601': { type: 'Classroom', desc: 'Lecture classroom' },
  '602': { type: 'Student Lab', desc: 'Lab — where students work' },
  '603': { type: 'Computer Lab', desc: 'Computer Lab (30 PCs)' },
  '604': { type: 'Classroom', desc: 'Lecture classroom' },
  '605': { type: 'Classroom', desc: 'Lecture classroom' },
  '606': { type: 'Meeting Room', desc: 'Meeting room' },
  '607': { type: 'Classroom', desc: 'Large lecture classroom' },
  '609': { type: 'Classroom', desc: 'Lecture classroom' },
  '705': { type: 'Meeting Room', desc: 'Meeting & seminar room' },
};

/**
 * Check if a room is a non-classroom facility that must not be booked.
 * @param {string} roomId - Room identifier.
 * @param {string} roomName - Room display name.
 * @returns {boolean} True if room should be excluded.
 */
export function isNonClassroomFacility(roomId, roomName = '') {
  const idStr = String(roomId || '').trim();
  const nameStr = String(roomName || '').toLowerCase();
  // Room 608 (Bridge): Water filling area & faculty space
  // Room 706 (Apex): Server supercomputer
  return (
    idStr === '608' ||
    idStr === '706' ||
    nameStr.includes('bridge') ||
    nameStr.includes('apex')
  );
}

/**
 * Normalize raw room JSON from backend or storage into a consistent frontend model.
 * @param {Object} raw - Raw room object.
 * @returns {Object} Normalized room object with compatibility getters.
 */
export function normalizeRoom(raw) {
  const roomId = String(raw.room_id || raw.id || '');
  const equipment = raw.equipment || {};
  const periods = raw.unavailable_periods || [];

  // Check if room is currently closed today
  const today = new Date().toISOString().split('T')[0];
  const activeClosure = periods.find(
    (p) => today >= p.start_date && today <= p.end_date
  );

  const meta = CMKL_ROOM_METADATA[roomId] || {};
  const roomType = raw.room_type || meta.type || 'Classroom';
  const description = raw.description || meta.desc || '';

  // Clean room name (e.g. "Pioneer" instead of "Pioneer (601)")
  let cleanName = raw.name || `Room ${roomId}`;
  if (cleanName.includes('(')) {
    cleanName = cleanName.split('(')[0].trim();
  }

  return {
    ...raw,
    id: roomId,
    room_id: roomId,
    name: cleanName,
    room_type: roomType,
    description,
    capacity: Number(raw.capacity) || 0,
    equipment,
    unavailable_periods: periods,
    hasProjector: Boolean(equipment.projector && equipment.projector > 0),
    hasWhiteboard: Boolean(equipment.whiteboard && equipment.whiteboard > 0),
    hasComputers: Boolean(equipment.computers && equipment.computers > 0),
    isAvailable: !activeClosure,
    closureReason: activeClosure ? activeClosure.reason : null,
    activeClosure,
  };
}

/**
 * Sort rooms in ascending natural order by room number.
 * @param {Object[]} rooms - List of room objects.
 * @returns {Object[]} Sorted array.
 */
export function sortRoomsByNumber(rooms) {
  return [...rooms].sort((a, b) => {
    const numA = parseInt(a.room_id || a.id, 10);
    const numB = parseInt(b.room_id || b.id, 10);
    if (!isNaN(numA) && !isNaN(numB)) {
      return numA - numB;
    }
    return String(a.room_id || a.id).localeCompare(String(b.room_id || b.id));
  });
}

/**
 * Load offline rooms from localStorage, filtering out non-classrooms.
 * @returns {Object[]} List of normalized rooms.
 */
function getLocalRooms() {
  const raw = localStorage.getItem(ROOMS_STORAGE_KEY);
  if (!raw) {
    localStorage.setItem(ROOMS_STORAGE_KEY, JSON.stringify(OFFICIAL_SEED_ROOMS));
    return sortRoomsByNumber(OFFICIAL_SEED_ROOMS.map(normalizeRoom));
  }
  try {
    const list = JSON.parse(raw);
    const valid = list.filter((r) => !isNonClassroomFacility(r.room_id || r.id, r.name));
    return sortRoomsByNumber(valid.map(normalizeRoom));
  } catch {
    return sortRoomsByNumber(OFFICIAL_SEED_ROOMS.map(normalizeRoom));
  }
}

/**
 * Save rooms list to localStorage.
 * @param {Object[]} rooms - List of room objects.
 */
function saveLocalRooms(rooms) {
  const valid = rooms.filter((r) => !isNonClassroomFacility(r.room_id || r.id, r.name));
  const sorted = sortRoomsByNumber(valid);
  localStorage.setItem(ROOMS_STORAGE_KEY, JSON.stringify(sorted));
}

/**
 * Fetch all registered rooms from the API Gateway with offline fallback.
 * Strictly filters out non-classroom spaces like Room 608 Bridge.
 * @returns {Promise<Object[]>} Array of normalized room objects sorted by room number.
 */
export async function fetchRooms() {
  try {
    const response = await fetch(`${API_BASE_URL}/rooms`, {
      headers: getAuthHeaders(),
    });
    if (response.ok) {
      const data = await response.json();
      const rawList = data.rooms || [];
      const filtered = rawList.filter(
        (r) => !isNonClassroomFacility(r.room_id || r.id, r.name)
      );
      const list = sortRoomsByNumber(filtered.map(normalizeRoom));
      saveLocalRooms(list);
      return list;
    }
    throw new Error(`Server responded with ${response.status}`);
  } catch {
    return getLocalRooms();
  }
}

/**
 * Create a new room (Staff privilege).
 * @param {Object} roomData - Room creation payload.
 * @returns {Promise<Object>} Created room object.
 */
export async function createRoom(roomData) {
  const cap = Number(roomData.capacity);
  if (isNaN(cap) || cap < 1) {
    throw new Error('Room capacity must be at least 1.');
  }
  if (!roomData.name || !roomData.name.trim()) {
    throw new Error('Room name is required.');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/rooms`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(roomData),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to create room.');
    }
    return normalizeRoom(data.room);
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    // Local fallback creation
    const current = getLocalRooms();
    if (current.some((r) => r.name.toLowerCase() === roomData.name.trim().toLowerCase())) {
      throw new Error(`Room with name '${roomData.name}' already exists.`);
    }
    const newRoom = {
      room_id: roomData.room_id || String(Date.now()).slice(-4),
      name: roomData.name.trim(),
      room_type: roomData.room_type || 'Classroom',
      capacity: cap,
      equipment: roomData.equipment || {},
      unavailable_periods: [],
    };
    current.push(newRoom);
    saveLocalRooms(current);
    return normalizeRoom(newRoom);
  }
}

/**
 * Edit an existing room's capacity, name, or equipment.
 * @param {string} roomId - Identifier of room to update.
 * @param {Object} roomData - Updated fields.
 * @returns {Promise<Object>} Updated room object.
 */
export async function editRoom(roomId, roomData) {
  try {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(roomData),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to edit room.');
    }
    return normalizeRoom(data.room);
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    const current = getLocalRooms();
    const idx = current.findIndex((r) => r.room_id === roomId);
    if (idx === -1) {
      throw new Error(`Room '${roomId}' not found.`);
    }
    current[idx] = { ...current[idx], ...roomData };
    saveLocalRooms(current);
    return normalizeRoom(current[idx]);
  }
}

/**
 * Delete a room from the system (Staff privilege).
 * @param {string} roomId - Identifier of room to delete.
 * @returns {Promise<void>}
 */
export async function deleteRoom(roomId) {
  try {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to delete room.');
    }
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    const current = getLocalRooms().filter((r) => r.room_id !== roomId);
    saveLocalRooms(current);
  }
}

/**
 * Mark a room closed / unavailable for a specific date range with a reason.
 * @param {string} roomId - Identifier of the room.
 * @param {Object} payload - Closure period details.
 * @returns {Promise<Object>} Created unavailability period.
 */
export async function markRoomUnavailable(roomId, payload) {
  if (payload.start_date > payload.end_date) {
    throw new Error('End date cannot be before start date.');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/rooms/${roomId}/unavailable`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Failed to mark room unavailable.');
    }
    return data.unavailable_period;
  } catch (err) {
    if (err.message && !err.message.includes('fetch')) {
      throw err;
    }
    const current = getLocalRooms();
    const room = current.find((r) => r.room_id === roomId);
    if (!room) throw new Error(`Room '${roomId}' not found.`);
    room.unavailable_periods = room.unavailable_periods || [];
    room.unavailable_periods.push(payload);
    saveLocalRooms(current);
    return payload;
  }
}

/**
 * Reset local rooms and storage to official CMKL campus classrooms.
 */
export function resetRoomsToSeed() {
  localStorage.setItem(ROOMS_STORAGE_KEY, JSON.stringify(OFFICIAL_SEED_ROOMS));
  return OFFICIAL_SEED_ROOMS.map(normalizeRoom);
}