import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  TouchableOpacity,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
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
  const [pendingBets, setPendingBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [modalMode, setModalMode] = useState(null); // 'deposit' | 'withdraw' | null
  const [settlingId, setSettlingId] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [bal, hist, pend] = await Promise.all([
        api.getBalance(),
        api.getBankrollHistory(20),
        api.listPendingBets(),
      ]);
      setBalance(bal);
      setHistory(hist.items || []);
      setPendingBets(pend || []);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const settle = async (bet, outcome) => {
    setSettlingId(bet.id);
    try {
      await api.settleBet(bet.id, outcome);
      await load();
    } catch (e) {
      Alert.alert('Error al liquidar', e.message);
    } finally {
      setSettlingId(null);
    }
  };

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

        {!loading && balance && (
          <View style={styles.actionsRow}>
            <TouchableOpacity
              style={[styles.actionBtn, styles.actionDeposit]}
              onPress={() => setModalMode('deposit')}
            >
              <Ionicons name="arrow-down" size={16} color={C.bg} />
              <Text style={styles.actionDepositText}>Depositar</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, styles.actionWithdraw]}
              onPress={() => setModalMode('withdraw')}
            >
              <Ionicons name="arrow-up" size={16} color={C.accent} />
              <Text style={styles.actionWithdrawText}>Retirar</Text>
            </TouchableOpacity>
          </View>
        )}

        {!loading && pendingBets.length > 0 && (
          <View style={styles.historySection}>
            <Text style={styles.sectionTitle}>
              Apuestas pendientes ({pendingBets.length})
            </Text>
            {pendingBets.map((b) => (
              <View key={b.id} style={styles.betCard}>
                <View style={styles.betHeader}>
                  <Text style={styles.betLeague}>{b.league}</Text>
                  <Text style={styles.betStake}>
                    ${b.stake_amount.toFixed(2)} @ {b.quota_used.toFixed(2)}
                  </Text>
                </View>
                <Text style={styles.betMatchup} numberOfLines={1}>
                  {b.home_team_name}{' '}
                  <Text style={styles.betVs}>vs</Text>{' '}
                  {b.away_team_name}
                </Text>
                <View style={styles.settleRow}>
                  <SettleBtn
                    label="Ganada"
                    color={C.success}
                    onPress={() => settle(b, 'won')}
                    disabled={settlingId !== null}
                    loading={settlingId === b.id}
                  />
                  <SettleBtn
                    label="Perdida"
                    color={C.error}
                    onPress={() => settle(b, 'lost')}
                    disabled={settlingId !== null}
                    loading={settlingId === b.id}
                  />
                  <SettleBtn
                    label="Anulada"
                    color={C.textMuted}
                    onPress={() => settle(b, 'void')}
                    disabled={settlingId !== null}
                    loading={settlingId === b.id}
                  />
                </View>
              </View>
            ))}
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

      <AmountModal
        mode={modalMode}
        onClose={() => setModalMode(null)}
        onSuccess={async () => {
          setModalMode(null);
          await load();
        }}
      />
    </SafeAreaView>
  );
}

function SettleBtn({ label, color, onPress, disabled, loading }) {
  return (
    <TouchableOpacity
      style={[styles.settleBtn, { borderColor: color }]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={[styles.settleBtnText, { color }]}>
        {loading ? '...' : label}
      </Text>
    </TouchableOpacity>
  );
}

function AmountModal({ mode, onClose, onSuccess }) {
  const [amount, setAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (mode) setAmount('');
  }, [mode]);

  const submit = async () => {
    const value = parseFloat(amount);
    if (!Number.isFinite(value) || value <= 0) {
      Alert.alert('Monto inválido', 'Ingresa un número mayor a 0.');
      return;
    }
    setSubmitting(true);
    try {
      if (mode === 'deposit') await api.deposit(value);
      else await api.withdraw(value);
      onSuccess();
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const isDeposit = mode === 'deposit';

  return (
    <Modal
      visible={!!mode}
      animationType="fade"
      transparent
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        style={styles.modalBackdrop}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>
            {isDeposit ? 'Depositar' : 'Retirar'} fondos
          </Text>
          <TextInput
            style={styles.modalInput}
            value={amount}
            onChangeText={setAmount}
            placeholder="0.00"
            placeholderTextColor={C.textMuted}
            keyboardType="decimal-pad"
            autoFocus
          />
          <View style={styles.modalActions}>
            <TouchableOpacity
              style={[styles.modalBtn, styles.modalBtnGhost]}
              onPress={onClose}
              disabled={submitting}
            >
              <Text style={styles.modalBtnGhostText}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalBtn, styles.modalBtnPrimary]}
              onPress={submit}
              disabled={submitting}
            >
              <Text style={styles.modalBtnPrimaryText}>
                {submitting
                  ? '...'
                  : isDeposit
                    ? 'Depositar'
                    : 'Retirar'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
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
    marginBottom: 12,
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

  actionsRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 20,
  },
  actionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 8,
  },
  actionDeposit: { backgroundColor: C.accent },
  actionWithdraw: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: C.accent,
  },
  actionDepositText: {
    color: C.bg,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  actionWithdrawText: {
    color: C.accent,
    fontWeight: '700',
    letterSpacing: 0.5,
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

  betCard: {
    backgroundColor: C.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    padding: 12,
    marginBottom: 8,
    gap: 8,
  },
  betHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  betLeague: {
    color: C.accent,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: 'rgba(0, 245, 160, 0.1)',
  },
  betStake: {
    color: C.textPrimary,
    fontSize: 13,
    fontFamily: 'monospace',
    fontWeight: '700',
  },
  betMatchup: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  betVs: { color: C.textMuted, fontWeight: '400' },
  settleRow: { flexDirection: 'row', gap: 6, marginTop: 4 },
  settleBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    alignItems: 'center',
  },
  settleBtnText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.5,
  },

  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalCard: {
    width: '100%',
    backgroundColor: C.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    padding: 20,
    gap: 16,
  },
  modalTitle: {
    color: C.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  modalInput: {
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 14,
    color: C.textPrimary,
    fontSize: 18,
    fontFamily: 'monospace',
  },
  modalActions: { flexDirection: 'row', gap: 10 },
  modalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalBtnPrimary: { backgroundColor: C.accent },
  modalBtnPrimaryText: {
    color: C.bg,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  modalBtnGhost: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: C.border,
  },
  modalBtnGhostText: {
    color: C.textMuted,
    fontWeight: '600',
  },
});
