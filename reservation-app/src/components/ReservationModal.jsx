// file: src/components/ReservationModal.jsx
// purpose: Modal dialog for reserving a classroom or editing an existing reservation
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import { X, Calendar, CheckCircle2, AlertCircle } from 'lucide-react';

import { createReservation, editReservation, SEMESTER_START, SEMESTER_END } from '../api/reservationApi';

/**
 * Modal dialog for creating or updating a room reservation.
 * @param {Object} props
 * @param {Object|null} props.room - The room to reserve (for new booking).
 * @param {Object|null} [props.reservation] - Existing reservation when in edit mode.
 * @param {Object[]} [props.rooms] - All rooms list for selection dropdown if room not locked.
 * @param {function} props.onClose - Dismiss callback.
 * @param {function} props.onSuccess - Callback invoked after save.
 * @returns {JSX.Element|null} The modal component.
 */
export default function ReservationModal({
  room,
  reservation,
  rooms = [],
  onClose,
  onSuccess,
}) {
  const isEditing = Boolean(reservation);

  const initialRoomId = reservation?.room_id || room?.room_id || room?.id || (rooms[0] ? rooms[0].room_id : '');
  const [selectedRoomId, setSelectedRoomId] = useState(initialRoomId);
  const [competency, setCompetency] = useState(reservation ? reservation.competency : '');
  const [groupSize, setGroupSize] = useState(reservation ? String(reservation.group_size) : '');
  const [date, setDate] = useState(reservation ? reservation.start_date : '2026-10-12');
  const [startTime, setStartTime] = useState(reservation ? reservation.start_time : '10:00');
  const [endTime, setEndTime] = useState(reservation ? reservation.end_time : '12:00');
  const [repetition, setRepetition] = useState(reservation?.repetition || 'Weekly');

  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Find the selected room object to inspect capacity
  const targetRoom = (rooms.length > 0 ? rooms.find((r) => r.room_id === selectedRoomId) : null) || room;
  const roomCapacity = targetRoom?.capacity || 40;

  /**
   * Submit the reservation form.
   * @param {React.FormEvent} e - Form event.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (!competency.trim()) {
      setErrorMessage('Competency / Course code is required (e.g. SEN-201).');
      return;
    }

    const groupNum = parseInt(groupSize, 10);
    if (isNaN(groupNum) || groupNum < 1) {
      setErrorMessage('Group size must be at least 1.');
      return;
    }

    if (groupNum > roomCapacity) {
      setErrorMessage(
        `Group size (${groupNum}) exceeds room capacity (${roomCapacity} seats).`
      );
      return;
    }

    if (startTime >= endTime) {
      setErrorMessage('End time must be strictly after start time.');
      return;
    }

    if (date < SEMESTER_START || date > SEMESTER_END) {
      setErrorMessage(
        `Date must fall within semester period (${SEMESTER_START} to ${SEMESTER_END}).`
      );
      return;
    }

    setIsLoading(true);

    const payload = {
      competency: competency.trim().toUpperCase(),
      room_id: selectedRoomId,
      group_size: groupNum,
      start_date: date,
      end_date: SEMESTER_END,
      start_time: startTime,
      end_time: endTime,
      repetition,
    };

    try {
      if (isEditing) {
        await editReservation(reservation.reservation_id, payload);
      } else {
        await createReservation(payload);
      }
      setShowSuccess(true);
      setTimeout(() => {
        setShowSuccess(false);
        onSuccess();
        onClose();
      }, 1200);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to submit reservation.');
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
            <Calendar className="w-5 h-5" />
            <h2 className="text-xl font-bold">
              {isEditing
                ? `Edit Reservation (${reservation.competency} — Room ${reservation.room_id})`
                : `Reserve Room ${targetRoom?.room_id || selectedRoomId}${targetRoom?.name ? ` — ${targetRoom.name}` : ''}`}
            </h2>
          </div>
          <button
            id="modal-close"
            onClick={onClose}
            className="text-blue-100 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success View */}
        {showSuccess ? (
          <div className="p-8 flex flex-col items-center justify-center text-center">
            <CheckCircle2 className="w-16 h-16 text-green-500 mb-3 animate-bounce" />
            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
              {isEditing ? 'Reservation Updated!' : 'Reservation Confirmed!'}
            </h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm">
              {competency.toUpperCase()} booked in Room {targetRoom?.room_id || selectedRoomId} ({targetRoom?.name || ''}) for {startTime} - {endTime}.
            </p>
          </div>
        ) : (
          /* Form View */
          <form id="reservation-form" onSubmit={handleSubmit} className="p-6 space-y-4">
            {errorMessage && (
              <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 rounded-lg text-sm flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Room selection (if multiple rooms available) */}
            {rooms.length > 0 && !room && (
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Select Classroom *
                </label>
                <select
                  id="reservation-room-select"
                  value={selectedRoomId}
                  onChange={(e) => setSelectedRoomId(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  {[...rooms]
                    .sort((a, b) => parseInt(a.room_id || a.id, 10) - parseInt(b.room_id || b.id, 10))
                    .map((r) => (
                      <option key={r.room_id || r.id} value={r.room_id || r.id}>
                        Room {r.room_id || r.id} — {r.name} (Seats: {r.capacity})
                      </option>
                    ))}
                </select>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Competency / Course *
                </label>
                <input
                  id="reservation-competency"
                  type="text"
                  required
                  value={competency}
                  onChange={(e) => setCompetency(e.target.value)}
                  placeholder="e.g. SEN-201"
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none uppercase"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Group Size * (Max {roomCapacity})
                </label>
                <input
                  id="reservation-group-size"
                  type="number"
                  required
                  min="1"
                  max={roomCapacity}
                  value={groupSize}
                  onChange={(e) => setGroupSize(e.target.value)}
                  placeholder={`Max: ${roomCapacity}`}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Date *
                </label>
                <input
                  id="reservation-date"
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Repetition
                </label>
                <select
                  id="reservation-repetition"
                  value={repetition}
                  onChange={(e) => setRepetition(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  <option value="Weekly">Weekly (Semester)</option>
                  <option value="None">Single Slot</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Start Time *
                </label>
                <input
                  id="reservation-start-time"
                  type="time"
                  required
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                  End Time *
                </label>
                <input
                  id="reservation-end-time"
                  type="time"
                  required
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-3">
              <button
                id="modal-cancel"
                type="button"
                onClick={onClose}
                disabled={isLoading}
                className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              >
                Cancel
              </button>
              <button
                id="modal-confirm"
                type="submit"
                disabled={isLoading}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm disabled:opacity-60 flex items-center justify-center min-w-[110px]"
              >
                {isLoading ? 'Checking...' : isEditing ? 'Save Changes' : 'Confirm'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
