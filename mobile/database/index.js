// Standalone SQLite database for the app.
//
// On first launch we copy the bundled assets/rinnegan-initial.db into
// the device's writable documents dir and open it. On subsequent
// launches we just open the writable copy — user data (bets, bankroll
// snapshots, predictions) persists across sessions.
//
// resetDb() wipes the writable copy and re-copies from the asset,
// useful for "factory reset" / debugging from the Settings screen.

import * as SQLite from 'expo-sqlite';
import * as FileSystem from 'expo-file-system';
import { Asset } from 'expo-asset';

const DB_NAME = 'rinnegan.db';
// The Asset module resolves this require() to a content URI at runtime.
const INITIAL_DB_ASSET = require('../assets/rinnegan-initial.db');

let _db = null;
let _openPromise = null;

function dbPath() {
  return `${FileSystem.documentDirectory}SQLite/${DB_NAME}`;
}

async function copyAssetToDocuments(overwrite = false) {
  const target = dbPath();
  const dir = `${FileSystem.documentDirectory}SQLite`;
  const dirInfo = await FileSystem.getInfoAsync(dir);
  if (!dirInfo.exists) {
    await FileSystem.makeDirectoryAsync(dir, { intermediates: true });
  }

  const existing = await FileSystem.getInfoAsync(target);
  if (existing.exists && !overwrite) return;

  const asset = Asset.fromModule(INITIAL_DB_ASSET);
  await asset.downloadAsync();
  // asset.localUri is set after downloadAsync (file:// path)
  await FileSystem.copyAsync({ from: asset.localUri, to: target });
}

export async function openDatabase() {
  if (_db) return _db;
  if (_openPromise) return _openPromise;

  _openPromise = (async () => {
    await copyAssetToDocuments(false);
    _db = SQLite.openDatabaseSync(DB_NAME);
    // Foreign keys are off by default in SQLite — turn on so our FK
    // constraints (bets -> predictions, etc) actually fire.
    _db.execSync('PRAGMA foreign_keys = ON;');
    return _db;
  })();

  return _openPromise;
}

export function getDb() {
  if (!_db) {
    throw new Error('Database not opened yet — call openDatabase() first.');
  }
  return _db;
}

// Useful from Settings: wipe user data + restore the bundled initial DB.
export async function resetDb() {
  if (_db) {
    try { _db.closeSync(); } catch { /* ignore */ }
    _db = null;
    _openPromise = null;
  }
  const target = dbPath();
  const info = await FileSystem.getInfoAsync(target);
  if (info.exists) {
    await FileSystem.deleteAsync(target);
  }
  return openDatabase();
}
