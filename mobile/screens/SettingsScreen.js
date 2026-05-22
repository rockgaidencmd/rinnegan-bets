import React, { useCallback, useEffect, useState } from 'react';
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
import { refreshFromRemote } from '../database/refresh';
import { getMeta } from '../database/meta';
import { SNAPSHOT_URL } from '../constants/Refresh';
import { RinneganColors as C } from '../constants/Colors';

function formatLastRefresh(iso) {
  if (!iso) return 'Nunca actualizado';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return 'Nunca actualizado';
  const date = d.toLocaleDateString('es-EC', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
  const time = d.toLocaleTimeString('es-EC', {
    hour: '2-digit', minute: '2-digit',
  });
  return date + ' ' + time;
}

export default function SettingsScreen() {
  const [resetting, setResetting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const version = Constants.expoConfig?.version || '0.1.0';

  const loadLastRefresh = useCallback(() => {
    try {
      setLastRefresh(getMeta('last_refresh_at'));
    } catch {
      setLastRefresh(null);
    }
  }, []);

  useEffect(() => {
    loadLastRefresh();
  }, [loadLastRefresh]);

  const handleRefresh = () => {
    Alert.alert(
      'Actualizar data',
      'Descarga el snapshot más reciente (equipos, partidos jugados y próximos). Tus apuestas y banca no se tocan.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Actualizar',
          onPress: async () => {
            setRefreshing(true);
            try {
              const result = await refreshFromRemote(SNAPSHOT_URL);
              loadLastRefresh();
              Alert.alert(
                'Listo',
                'Equipos: ' + result.teams + '\n' +
                'Partidos: ' + result.matches + '\n' +
                'Próximos: ' + result.fixtures,
              );
            } catch (e) {
              Alert.alert('No se pudo actualizar', e.message);
            } finally {
              setRefreshing(false);
            }
          },
        },
      ],
    );
  };

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
              loadLastRefresh();
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
            Puedes actualizar el catálogo de partidos cuando quieras.
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Datos</Text>
          <TouchableOpacity
            style={styles.primaryBtn}
            onPress={handleRefresh}
            disabled={refreshing}
          >
            <Ionicons name="cloud-download" size={16} color={C.bg} />
            <Text style={styles.primaryBtnText}>
              {refreshing ? 'Actualizando...' : 'Actualizar data'}
            </Text>
          </TouchableOpacity>
          <Text style={styles.hint}>
            Última actualización: {formatLastRefresh(lastRefresh)}
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
  primaryBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: C.accent,
  },
  primaryBtnText: {
    color: C.bg,
    fontWeight: '700',
    letterSpacing: 0.5,
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
