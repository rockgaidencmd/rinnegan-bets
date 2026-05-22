// Key/value store para metadata de la app (timestamps, flags, etc).
// Tabla creada en database/index.js al abrir la BDD.

import { getDb } from './index';

export function getMeta(key) {
  const db = getDb();
  const row = db.getFirstSync('SELECT value FROM meta WHERE key = ?', [key]);
  return row ? row.value : null;
}

export function setMeta(key, value) {
  const db = getDb();
  db.runSync(
    'INSERT INTO meta (key, value) VALUES (?, ?) ' +
    'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
    [key, value],
  );
}
