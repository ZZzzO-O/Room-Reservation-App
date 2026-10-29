// file: src/components/DeleteConfirmModal.jsx
// purpose: Modal dialog implementing the Delete Reservation Activity Diagram workflow
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState } from 'react';

import { deleteReservation } from '../api/reservationApi';
import ModalShell from './ModalShell';
import { BTN_SECONDARY, BTN_DANGER, ERROR_BOX } from '../utils/styles';

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

  return (
    <ModalShell title="Delete reservation" onClose={onClose}>
      <div className="p-5 space-y-4">
        {isDeleted ? (
          <p className="py-4 text-sm text-slate-700 dark:text-slate-200">
            Deleted. The slot is free for other bookings.
          </p>
        ) : (
          <>
            {errorMessage ? (
              <div className={ERROR_BOX}>{errorMessage}</div>
            ) : (
              <>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {reservation.repetition === 'Weekly'
                    ? 'This removes every weekly slot in the series. It can’t be undone.'
                    : 'This can’t be undone.'}
                </p>
                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm tabular-nums border-y border-slate-200 dark:border-slate-700 py-3">
                  <dt className="text-slate-500 dark:text-slate-400">Course</dt>
                  <dd className="font-semibold text-slate-900 dark:text-white">{reservation.competency}</dd>
                  <dt className="text-slate-500 dark:text-slate-400">Room</dt>
                  <dd className="text-slate-900 dark:text-white">{reservation.room_id}</dd>
                  <dt className="text-slate-500 dark:text-slate-400">When</dt>
                  <dd className="text-slate-900 dark:text-white">
                    {reservation.start_date}, {reservation.start_time}–{reservation.end_time}
                  </dd>
                  <dt className="text-slate-500 dark:text-slate-400">Group</dt>
                  <dd className="text-slate-900 dark:text-white">{reservation.group_size} students</dd>
                </dl>
              </>
            )}

            <div className="flex justify-end gap-2">
              <button
                id="delete-cancel-btn"
                type="button"
                onClick={onClose}
                disabled={isDeleting}
                className={BTN_SECONDARY}
              >
                {errorMessage ? 'Close' : 'Keep it'}
              </button>
              {!errorMessage && (
                <button
                  id="delete-confirm-btn"
                  type="button"
                  onClick={handleConfirm}
                  disabled={isDeleting}
                  className={BTN_DANGER}
                >
                  {isDeleting ? 'Deleting…' : 'Delete reservation'}
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </ModalShell>
  );
}
