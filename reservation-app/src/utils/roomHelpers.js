// file: src/utils/roomHelpers.js
// purpose: Pure helper functions for room filtering logic
// author: Zin Zin Zaw Win
// date: 2026-10-16

/**
 * Checks if a room meets the minimum capacity requirement.
 * @param {number} roomCapacity - The capacity of the room.
 * @param {number|string} requiredCapacity - The minimum required capacity (may be empty string).
 * @returns {boolean} True if the room is large enough, or if no requirement is set.
 */
export const isRoomBigEnough = (roomCapacity, requiredCapacity) => {
  if (!requiredCapacity) return true;
  return roomCapacity >= requiredCapacity;
};
