// Tell Metro to bundle .db files as binary assets — needed for
// require('./assets/rinnegan_initial.db') in database/index.js to
// resolve to a real file at runtime instead of failing as an
// unknown extension.
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);
config.resolver.assetExts.push('db');

module.exports = config;
