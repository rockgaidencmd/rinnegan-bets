import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Constants from 'expo-constants';
import { Ionicons } from '@expo/vector-icons';
import { resetDb } from '../database';
import { RinneganColors as C } from '../constants/Colors';

export default function SettingsScreen() {
  const [resetting, setResetting] = useState(false);
  const version = Constants.expoConfig?.version || '0.1.0';

  const handleReset = () => {
    Alert.alert(
      'Regenerar base de datos',
      'Esto eliminará todas tus apuestas, depósitos e historial y dejará la BDD como recién instalada. ¿Continuar?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Regenerar',
          style: 'destructive',
          onPress: async () => {
            setResetting(true);
            try {
              await resetDb();
              Alert.alert('Listo', 'BDD restaurada. Reabre la app si ves datos viejos en cache.');
            } catch (e) {
              Alert.alert('Error', e.message);
            } finally {
              setResetting(false);
            }
          },
        },
      ],
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.aboutCard}>
          <Text style={styles.title}>RINNEGAN BETS</Text>
          <Text style={styles.version}>v{version}</Text>
          <Text style={styles.note}>
            App standalone — todos los datos viven en este dispositivo.
            No requiere internet ni servidor.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Mantenimiento</Text>
          <TouchableOpacity
            style={styles.dangerBtn}
            onPress={handleReset}
            disabled={resetting}
          >
            <Ionicons name="refresh" size={16} color={C.error} />
            <Text style={styles.dangerBtnText}>
              {resetting ? 'Regenerando...' : 'Regenerar BDD desde asset'}
            </Text>
          </TouchableOpacity>
          <Text style={styles.hint}>
            Útil si algo se rompe en testing. Borra apuestas e historial.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, gap: 20 },

  aboutCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.borderActive,
    borderRadius: 12,
    padding: 20,
    gap: 6,
  },
  title: {
    color: C.accent,
    fontSize: 18,
    fontWeight: '800',
    letterSpacing: 2,
  },
  version: {
    color: C.textMuted,
    fontSize: 12,
    fontFamily: 'monospace',
  },
  note: {
    color: C.textSecondary,
    fontSize: 13,
    lineHeight: 19,
    marginTop: 6,
  },

  section: { gap: 8 },
  sectionTitle: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  dangerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.error,
    backgroundColor: 'rgba(255, 85, 119, 0.06)',
  },
  dangerBtnText: {
    color: C.error,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  hint: {
    color: C.textMuted,
    fontSize: 11,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
