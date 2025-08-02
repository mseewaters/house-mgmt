// Frontend timezone conversion utilities

// Convert UTC string to local time
function formatLocalTime(utcString) {
  const utcDate = new Date(utcString);
  return utcDate.toLocaleString(); // User's local timezone
}

// Convert UTC to specific timezone using Luxon
import { DateTime } from "luxon";

function formatTimezone(utcString, timezone = "America/New_York") {
  return DateTime.fromISO(utcString, { zone: "utc" })
    .setZone(timezone)
    .toFormat("yyyy-MM-dd HH:mm");
}

// Vue.js composable for timezone handling
import { ref, computed } from 'vue';

export function useTimezone() {
  const userTimezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone);
  
  const formatUTC = (utcString) => {
    if (!utcString) return '';
    const date = new Date(utcString);
    return date.toLocaleString('en-US', {
      timeZone: userTimezone.value,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };
  
  const formatRelative = (utcString) => {
    if (!utcString) return '';
    const date = new Date(utcString);
    const now = new Date();
    const diffMs = now - date;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return formatUTC(utcString);
  };
  
  return {
    userTimezone: computed(() => userTimezone.value),
    formatUTC,
    formatRelative
  };
}