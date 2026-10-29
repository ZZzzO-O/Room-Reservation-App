// file: src/components/UnavailabilityModal.jsx
// purpose: Modal dialog for marking a classroom unavailable for a date range with reason
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import { markRoomUnavailable } from '../api/roomApi';
import ModalShell from './ModalShell';
import { LABEL, INPUT, BTN_PRIMARY, BTN_SECONDARY, ERROR_BOX } from '../utils/styles';

/**
 * Dialog enabling staff members to close a room during maintenance or renovation.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is active.
 * @param {Object|null} props.room - Room to mark unavailable.
 * @param {function} props.onClose - Dismiss callback.
 * @param {function} props.onSuccess - Callback after marking unavailable.
 * @returns {JSX.Element|null} The unavailability modal.
 */
export default function UnavailabilityModal({ isOpen, room, onClose, onSuccess }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('Renovation');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  if (!isOpen || !room) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');

    if (startDate > endDate) {
      setErrorMessage('End date cannot be before start date.');
      return;
    }

    setIsLoading(true);
    try {
      await markRoomUnavailable(room.room_id || room.id, {
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim() || 'Unavailable',
      });
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to mark room unavailable.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ModalShell title={`Close room ${room.room_id || room.id}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No one can book {room.name || 'this room'} between these dates. Existing bookings in
          the range are not cancelled automatically.
        </p>

        {errorMessage && <div className={ERROR_BOX}>{errorMessage}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="unavail-start-date" className={LABEL}>
              From
            </label>
            <input
              id="unavail-start-date"
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className={INPUT}
            />
          </div>
          <div>
            <label htmlFor="unavail-end-date" className={LABEL}>
              To (inclusive)
            </label>
            <input
              id="unavail-end-date"
              type="date"
              required
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className={INPUT}
            />
          </div>
        </div>

        <div>
          <label htmlFor="unavail-reason" className={LABEL}>
            Reason
          </label>
          <input
            id="unavail-reason"
            type="text"
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Renovation, projector repair"
            className={INPUT}
          />
        </div>

        <div className="pt-1 flex justify-end gap-2">
          <button type="button" onClick={onClose} className={BTN_SECONDARY}>
            Cancel
          </button>
          <button id="unavail-save" type="submit" disabled={isLoading} className={BTN_PRIMARY}>
            {isLoading ? 'Saving…' : 'Close room'}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}
