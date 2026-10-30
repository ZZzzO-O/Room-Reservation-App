// file: src/components/RoomModal.jsx
// purpose: Modal dialog for creating and editing room details and categories (Staff privilege)
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import { createRoom, editRoom } from '../api/roomApi';
import ModalShell from './ModalShell';
import { LABEL, INPUT, BTN_PRIMARY, BTN_SECONDARY, ERROR_BOX } from '../utils/styles';

const ROOM_TYPES = ['Classroom', 'Lab', 'Computer Lab', 'Meeting Room'];

/**
 * Dialog for adding a new room or updating an existing room's attributes.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is visible.
 * @param {Object|null} props.room - Existing room to edit, or null when creating.
 * @param {Object[]} props.reservations - Existing reservations for room capacity validation.
 * @param {function} props.onClose - Callback to close modal.
 * @param {function} props.onSuccess - Callback invoked after save.
 * @returns {JSX.Element|null} The room modal component.
 */
export default function RoomModal({
  isOpen,
  room,
  reservations = [],
  onClose,
  onSuccess,
}) {
  const isEditing = Boolean(room);
  const roomId = room?.room_id || room?.id;
  const largestReservedGroup = isEditing
    ? reservations.reduce(
        (largest, reservation) =>
          String(reservation.room_id) === String(roomId)
            ? Math.max(largest, Number(reservation.group_size) || 0)
            : largest,
        0
      )
    : 0;

  const [roomIdInput, setRoomIdInput] = useState('');
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
    if (
      isEditing &&
      capNum < room.capacity &&
      capNum < largestReservedGroup
    ) {
      setErrorMessage(
        `Capacity cannot be reduced below ${largestReservedGroup} seats because this room has an existing reservation for that group size.`
      );
      return;
    }
    if (!name.trim()) {
      setErrorMessage('Room name is required.');
      return;
    }
    if (!isEditing && !roomIdInput.trim()) {
      setErrorMessage('Room ID is required.');
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
          room_id: roomIdInput.trim(),
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

  const equipmentFields = [
    { id: 'room-modal-projector', label: 'Projectors', value: projector, set: setProjector },
    { id: 'room-modal-whiteboard', label: 'Whiteboards', value: whiteboard, set: setWhiteboard },
    { id: 'room-modal-computers', label: 'Computers', value: computers, set: setComputers },
    { id: 'room-modal-mic', label: 'Microphones', value: mic, set: setMic },
    { id: 'room-modal-tv', label: 'TV screens', value: tvScreen, set: setTvScreen },
  ];

  return (
    <ModalShell
      title={isEditing ? `Edit room ${room.room_id || room.id}` : 'Add room'}
      onClose={onClose}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        {errorMessage && <div className={ERROR_BOX}>{errorMessage}</div>}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {!isEditing && (
            <div>
              <label htmlFor="room-modal-id" className={LABEL}>
                Room ID
              </label>
              <input
                id="room-modal-id"
                type="text"
                required
                value={roomIdInput}
                onChange={(e) => setRoomIdInput(e.target.value)}
                placeholder="e.g. 610"
                className={INPUT}
              />
            </div>
          )}
          <div>
            <label htmlFor="room-modal-name" className={LABEL}>
              Name
            </label>
            <input
              id="room-modal-name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Pioneer"
              className={INPUT}
            />
          </div>

          <div>
            <label htmlFor="room-modal-type" className={LABEL}>
              Type
            </label>
            <select
              id="room-modal-type"
              value={roomType}
              onChange={(e) => setRoomType(e.target.value)}
              className={INPUT}
            >
              {ROOM_TYPES.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="sm:w-1/2 sm:pr-2">
          <label htmlFor="room-modal-capacity" className={LABEL}>
            Seats
          </label>
          <input
            id="room-modal-capacity"
            type="number"
            required
            min="1"
            value={capacity}
            onChange={(e) => setCapacity(e.target.value)}
            placeholder="e.g. 40"
            className={INPUT}
          />
          {largestReservedGroup > 0 && (
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              At least {largestReservedGroup} seats are needed for existing reservations.
            </p>
          )}
        </div>

        <fieldset className="pt-3 border-t border-slate-200 dark:border-slate-700">
          <legend className="text-sm font-medium text-slate-700 dark:text-slate-300 pr-2">
            Equipment
          </legend>
          <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {equipmentFields.map((field) => (
              <div key={field.id}>
                <label htmlFor={field.id} className="block text-xs text-slate-600 dark:text-slate-400 mb-1">
                  {field.label}
                </label>
                <input
                  id={field.id}
                  type="number"
                  min="0"
                  value={field.value}
                  onChange={(e) => field.set(Math.max(0, parseInt(e.target.value, 10) || 0))}
                  className={INPUT}
                />
              </div>
            ))}
          </div>
        </fieldset>

        <div className="pt-1 flex justify-end gap-2">
          <button type="button" onClick={onClose} className={BTN_SECONDARY}>
            Cancel
          </button>
          <button id="room-modal-save" type="submit" disabled={isLoading} className={BTN_PRIMARY}>
            {isLoading ? 'Saving…' : isEditing ? 'Save changes' : 'Add room'}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}
