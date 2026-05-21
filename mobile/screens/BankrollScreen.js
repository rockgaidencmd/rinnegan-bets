import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';
import { RinneganColors as C } from '../constants/Colors';

const TZ = 'America/Guayaquil';

function formatDateTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString('es-EC', {
      timeZone: TZ,
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

export default function BankrollScreen() {
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [bal, hist] = await Promise.all([
        api.getBalance(),
        api.getBankrollHistory(20),
      ]);
      setBalance(bal);
      setHistory(hist.items || []);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={C.accent}
          />
        }
      >
        {loading && (
          <ActivityIndicator
            style={styles.loader}
            size="large"
            color={C.accent}
          />
        )}

        {!loading && error && <Text style={styles.error}>{error}</Text>}

        {!loading && balance && (
          <View style={styles.balanceCard}>
            <Text style={styles.balanceLabel}>Balance actual</Text>
            <Text style={styles.balanceValue}>
              ${balance.current?.toFixed(2)}
            </Text>
            <View style={styles.balanceRow}>
              <View>
                <Text style={styles.balanceSubLabel}>Disponible</Text>
                <Text style={styles.balanceSubValue}>
                  ${balance.available?.toFixed(2)}
                </Text>
              </View>
              <View>
                <Text style={styles.balanceSubLabel}>En juego</Text>
                <Text style={styles.balanceSubValue}>
                  ${balance.pending_commitment?.toFixed(2)}
                </Text>
              </View>
            </View>
          </View>
        )}

        {!loading && history.length > 0 && (
          <View style={styles.historySection}>
            <Text style={styles.sectionTitle}>Movimientos recientes</Text>
            {history.map((h) => (
              <View key={h.id} style={styles.historyRow}>
                <View style={styles.historyMeta}>
                  <Text style={styles.historyReason}>{h.reason}</Text>
                  <Text style={styles.historyDate}>
                    {formatDateTime(h.created_at)}
                  </Text>
                </View>
                <Text
                  style={[
                    styles.historyAmount,
                    h.change_amount >= 0
                      ? styles.amountPositive
                      : styles.amountNegative,
                  ]}
                >
                  {h.change_amount >= 0 ? '+' : ''}
                  ${h.change_amount?.toFixed(2)}
                </Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, paddingBottom: 24 },
  loader: { marginTop: 32 },
  error: { color: C.error, textAlign: 'center', padding: 16 },

  balanceCard: {
    backgroundColor: C.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.borderActive,
    padding: 20,
    marginBottom: 20,
  },
  balanceLabel: {
    color: C.textMuted,
    fontSize: 12,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  balanceValue: {
    color: C.accent,
    fontSize: 36,
    fontWeight: '800',
    fontFamily: 'monospace',
    marginTop: 4,
  },
  balanceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: C.border,
  },
  balanceSubLabel: {
    color: C.textMuted,
    fontSize: 11,
    letterSpacing: 0.5,
  },
  balanceSubValue: {
    color: C.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    fontFamily: 'monospace',
    marginTop: 2,
  },

  historySection: { marginTop: 8 },
  sectionTitle: {
    color: C.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  historyRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: C.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    padding: 12,
    marginBottom: 6,
  },
  historyMeta: { flex: 1 },
  historyReason: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  historyDate: {
    color: C.textMuted,
    fontSize: 11,
    marginTop: 2,
    fontFamily: 'monospace',
  },
  historyAmount: {
    fontSize: 15,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  amountPositive: { color: C.success },
  amountNegative: { color: C.error },
});
