// file: src/pages/MyReservationsPage.jsx
// purpose: View, search, edit, and cancel classroom reservations
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import { Search } from 'lucide-react';

import DeleteConfirmModal from '../components/DeleteConfirmModal';
import ReservationModal from '../components/ReservationModal';
import { INPUT, BTN_PRIMARY } from '../utils/styles';

const CARD_ACTION =
  'px-3 py-2 rounded-md text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors';

/**
 * Reservations page displaying scheduled classes and bookings.
 * @param {Object} props
 * @param {Object[]} props.reservations - Active reservations.
 * @param {Object[]} props.rooms - Catalog of rooms.
 * @param {function} props.onRefresh - Callback to refetch reservations after edits.
 * @param {function} props.onNavigateToBrowse - Handler to return to browse.
 * @returns {JSX.Element} The MyReservationsPage component.
 */
export default function MyReservationsPage({
  reservations,
  rooms,
  onRefresh,
  onNavigateToBrowse,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedResForDelete, setSelectedResForDelete] = useState(null);
  const [selectedResForEdit, setSelectedResForEdit] = useState(null);
  const [isNewBookingModalOpen, setIsNewBookingModalOpen] = useState(false);

  /**
   * Filter reservations by competency code, room ID, or start date.
   */
  const filteredReservations = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return reservations;
    return reservations.filter((r) => {
      const comp = (r.competency || '').toLowerCase();
      const rm = String(r.room_id || '').toLowerCase();
      const dt = (r.start_date || '').toLowerCase();
      return comp.includes(q) || rm.includes(q) || dt.includes(q);
    });
  }, [reservations, searchQuery]);

  return (
    <div className="space-y-5">
      <header className="flex flex-col sm:flex-row justify-between sm:items-end gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Reservations
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 tabular-nums">
            {reservations.length} {reservations.length === 1 ? 'booking' : 'bookings'} this semester
          </p>
        </div>

        <button
          id="btn-new-reservation"
          onClick={() => setIsNewBookingModalOpen(true)}
          className={`${BTN_PRIMARY} shrink-0`}
        >
          New reservation
        </button>
      </header>

      <div className="relative max-w-md">
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none"
          aria-hidden="true"
        />
        <input
          id="search-reservations"
          type="search"
          aria-label="Search reservations"
          placeholder="Course code, room number or date"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={`${INPUT} pl-9`}
        />
      </div>

      {filteredReservations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredReservations.map((res) => {
            const matchedRoom = rooms.find((r) => String(r.room_id || r.id) === String(res.room_id));
            const repeats = res.repetition || 'Weekly';

            return (
              <article
                key={res.reservation_id}
                className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 flex flex-col"
              >
                <div className="p-4 flex-grow">
                  <div className="flex items-baseline justify-between gap-3 mb-3">
                    <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                      {res.competency}
                    </h2>
                    <span className="text-xs text-slate-400 font-mono">{res.reservation_id}</span>
                  </div>

                  <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm tabular-nums">
                    <dt className="text-slate-500 dark:text-slate-400">Room</dt>
                    <dd className="text-slate-900 dark:text-white">
                      {res.room_id}
                      {matchedRoom?.name && (
                        <span className="text-slate-500 dark:text-slate-400"> {matchedRoom.name}</span>
                      )}
                    </dd>
                    <dt className="text-slate-500 dark:text-slate-400">Date</dt>
                    <dd className="text-slate-900 dark:text-white">
                      {res.start_date}
                      {res.day_of_week && (
                        <span className="text-slate-500 dark:text-slate-400"> ({res.day_of_week})</span>
                      )}
                    </dd>
                    <dt className="text-slate-500 dark:text-slate-400">Time</dt>
                    <dd className="text-slate-900 dark:text-white">
                      {res.start_time}–{res.end_time}
                    </dd>
                    <dt className="text-slate-500 dark:text-slate-400">Group</dt>
                    <dd className="text-slate-900 dark:text-white">{res.group_size} students</dd>
                    <dt className="text-slate-500 dark:text-slate-400">Repeats</dt>
                    <dd className="text-slate-900 dark:text-white">{repeats}</dd>
                  </dl>
                </div>

                <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-700 flex justify-end">
                  <button
                    id={`btn-edit-${res.reservation_id}`}
                    onClick={() => setSelectedResForEdit(res)}
                    className={CARD_ACTION}
                  >
                    Edit
                  </button>
                  <button
                    id={`btn-delete-${res.reservation_id}`}
                    onClick={() => setSelectedResForDelete(res)}
                    className={`${CARD_ACTION} hover:text-red-700 dark:hover:text-red-400`}
                  >
                    Delete
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="py-12 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-700">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {searchQuery ? 'No bookings match that search.' : 'No reservations yet.'}
          </p>
          {!searchQuery && (
            <button
              onClick={onNavigateToBrowse}
              className="mt-3 text-sm font-medium text-brand-700 dark:text-brand-300 underline underline-offset-2"
            >
              Find a room to book
            </button>
          )}
        </div>
      )}

      {selectedResForDelete && (
        <DeleteConfirmModal
          isOpen={Boolean(selectedResForDelete)}
          reservation={selectedResForDelete}
          onClose={() => setSelectedResForDelete(null)}
          onSuccess={onRefresh}
        />
      )}

      {selectedResForEdit && (
        <ReservationModal
          reservation={selectedResForEdit}
          rooms={rooms}
          onClose={() => setSelectedResForEdit(null)}
          onSuccess={onRefresh}
        />
      )}

      {isNewBookingModalOpen && (
        <ReservationModal
          rooms={rooms}
          onClose={() => setIsNewBookingModalOpen(false)}
          onSuccess={onRefresh}
        />
      )}
    </div>
  );
}
