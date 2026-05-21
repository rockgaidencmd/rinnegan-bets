import React, { useEffect, useState } from 'react';
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AppNavigator from './components/AppNavigator';
import { openDatabase } from './database';
import { RinneganColors } from './constants/Colors';

export default function App() {
  const [dbReady, setDbReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    openDatabase()
      .then(() => setDbReady(true))
      .catch((e) => setError(e.message));
  }, []);

  if (error) {
    return (
      <View style={styles.splash}>
        <Text style={styles.splashTitle}>Error iniciando BDD</Text>
        <Text style={styles.splashError}>{error}</Text>
      </View>
    );
  }

  if (!dbReady) {
    return (
      <View style={styles.splash}>
        <ActivityIndicator size="large" color={RinneganColors.accent} />
        <Text style={styles.splashHint}>Preparando base de datos...</Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <AppNavigator />
      <StatusBar style="light" backgroundColor={RinneganColors.bg} />
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1,
    backgroundColor: RinneganColors.bg,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    padding: 24,
  },
  splashTitle: {
    color: RinneganColors.error,
    fontSize: 16,
    fontWeight: '700',
  },
  splashError: {
    color: RinneganColors.textSecondary,
    fontSize: 13,
    textAlign: 'center',
  },
  splashHint: {
    color: RinneganColors.textMuted,
    fontSize: 13,
    letterSpacing: 0.5,
  },
});
