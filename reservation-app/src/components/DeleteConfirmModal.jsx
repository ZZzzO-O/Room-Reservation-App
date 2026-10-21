// file: src/components/DeleteConfirmModal.jsx
// purpose: Modal dialog implementing the Delete Reservation Activity Diagram workflow
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';
import { AlertTriangle, X, Trash2, CheckCircle2 } from 'lucide-react';

import { deleteReservation } from '../api/reservationApi';

/**
 * Confirmation dialog for cancelling a reservation, implementing Lab 4's Activity Diagram.
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether modal is active.
 * @param {Object|null} props.reservation - The reservation selected for deletion.
 * @param {function} props.onClose - Callback when deletion is cancelled.
 * @param {function} props.onSuccess - Callback after successful deletion.
 * @returns {JSX.Element|null} The modal component.
 */
export default function DeleteConfirmModal({ isOpen, reservation, onClose, onSuccess }) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isDeleted, setIsDeleted] = useState(false);

  if (!isOpen || !reservation) return null;

  /**
   * Execute deletion upon user clicking confirm.
   */
  const handleConfirm = async () => {
    setErrorMessage('');
    setIsDeleting(true);

    try {
      await deleteReservation(reservation.reservation_id);
      setIsDeleted(true);
      setTimeout(() => {
        setIsDeleted(false);
        onSuccess();
        onClose();
      }, 1000);
    } catch (err) {
      setErrorMessage(
        err.message || 'The reservation could not be found or has already been deleted.'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  /**
   * Explicit cancel action: keep reservation unchanged.
   */
  const handleCancel = () => {
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-200 dark:border-slate-700">
        {/* Header */}
        <div className="bg-red-600 px-6 py-4 text-white flex justify-between items-center">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            <h2 className="text-lg font-bold">Delete Reservation</h2>
          </div>
          <button
            onClick={handleCancel}
            className="text-red-100 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          {isDeleted ? (
            <div className="py-6 flex flex-col items-center justify-center text-center">
              <CheckCircle2 className="w-12 h-12 text-green-500 mb-2" />
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Reservation Deleted
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                The slot has been freed for other bookings.
              </p>
            </div>
          ) : (
            <>
              {errorMessage ? (
                <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800/60 text-red-700 dark:text-red-300 rounded-lg text-sm">
                  {errorMessage}
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-slate-600 dark:text-slate-300">
                    Are you sure you want to permanently delete this classroom reservation?
                  </p>

                  <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-700 text-sm space-y-1">
                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                      Competency: {reservation.competency}
                    </p>
                    <p className="text-slate-600 dark:text-slate-400">
                      Room: {reservation.room_id} | Seats: {reservation.group_size}
                    </p>
                    <p className="text-slate-600 dark:text-slate-400">
                      Date: {reservation.start_date} ({reservation.start_time} - {reservation.end_time})
                    </p>
                  </div>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-3">
                <button
                  id="delete-cancel-btn"
                  type="button"
                  onClick={handleCancel}
                  disabled={isDeleting}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 text-sm font-medium rounded-lg hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                  Cancel
                </button>
                {!errorMessage && (
                  <button
                    id="delete-confirm-btn"
                    type="button"
                    onClick={handleConfirm}
                    disabled={isDeleting}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm disabled:opacity-60 flex items-center gap-1.5"
                  >
                    <Trash2 className="w-4 h-4" />
                    {isDeleting ? 'Deleting...' : 'Confirm Delete'}
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
