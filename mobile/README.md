# Rinnegan Bets — Mobile (Expo, standalone)

App **independiente**: SQLite local pre-poblada, lógica de predicción
en JS, sin backend. La primera vez que se abre copia el snapshot
bundleado a storage del dispositivo y trabaja contra esa copia.

## Setup

```bash
cd mobile
npm install
npm start            # escanea el QR con Expo Go (SDK 54)
```

No necesitas el backend corriendo para usarla.

## Regenerar el snapshot inicial

`mobile/assets/rinnegan-initial.db` es la BDD bundleada con la app.
Para refrescarla desde tu BDD local de desarrollo:

```bash
cd backend
source venv/bin/activate
python scripts/export_mobile_db.py
```

Esto:
- Copia `teams` (catálogo completo)
- Copia `matches WHERE home_goals IS NOT NULL` (con resultado)
- Llama `GET /api/fixtures` por cada liga (best-effort — necesita el
  backend corriendo en `localhost:8000` para llenar la tabla de
  próximos partidos; si está apagado, queda vacía)
- Crea `predictions / bets / bankroll_snapshots` vacías
- `VACUUM` final

Output típico: ~0.5 MB, 215 teams, 1169 matches, ~60 fixtures.

Después un `git commit` del nuevo `.db` y un rebuild de la app
(o Expo OTA update) entrega la data nueva al teléfono.

## Estructura

```
mobile/
├── App.js                    SafeAreaProvider + StatusBar; gatea el
│                             render del navigator hasta que la BDD
│                             abre (splash con spinner mientras tanto).
├── app.json                  expo-sqlite + expo-asset en plugins
├── metro.config.js           agrega 'db' a resolver.assetExts
│
├── assets/
│   └── rinnegan-initial.db   snapshot bundleado (~0.5 MB)
│
├── database/
│   ├── index.js              openDatabase / getDb / resetDb
│   ├── leagues.js            listLeagues (estatic + counts)
│   ├── teams.js              searchTeams / getTeamsByLeague / getTeamStats
│   ├── matches.js            listMatches + getLastMatchesForTeam
│   ├── fixtures.js           listFixtures (snapshot bundleado)
│   ├── bankroll.js           getBalance / getHistory / deposit / withdraw
│   ├── bets.js               placeBet / listPendingBets / settleBet
│   └── predictions.js        savePrediction / getPrediction
│
├── core/                     Lógica pura (port literal del backend Python)
│   ├── leagues.js            LEAGUES catalog (port de core/leagues.py)
│   ├── features.js           extractTeamFeatures / computeForm / avgXg
│   ├── models/
│   │   ├── _shared.js        constants + helpers (normalize, blend, …)
│   │   ├── europe.js         EUROPE_WEIGHTS + europePreScore
│   │   ├── ecuador.js        ECUADOR_WEIGHTS + ecuadorPreScore
│   │   └── index.js          getModelForLeague factory
│   ├── kelly.js              EV + Kelly + verdict thresholds
│   └── predict.js            orchestrator (mismo shape que /api/predictions)
│
├── api/
│   └── client.js             Wrapper async sobre database/ + core/
│                             (mismo shape api.* que las screens consumen)
│
├── components/
│   ├── AppNavigator.js       Bottom-tabs: Partidos · Ligas · Predicción
│   │                                       Banca · Ajustes
│   ├── TeamsComparison.js    side-by-side stats
│   └── TeamDetailModal.js    stats + últimos partidos por equipo
│
└── screens/
    ├── PartidosScreen.js
    ├── LigasScreen.js
    ├── PrediccionScreen.js   modo "Buscar" + modo "Próximos partidos"
    ├── BankrollScreen.js     balance + depositar/retirar + apuestas
    │                         pendientes con liquidar (G/P/A)
    └── SettingsScreen.js     about + regenerar BDD
```

## Estrategia de refresh

**R2 — Descargar `snapshot.db` desde un host estático — IMPLEMENTADO**

La URL vive en `mobile/constants/Refresh.js` apuntando al raw de
GitHub del `mobile/assets/rinnegan-initial.db` en una rama definida.
Botón "Actualizar data" en Ajustes hace:

1. Descarga el `.db` remoto a un archivo temporal en `SQLite/`
2. Valida que sea SQLite válido y tenga las tablas esperadas
3. `ATTACH` del archivo temp y dentro de una transacción:
   - `INSERT OR REPLACE INTO teams SELECT * FROM remote.teams`
   - `INSERT OR REPLACE INTO matches SELECT * FROM remote.matches`
   - `DELETE FROM fixtures; INSERT INTO fixtures SELECT ... FROM remote.fixtures`
4. **Nunca toca** `predictions / bets / bankroll_snapshots / meta` —
   las apuestas y el banco del usuario se preservan.
5. Guarda `last_refresh_at` en `meta` para mostrar timestamp en UI.

Si algo falla → `ROLLBACK` y la BDD local queda intacta.

**Para publicar una versión nueva de data:**
```bash
cd backend && source venv/bin/activate
python scripts/export_mobile_db.py
git add mobile/assets/rinnegan-initial.db
git commit -m "data(mobile): refresh snapshot"
git push                # raw URL queda actualizada al instante
```

Tu hermano toca "Actualizar data" en Ajustes → baja el nuevo `.db`.

### Otras opciones consideradas (no implementadas)

**R1 — Cliente pega directo a SofaScore desde el celular**
  - En nativo no aplica CORS, factible
  - Botón en Ajustes itera ligas y mete partidos nuevos en SQLite
  - Pro: cero dependencia externa
  - Contra: SofaScore es API no oficial; hay que portar los parsers
    del backend (`backend/data/sofascore/*`) a JS

**R3 — Expo OTA updates con BDD nueva**
  - `eas update` con el asset actualizado
  - Pro: nativo de Expo
  - Contra: requiere eas + el `.db` dispara un download grande cada vez

## TODOs conocidos

- Aliases de búsqueda de equipos (IDV→Independiente, etc) — el Python
  los tiene en `data/team_search.py`, el JS aún no
- Tests unitarios JS — el backend tiene 244, el mobile no tiene infra
  todavía; al validar el port se puede comparar números contra el
  backend ejecutando el mismo input en ambos lados
- Refresh de data (R1/R2/R3 arriba)
- Pantalla de **historial de apuestas liquidadas** (hoy solo se ven
  los movimientos en bankroll_snapshots; ver el bet original requiere
  cruce con predictions)
