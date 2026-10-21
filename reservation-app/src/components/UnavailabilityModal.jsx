// file: src/components/UnavailabilityModal.jsx
// purpose: Modal dialog for marking a classroom unavailable for a date range with reason
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import { X, CalendarX, AlertCircle } from 'lucide-react';

import { markRoomUnavailable } from '../api/roomApi';

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

  /**
   * Submit unavailability period to backend.
   * @param {React.FormEvent} e - Form event.
   */
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-200 dark:border-slate-700">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-600 to-rose-600 px-6 py-4 text-white flex justify-between items-center">
          <div className="flex items-center gap-2">
            <CalendarX className="w-5 h-5" />
            <h2 className="text-xl font-bold">Mark Room Unavailable</h2>
          </div>
          <button
            onClick={onClose}
            className="text-amber-100 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Close <span className="font-semibold text-slate-900 dark:text-white">{room.name}</span> for reservations during a scheduled maintenance or renovation window.
          </p>

          {errorMessage && (
            <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 rounded-lg text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Start Date *
              </label>
              <input
                id="unavail-start-date"
                type="date"
                required
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                End Date *
              </label>
              <input
                id="unavail-end-date"
                type="date"
                required
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Reason for Unavailability *
            </label>
            <input
              id="unavail-reason"
              type="text"
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Renovation, Equipment Repair"
              className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-amber-500 outline-none"
            />
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
              id="unavail-save"
              type="submit"
              disabled={isLoading}
              className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm disabled:opacity-60"
            >
              {isLoading ? 'Saving...' : 'Mark Closed'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
