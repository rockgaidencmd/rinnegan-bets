// Refresh de data desde un snapshot remoto.
//
// Estrategia (R2 del README):
//   1. Descarga el .db remoto a un archivo temp en SQLite/
//   2. Verifica que sea SQLite válido y tenga las tablas esperadas
//   3. ATTACH del archivo temp al handle abierto
//   4. UPSERT teams + matches (PKs vienen del backend, estables)
//   5. DELETE + INSERT de fixtures (AUTOINCREMENT, snapshot completo)
//   6. NUNCA toca predictions / bets / bankroll_snapshots / meta
//   7. Guarda last_refresh_at en meta
//
// La transacción es atómica: si algo falla, rollback y la BDD local
// queda como estaba.

import * as FileSystem from 'expo-file-system/legacy';
import * as SQLite from 'expo-sqlite';
import { getDb } from './index';
import { setMeta } from './meta';

const TEMP_DB_NAME = 'remote_snapshot.db';

const SQL_BEGIN = 'BEGIN TRANSACTION;';
const SQL_COMMIT = 'COMMIT;';
const SQL_ROLLBACK = 'ROLLBACK;';
const SQL_DETACH = 'DETACH DATABASE remote;';
const SQL_UPSERT_TEAMS = 'INSERT OR REPLACE INTO teams SELECT * FROM remote.teams;';
const SQL_UPSERT_MATCHES = 'INSERT OR REPLACE INTO matches SELECT * FROM remote.matches;';
const SQL_CLEAR_FIXTURES = 'DELETE FROM fixtures;';
const SQL_INSERT_FIXTURES =
  'INSERT INTO fixtures ' +
  '(league, match_date, home_team_id, home_team_name, ' +
  ' away_team_id, away_team_name, fetched_at) ' +
  'SELECT league, match_date, home_team_id, home_team_name, ' +
  '       away_team_id, away_team_name, fetched_at ' +
  'FROM remote.fixtures;';

function tempPath() {
  return FileSystem.documentDirectory + 'SQLite/' + TEMP_DB_NAME;
}

function buildAttachStatement(absolutePath) {
  // SQLite no soporta bind params en ATTACH. El path es app-controlled
  // (siempre el mismo archivo temp), no es entrada del usuario.
  // Strip del prefijo file:// porque expo-file-system devuelve URIs
  // pero el motor nativo de SQLite espera path filesystem plano.
  // Escapamos single quotes por buena medida.
  const cleaned = absolutePath.replace(/^file:\/\//, '');
  const escaped = cleaned.replace(/'/g, "''");
  return "ATTACH DATABASE '" + escaped + "' AS remote;";
}

async function downloadSnapshot(url) {
  const target = tempPath();
  const dir = FileSystem.documentDirectory + 'SQLite';

  const dirInfo = await FileSystem.getInfoAsync(dir);
  if (!dirInfo.exists) {
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
  }

  const existing = await FileSystem.getInfoAsync(target);
  if (existing.exists) {
    await FileSystem.deleteAsync(target);
  }

  const result = await FileSystem.downloadAsync(url, target);
  if (result.status !== 200) {
    throw new Error('Descarga falló (HTTP ' + result.status + ').');
  }

  const info = await FileSystem.getInfoAsync(target);
  if (!info.exists || info.size < 1024) {
    throw new Error('El archivo descargado está vacío o corrupto.');
  }
  return target;
}

function validateSnapshot() {
  const probe = SQLite.openDatabaseSync(TEMP_DB_NAME);
  try {
    const teams = probe.getFirstSync(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='teams'",
    );
    const matches = probe.getFirstSync(
      "SELECT name FROM sqlite_master WHERE type='table' AND name='matches'",
    );
    if (!teams || !matches) {
      throw new Error('El snapshot no contiene las tablas esperadas.');
    }
  } finally {
    try { probe.closeSync(); } catch { /* ignore */ }
  }
}

function mergeAttachedSnapshot(absoluteTempPath) {
  const db = getDb();
  const attachStmt = buildAttachStatement(absoluteTempPath);
  db.execSync(attachStmt);
  try {
    db.execSync(SQL_BEGIN);
    try {
      db.execSync(SQL_UPSERT_TEAMS);
      db.execSync(SQL_UPSERT_MATCHES);
      db.execSync(SQL_CLEAR_FIXTURES);
      db.execSync(SQL_INSERT_FIXTURES);
      db.execSync(SQL_COMMIT);
    } catch (err) {
      try { db.execSync(SQL_ROLLBACK); } catch { /* ignore */ }
      throw err;
    }
  } finally {
    try { db.execSync(SQL_DETACH); } catch { /* ignore */ }
  }
}

export async function refreshFromRemote(url) {
  const tempFilePath = await downloadSnapshot(url);
  validateSnapshot();
  mergeAttachedSnapshot(tempFilePath);

  try {
    await FileSystem.deleteAsync(tempFilePath);
  } catch { /* best-effort */ }

  const db = getDb();
  const counts = {
    teams: db.getFirstSync('SELECT COUNT(*) AS c FROM teams').c,
    matches: db.getFirstSync('SELECT COUNT(*) AS c FROM matches').c,
    fixtures: db.getFirstSync('SELECT COUNT(*) AS c FROM fixtures').c,
  };

  const refreshedAt = new Date().toISOString();
  setMeta('last_refresh_at', refreshedAt);
  setMeta('last_refresh_url', url);

  return { refreshedAt, ...counts };
}
