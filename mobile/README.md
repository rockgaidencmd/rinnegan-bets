# Rinnegan Bets — Mobile (Expo)

App mobile que consume el backend FastAPI del repo padre.

## Setup

```bash
cd mobile
npm install
```

## Configurar URL del backend

El default en `app.json` (`extra.apiUrl`) apunta a `http://192.168.1.100:8000`.
Cambia esa IP por la de tu PC en la LAN (la mobile NO puede usar `localhost`,
eso apunta al propio teléfono).

Para descubrir la IP de tu PC en Linux:

```bash
hostname -I | awk '{print $1}'
```

## Backend — habilitar CORS LAN

El backend ya tiene CORS para el frontend web (`http://localhost:5173`).
Para Expo Go también hay que permitir el origen del dispositivo, o
usar `allow_origin_regex` para aceptar la subred local.

## Correr

```bash
npm start            # abre el dev server, escanea QR con Expo Go
npm run android      # emulador Android
npm run ios          # simulador iOS (solo macOS)
```

## Estructura

```
mobile/
├── App.js                  Entry point + SafeArea + StatusBar
├── app.json                Expo config (apiUrl en extra)
├── components/
│   └── AppNavigator.js     Bottom tabs (Partidos · Predicción · Bankroll)
├── constants/
│   └── Colors.js           Paleta dark (sync con frontend web)
├── api/
│   └── client.js           Wrapper fetch sobre el backend
└── screens/
    ├── PartidosScreen.js   Lista paginada con filtro por liga
    ├── PrediccionScreen.js Placeholder
    └── BankrollScreen.js   Balance + últimos 20 movimientos
```
