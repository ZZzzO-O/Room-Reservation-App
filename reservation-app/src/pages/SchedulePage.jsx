// file: src/pages/SchedulePage.jsx
// purpose: Weekly timetable schedule grid and text report export
// author: Zin Zin Zaw Win
// date: 2026-10-20

import React, { useState, useMemo } from 'react';
import {
  CalendarDays,
  Download,
  Filter,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  Users,
} from 'lucide-react';

import { exportScheduleReport } from '../api/reservationApi';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];

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

  /**
   * Filter reservations by week start and optional room filter.
   */
  const weekReservations = useMemo(() => {
    return reservations.filter((r) => {
      if (selectedRoomFilter && r.room_id !== selectedRoomFilter) {
        return false;
      }
      return true;
    });
  }, [reservations, selectedRoomFilter]);

  /**
   * Advance or backtrack week date by 7 days.
   * @param {number} daysDelta - Number of days to jump.
   */
  const handleShiftWeek = (daysDelta) => {
    const cur = new Date(weekStart);
    cur.setDate(cur.getDate() + daysDelta);
    setWeekStart(cur.toISOString().split('T')[0]);
  };

  /**
   * Export timetable as a formatted text file.
   */
  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportScheduleReport(weekStart, selectedRoomFilter || undefined);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Schedule Controls Header */}
      <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 transition-colors space-y-4">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <CalendarDays className="w-6 h-6 text-blue-600" />
              Weekly Class Schedule
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Timetable overview supporting parallel classes across CMKL classrooms.
            </p>
          </div>

          <button
            id="btn-export-schedule"
            onClick={handleExport}
            disabled={isExporting}
            className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 dark:bg-blue-600 dark:hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition-colors shrink-0"
          >
            <Download className="w-4 h-4" />
            {isExporting ? 'Exporting...' : 'Export Timetable (TXT)'}
          </button>
        </div>

        {/* Date Navigator and Room Filter */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          {/* Week Shift */}
          <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-900/60 p-1.5 rounded-xl border border-slate-200 dark:border-slate-700">
            <button
              onClick={() => handleShiftWeek(-7)}
              className="p-1.5 hover:bg-white dark:hover:bg-slate-800 rounded-lg text-slate-600 dark:text-slate-300 transition-colors"
              title="Previous Week"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs font-semibold px-2 text-slate-700 dark:text-slate-200">
              Week of {weekStart}
            </span>
            <button
              onClick={() => handleShiftWeek(7)}
              className="p-1.5 hover:bg-white dark:hover:bg-slate-800 rounded-lg text-slate-600 dark:text-slate-300 transition-colors"
              title="Next Week"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Room Filter Dropdown */}
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="w-4 h-4 text-slate-400 shrink-0" />
            <select
              id="schedule-room-filter"
              value={selectedRoomFilter}
              onChange={(e) => setSelectedRoomFilter(e.target.value)}
              className="w-full sm:w-64 px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl text-xs font-medium text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All CMKL Classrooms</option>
              {[...rooms]
                .sort((a, b) => parseInt(a.room_id || a.id, 10) - parseInt(b.room_id || b.id, 10))
                .map((r) => (
                  <option key={r.room_id || r.id} value={r.room_id || r.id}>
                    Room {r.room_id || r.id} — {r.name}
                  </option>
                ))}
            </select>
          </div>
        </div>
      </div>

      {/* Timetable Grid View */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {DAYS_OF_WEEK.map((day) => {
          const dayBookings = weekReservations.filter(
            (r) =>
              (r.day_of_week && r.day_of_week.toLowerCase() === day.toLowerCase()) ||
              // Check date match if day_of_week not set
              (r.start_date && new Date(r.start_date).toLocaleDateString('en-US', { weekday: 'long' }) === day)
          );

          return (
            <div
              key={day}
              className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm flex flex-col"
            >
              {/* Day Header */}
              <div className="bg-slate-50 dark:bg-slate-900/80 px-4 py-3 border-b border-slate-200 dark:border-slate-700 text-center">
                <h3 className="font-bold text-sm text-slate-800 dark:text-slate-100">
                  {day}
                </h3>
                <span className="text-[11px] text-slate-400">
                  {dayBookings.length} {dayBookings.length === 1 ? 'Class' : 'Classes'}
                </span>
              </div>

              {/* Day Slots */}
              <div className="p-3 flex-grow space-y-2.5">
                {dayBookings.length > 0 ? (
                  dayBookings.map((res) => {
                    const matched = rooms.find((r) => String(r.room_id || r.id) === String(res.room_id));
                    const rmName = matched
                      ? `Room ${res.room_id} (${matched.name})`
                      : `Room ${res.room_id}`;

                    return (
                      <div
                        key={res.reservation_id}
                        className="p-3 bg-blue-50/70 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 rounded-xl space-y-1.5 transition-all hover:border-blue-400"
                      >
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-xs text-blue-900 dark:text-blue-300">
                            {res.competency}
                          </span>
                          <span className="text-[10px] text-blue-600 dark:text-blue-400 font-mono">
                            {res.start_time} - {res.end_time}
                          </span>
                        </div>

                        <div className="flex items-center gap-1 text-[11px] text-slate-600 dark:text-slate-300">
                          <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                          <span>{rmName}</span>
                        </div>

                        <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1 border-t border-blue-100 dark:border-blue-900/40">
                          <span className="flex items-center gap-1">
                            <Users className="w-2.5 h-2.5" /> {res.group_size} seats
                          </span>
                          <span>{res.repetition === 'Once' ? 'Single Slot' : (res.repetition || 'Weekly')}</span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="py-10 text-center text-xs text-slate-400 dark:text-slate-500 italic">
                    No bookings scheduled
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
