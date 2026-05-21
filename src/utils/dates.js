/**
 * Date formatters fixed to Ecuador timezone (UTC-5, no DST).
 *
 * SofaScore returns UTC timestamps. A match played at 20:00 Ecuador time
 * becomes 01:00 UTC the next day. Without explicit timeZone, JS would use
 * the browser's local one — wrong if the user is abroad or if the browser
 * runtime is in UTC (Vercel, Docker, etc.).
 */

const EC_TIMEZONE = 'America/Guayaquil';


export function formatDateShort(isoString) {
  return new Date(isoString).toLocaleDateString('es-EC', {
    day: '2-digit',
    month: 'short',
    timeZone: EC_TIMEZONE,
  });
}


export function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString('es-EC', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: EC_TIMEZONE,
  });
}
