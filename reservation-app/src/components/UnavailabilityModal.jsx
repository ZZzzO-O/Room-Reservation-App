// file: src/components/UnavailabilityModal.jsx
// purpose: Modal dialog for marking a classroom unavailable for a date range with reason
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import {
  markRoomUnavailable,
  removeRoomUnavailable,
  updateRoomUnavailable,
} from '../api/roomApi';
import ModalShell from './ModalShell';
import {
  LABEL,
  INPUT,
  BTN_PRIMARY,
  BTN_SECONDARY,
  BTN_DANGER,
  ERROR_BOX,
} from '../utils/styles';

/**
 * Dialog enabling staff members to close a room during maintenance or renovation.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is active.
 * @param {Object|null} props.room - Room to mark unavailable.
 * @param {Object[]} props.room.unavailable_periods - Existing closures.
 * @param {function} props.onClose - Dismiss callback.
 * @param {function} props.onSuccess - Callback after marking unavailable.
 * @returns {JSX.Element|null} The unavailability modal.
 */
export default function UnavailabilityModal({ isOpen, room, onClose, onSuccess }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [reason, setReason] = useState('Renovation');
  const [editingPeriodId, setEditingPeriodId] = useState(null);
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
      const payload = {
        start_date: startDate,
        end_date: endDate,
        reason: reason.trim() || 'Unavailable',
      };
      if (editingPeriodId === null) {
        await markRoomUnavailable(room.room_id || room.id, payload);
      } else {
        await updateRoomUnavailable(
          room.room_id || room.id,
          editingPeriodId,
          payload
        );
      }
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMessage(
        err.message ||
          (editingPeriodId === null
            ? 'Failed to mark room unavailable.'
            : 'Failed to update room closure.')
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditPeriod = (period) => {
    setEditingPeriodId(period.period_id);
    setStartDate(period.start_date);
    setEndDate(period.end_date);
    setReason(period.reason || 'Unavailable');
    setErrorMessage('');
  };

  const handleCancelEdit = () => {
    setEditingPeriodId(null);
    setStartDate('');
    setEndDate('');
    setReason('Renovation');
    setErrorMessage('');
  };

  const handleRemovePeriod = async (period) => {
    setErrorMessage('');
    setIsLoading(true);
    try {
      await removeRoomUnavailable(room.room_id || room.id, period.period_id);
      if (editingPeriodId === period.period_id) {
        handleCancelEdit();
      }
      onSuccess();
      onClose();
    } catch (err) {
      setErrorMessage(err.message || 'Failed to remove room closure.');
    } finally {
      setIsLoading(false);
    }
  };

  const periods = room.unavailable_periods || [];

  return (
    <ModalShell title={`Close room ${room.room_id || room.id}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="p-5 space-y-4">
        <p className="text-sm text-slate-600 dark:text-slate-300">
          No one can book {room.name || 'this room'} between these dates. If a booking already
          falls in this range, move or cancel it before closing the room.
        </p>

        {periods.length > 0 && (
          <section className="space-y-2" aria-label="Scheduled closures">
            <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Scheduled closures
            </h3>
            {periods.map((period) => (
              <div
                key={period.period_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-slate-200 dark:border-slate-700 p-3"
              >
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  <span className="font-medium">{period.reason || 'Unavailable'}</span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">
                    {period.start_date} to {period.end_date}
                  </span>
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleEditPeriod(period)}
                    disabled={isLoading}
                    className={BTN_SECONDARY}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRemovePeriod(period)}
                    disabled={isLoading}
                    className={BTN_DANGER}
                  >
                    Remove
                  </button>
                </div>
              </div>
            ))}
          </section>
        )}

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
          {editingPeriodId !== null && (
            <button
              type="button"
              onClick={handleCancelEdit}
              disabled={isLoading}
              className={BTN_SECONDARY}
            >
              Cancel edit
            </button>
          )}
          <button id="unavail-save" type="submit" disabled={isLoading} className={BTN_PRIMARY}>
            {isLoading
              ? 'Saving…'
              : editingPeriodId === null
                ? 'Close room'
                : 'Save changes'}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}
