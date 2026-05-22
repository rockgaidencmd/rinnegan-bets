// URL del snapshot remoto (rinnegan-initial.db).
//
// Cuando se hace push a esta rama en GitHub, la URL raw devuelve el
// .db actualizado. El botón "Actualizar data" en Ajustes lo descarga
// y mergea sobre la BDD local preservando apuestas y bankroll.
//
// Para apuntar a main cuando se mergee:
//   .../rinnegan-bets/main/mobile/assets/rinnegan-initial.db
export const SNAPSHOT_URL =
  'https://raw.githubusercontent.com/rockgaidencmd/rinnegan-bets/feat/mobile-standalone-sqlite/mobile/assets/rinnegan-initial.db';
