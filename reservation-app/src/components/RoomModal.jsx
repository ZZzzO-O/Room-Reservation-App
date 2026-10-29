// file: src/components/RoomModal.jsx
// purpose: Modal dialog for creating and editing room details and categories (Staff privilege)
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import { X, Building2, AlertCircle } from 'lucide-react';

import { createRoom, editRoom } from '../api/roomApi';

/**
 * Dialog for adding a new room or updating an existing room's attributes.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible.
 * @param {Object|null} props.room - Existing room to edit, or null when creating.
 * @param {function} props.onClose - Callback to close modal.
 * @param {function} props.onSuccess - Callback invoked after save.
 * @returns {JSX.Element|null} The room modal component.
 */
export default function RoomModal({ isOpen, room, onClose, onSuccess }) {
  const isEditing = Boolean(room);

  const [name, setName] = useState(room ? room.name : '');
  const [roomType, setRoomType] = useState(room ? room.room_type || 'Classroom' : 'Classroom');
  const [capacity, setCapacity] = useState(room ? String(room.capacity) : '');
  const [projector, setProjector] = useState(room?.equipment?.projector || 0);
  const [whiteboard, setWhiteboard] = useState(room?.equipment?.whiteboard || 0);
  const [computers, setComputers] = useState(room?.equipment?.computers || 0);
  const [mic, setMic] = useState(room?.equipment?.mic || 0);
  const [tvScreen, setTvScreen] = useState(room?.equipment?.tv_screen || 0);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen) return null;

  /**
   * Submit create or update request.
   * @param {React.FormEvent} e - Form submission event.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    const capNum = parseInt(capacity, 10);
    if (isNaN(capNum)) {
      setErrorMessage('Capacity is required.');
      return;
    }
    if (capNum < 1) {
      setErrorMessage('Capacity must be at least 1.');
      return;
    }
    if (!name.trim()) {
      setErrorMessage('Room name is required.');
      return;
    }

    const equipment = {};
    if (projector > 0) equipment.projector = projector;
    if (whiteboard > 0) equipment.whiteboard = whiteboard;
    if (computers > 0) equipment.computers = computers;
    if (mic > 0) equipment.mic = mic;
    if (tvScreen > 0) equipment.tv_screen = tvScreen;

    setIsLoading(true);
    try {
      if (isEditing) {
        await editRoom(room.room_id || room.id, {
          name: name.trim(),
          room_type: roomType,
          capacity: capNum,
          equipment,
        });
      } else {
        await createRoom({
          name: name.trim(),
          room_type: roomType,
          capacity: capNum,
          equipment,
        });
      }
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to save room.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200 dark:border-slate-700 my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 text-white flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            <h2 className="text-xl font-bold">
              {isEditing ? `Edit ${room.name}` : 'Add New Classroom'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-blue-100 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 rounded-lg text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Room Name *
              </label>
              <input
                id="room-modal-name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Pioneer, Voyager"
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Space Category *
              </label>
              <select
                id="room-modal-type"
                value={roomType}
                onChange={(e) => setRoomType(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="Classroom">Classroom</option>
                <option value="Lab">Lab</option>
                <option value="Computer Lab">Computer Lab</option>
                <option value="Meeting Room">Meeting Room</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Seating Capacity *
            </label>
            <input
              id="room-modal-capacity"
              type="number"
              required
              min="1"
              value={capacity}
              onChange={(e) => setCapacity(e.target.value)}
              placeholder="e.g. 40"
              className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          {/* Equipment Fields */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
              Available Equipment
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-slate-50 dark:bg-slate-900/50 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
              <div>
                <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">
                  Projectors
                </label>
                <input
                  type="number"
                  min="0"
                  value={projector}
                  onChange={(e) => setProjector(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className="w-full px-2 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">
                  Whiteboards
                </label>
                <input
                  type="number"
                  min="0"
                  value={whiteboard}
                  onChange={(e) => setWhiteboard(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className="w-full px-2 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">
                  Computers
                </label>
                <input
                  type="number"
                  min="0"
                  value={computers}
                  onChange={(e) => setComputers(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className="w-full px-2 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">
                  Microphones
                </label>
                <input
                  type="number"
                  min="0"
                  value={mic}
                  onChange={(e) => setMic(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className="w-full px-2 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-sm text-slate-900 dark:text-white"
                />
              </div>

              <div>
                <label className="text-xs text-slate-600 dark:text-slate-400 block mb-1">
                  TV Screens
                </label>
                <input
                  type="number"
                  min="0"
                  value={tvScreen}
                  onChange={(e) => setTvScreen(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className="w-full px-2 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded text-sm text-slate-900 dark:text-white"
                />
              </div>
            </div>
          </div>

          <div className="pt-3 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
            >
              Cancel
            </button>
            <button
              id="room-modal-save"
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm disabled:opacity-60"
            >
              {isLoading ? 'Saving...' : 'Save Room'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
