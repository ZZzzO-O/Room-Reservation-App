// file: src/pages/SchedulePage.jsx
// purpose: Weekly timetable schedule grid and text report export
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

import { exportScheduleReport } from '../api/reservationApi';
import { INPUT, BTN_SECONDARY } from '../utils/styles';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

const WEEK_BUTTON =
  'p-2.5 rounded-md text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors';

/**
 * Schedule view component showing the weekly timetable across classrooms.
 * @param {Object} props
 * @param {Object[]} props.reservations - Active reservations.
 * @param {Object[]} props.rooms - Registered rooms catalog.
 * @returns {JSX.Element} The SchedulePage component.
 */
export default function SchedulePage({ reservations, rooms }) {
  // Test plan seed week begins on Mon 2026-10-12
  const [weekStart, setWeekStart] = useState('2026-10-12');
  const [selectedRoomFilter, setSelectedRoomFilter] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  const weekReservations = useMemo(() => {
    return reservations.filter((r) => {
      if (selectedRoomFilter && r.room_id !== selectedRoomFilter) {
        return false;
      }
      return true;
    });
  }, [reservations, selectedRoomFilter]);

  /**
   * Move the visible week forwards or backwards.
   * @param {number} daysDelta - Number of days to jump.
   */
  const handleShiftWeek = (daysDelta) => {
    const cur = new Date(weekStart);
    cur.setDate(cur.getDate() + daysDelta);
    setWeekStart(cur.toISOString().split('T')[0]);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportScheduleReport(weekStart, selectedRoomFilter || undefined);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-5">
      <header className="flex flex-col sm:flex-row justify-between sm:items-end gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Weekly schedule
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Classes in different rooms can run at the same time.
          </p>
        </div>

        <button
          id="btn-export-schedule"
          onClick={handleExport}
          disabled={isExporting}
          className={`${BTN_SECONDARY} shrink-0`}
        >
          {isExporting ? 'Exporting…' : 'Export as .txt'}
        </button>
      </header>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1">
          <button
            onClick={() => handleShiftWeek(-7)}
            className={WEEK_BUTTON}
            aria-label="Previous week"
          >
            <ChevronLeft className="w-4 h-4" aria-hidden="true" />
          </button>
          <span className="px-2 text-sm font-medium text-slate-700 dark:text-slate-200 tabular-nums">
            Week of {weekStart}
          </span>
          <button
            onClick={() => handleShiftWeek(7)}
            className={WEEK_BUTTON}
            aria-label="Next week"
          >
            <ChevronRight className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>

        <select
          id="schedule-room-filter"
          aria-label="Filter by room"
          value={selectedRoomFilter}
          onChange={(e) => setSelectedRoomFilter(e.target.value)}
          className={`${INPUT} sm:w-64`}
        >
          <option value="">All rooms</option>
          {[...rooms]
            .sort((a, b) => parseInt(a.room_id || a.id, 10) - parseInt(b.room_id || b.id, 10))
            .map((r) => (
              <option key={r.room_id || r.id} value={r.room_id || r.id}>
                {r.room_id || r.id} {r.name}
              </option>
            ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden bg-white dark:bg-slate-800 divide-y md:divide-y-0 md:divide-x divide-slate-200 dark:divide-slate-700">
        {DAYS_OF_WEEK.map((day) => {
          const dayBookings = weekReservations
            .filter(
              (r) =>
                (r.day_of_week && r.day_of_week.toLowerCase() === day.toLowerCase()) ||
                // Fall back to the start date when day_of_week is missing
                (r.start_date && new Date(r.start_date).toLocaleDateString('en-US', { weekday: 'long' }) === day)
            )
            .sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));

          return (
            <section key={day} className="flex flex-col min-h-40">
              <h2 className="px-3 py-2 flex items-baseline justify-between text-sm font-semibold text-slate-800 dark:text-slate-100 bg-slate-50 dark:bg-slate-900/60 border-b border-slate-200 dark:border-slate-700">
                {day}
                <span className="text-xs font-normal text-slate-500 dark:text-slate-400 tabular-nums">
                  {dayBookings.length}
                </span>
              </h2>

              {dayBookings.length > 0 ? (
                <ul className="divide-y divide-slate-100 dark:divide-slate-700">
                  {dayBookings.map((res) => {
                    const matched = rooms.find((r) => String(r.room_id || r.id) === String(res.room_id));
                    return (
                      <li
                        key={res.reservation_id}
                        className="px-3 py-2 border-l-2 border-brand-500 text-xs tabular-nums"
                      >
                        <div className="flex justify-between gap-2">
                          <span className="font-semibold text-slate-900 dark:text-white">
                            {res.competency}
                          </span>
                          <span className="font-mono text-slate-600 dark:text-slate-300">
                            {res.start_time}–{res.end_time}
                          </span>
                        </div>
                        <div className="mt-0.5 text-slate-500 dark:text-slate-400">
                          {res.room_id}
                          {matched?.name ? ` ${matched.name}` : ''} · {res.group_size} students
                          {res.repetition === 'Once' ? ' · once' : ''}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="px-3 py-6 text-xs text-slate-400 dark:text-slate-500">No classes</p>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
