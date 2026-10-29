// file: src/pages/MyReservationsPage.jsx
// purpose: View, search, edit, and cancel classroom reservations
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import {
  Calendar,
  Search,
  Clock,
  Users,
  MapPin,
  Edit2,
  Trash2,
  Plus,
  Repeat,
} from 'lucide-react';

import DeleteConfirmModal from '../components/DeleteConfirmModal';
import ReservationModal from '../components/ReservationModal';

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
   * Filter reservations by competency code or room ID.
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
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 transition-colors">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Classroom Reservations
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Manage scheduled competencies and review booked semester time slots.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              id="btn-new-reservation"
              onClick={() => setIsNewBookingModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Reservation
            </button>
          </div>
        </div>

        {/* Search bar */}
        <div className="mt-4 max-w-md relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
          <input
            id="search-reservations"
            type="text"
            placeholder="Search by course (e.g. SEN-201) or room number (e.g. 604, 609)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      {/* Reservations List */}
      {filteredReservations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredReservations.map((res) => {
            const matchedRoom = rooms.find((r) => String(r.room_id || r.id) === String(res.room_id));
            const roomLabel = matchedRoom
              ? `Room ${res.room_id}${matchedRoom.name ? ` (${matchedRoom.name})` : ''}`
              : `Room ${res.room_id}`;

            return (
              <div
                key={res.reservation_id}
                className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-200 dark:border-slate-700 flex flex-col justify-between hover:shadow-md hover:border-blue-200 dark:hover:border-blue-800 transition-all space-y-4"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="px-3 py-1 bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-bold tracking-wide">
                      {res.competency}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      {res.reservation_id}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm text-slate-600 dark:text-slate-300 mt-3">
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {roomLabel}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                      <span>{res.start_date} ({res.day_of_week || 'Weekday'})</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-slate-400 shrink-0" />
                      <span>{res.start_time} - {res.end_time}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Users className="w-4 h-4 text-slate-400 shrink-0" />
                      <span>Group Size: {res.group_size}</span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <Repeat className="w-3.5 h-3.5" />
                      <span>{res.repetition === 'Once' ? 'Single Slot' : (res.repetition || 'Weekly')}</span>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-700/60 flex items-center justify-end gap-2">
                  <button
                    id={`btn-edit-${res.reservation_id}`}
                    onClick={() => setSelectedResForEdit(res)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg text-xs font-semibold transition-colors"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                    Edit
                  </button>
                  <button
                    id={`btn-delete-${res.reservation_id}`}
                    onClick={() => setSelectedResForDelete(res)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-red-50 hover:bg-red-100 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg text-xs font-semibold transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Delete
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="py-16 text-center bg-white dark:bg-slate-800 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 p-8">
          <Calendar className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
            No reservations found
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
            {searchQuery
              ? 'No bookings match your search query.'
              : 'You have not reserved any classrooms for this semester yet.'}
          </p>
          <button
            onClick={onNavigateToBrowse}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition-colors"
          >
            Browse Available Classrooms
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal (Activity Diagram workflow) */}
      {selectedResForDelete && (
        <DeleteConfirmModal
          isOpen={Boolean(selectedResForDelete)}
          reservation={selectedResForDelete}
          onClose={() => setSelectedResForDelete(null)}
          onSuccess={onRefresh}
        />
      )}

      {/* Edit Reservation Modal */}
      {selectedResForEdit && (
        <ReservationModal
          reservation={selectedResForEdit}
          rooms={rooms}
          onClose={() => setSelectedResForEdit(null)}
          onSuccess={onRefresh}
        />
      )}

      {/* New Reservation Modal */}
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
