// file: src/components/ReservationModal.jsx
// purpose: Modal dialog for reserving a classroom or editing an existing reservation
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import { createReservation, editReservation, SEMESTER_START, SEMESTER_END } from '../api/reservationApi';
import ModalShell from './ModalShell';
import { LABEL, INPUT, BTN_PRIMARY, BTN_SECONDARY, ERROR_BOX } from '../utils/styles';

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
  const rawRep = reservation?.repetition;
  const initialRepetition =
    rawRep === 'Once' || rawRep === 'None' ? 'Once' : 'Weekly';
  const [repetition, setRepetition] = useState(initialRepetition);

  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Find the selected room object to inspect capacity
  const targetRoom = (rooms.length > 0 ? rooms.find((r) => r.room_id === selectedRoomId) : null) || room;
  const roomCapacity = targetRoom?.capacity || 40;

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

    const isSingleSlot = repetition === 'Once' || repetition === 'None';
    const payload = {
      competency: competency.trim().toUpperCase(),
      room_id: selectedRoomId,
      group_size: groupNum,
      start_date: date,
      end_date: isSingleSlot ? date : SEMESTER_END,
      start_time: startTime,
      end_time: endTime,
      repetition: isSingleSlot ? 'Once' : 'Weekly',
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

  const roomLabel = targetRoom?.room_id || selectedRoomId;
  const title = isEditing
    ? `Edit ${reservation.competency}, room ${reservation.room_id}`
    : `Book room ${roomLabel}${targetRoom?.name ? ` (${targetRoom.name})` : ''}`;

  return (
    <ModalShell title={title} onClose={onClose} size="lg">
      {showSuccess ? (
        <p className="p-5 text-sm text-slate-700 dark:text-slate-200 tabular-nums">
          {isEditing ? 'Saved.' : 'Booked.'} {competency.toUpperCase()} in room {roomLabel},{' '}
          {startTime}–{endTime}.
        </p>
      ) : (
        <form id="reservation-form" onSubmit={handleSubmit} className="p-5 space-y-4">
          {errorMessage && <div className={ERROR_BOX}>{errorMessage}</div>}

          {rooms.length > 0 && !room && (
            <div>
              <label htmlFor="reservation-room-select" className={LABEL}>
                Room
              </label>
              <select
                id="reservation-room-select"
                value={selectedRoomId}
                onChange={(e) => setSelectedRoomId(e.target.value)}
                className={INPUT}
              >
                {[...rooms]
                  .sort((a, b) => parseInt(a.room_id || a.id, 10) - parseInt(b.room_id || b.id, 10))
                  .map((r) => (
                    <option key={r.room_id || r.id} value={r.room_id || r.id}>
                      {r.room_id || r.id} {r.name} ({r.capacity} seats)
                    </option>
                  ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="reservation-competency" className={LABEL}>
                Course code
              </label>
              <input
                id="reservation-competency"
                type="text"
                required
                value={competency}
                onChange={(e) => setCompetency(e.target.value)}
                placeholder="e.g. SEN-201"
                className={`${INPUT} uppercase`}
              />
            </div>

            <div>
              <label htmlFor="reservation-group-size" className={LABEL}>
                Students <span className="font-normal text-slate-500">(max {roomCapacity})</span>
              </label>
              <input
                id="reservation-group-size"
                type="number"
                required
                min="1"
                max={roomCapacity}
                value={groupSize}
                onChange={(e) => setGroupSize(e.target.value)}
                className={INPUT}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="reservation-date" className={LABEL}>
                {repetition === 'Weekly' ? 'First class' : 'Date'}
              </label>
              <input
                id="reservation-date"
                type="date"
                required
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className={INPUT}
              />
            </div>

            <div>
              <label htmlFor="reservation-repetition" className={LABEL}>
                Repeats
              </label>
              <select
                id="reservation-repetition"
                value={repetition}
                onChange={(e) => setRepetition(e.target.value)}
                className={INPUT}
              >
                <option value="Weekly">Weekly until {SEMESTER_END}</option>
                <option value="Once">Once</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="reservation-start-time" className={LABEL}>
                Start
              </label>
              <input
                id="reservation-start-time"
                type="time"
                required
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className={INPUT}
              />
            </div>

            <div>
              <label htmlFor="reservation-end-time" className={LABEL}>
                End
              </label>
              <input
                id="reservation-end-time"
                type="time"
                required
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className={INPUT}
              />
            </div>
          </div>

          <div className="pt-1 flex justify-end gap-2">
            <button
              id="modal-cancel"
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className={BTN_SECONDARY}
            >
              Cancel
            </button>
            <button
              id="modal-confirm"
              type="submit"
              disabled={isLoading}
              className={`${BTN_PRIMARY} min-w-[110px]`}
            >
              {isLoading ? 'Checking…' : isEditing ? 'Save changes' : 'Book'}
            </button>
          </div>
        </form>
      )}
    </ModalShell>
  );
}
