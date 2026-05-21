import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import {
  getApiBaseUrl,
  setApiBaseUrl,
  getDefaultApiUrl,
  api,
} from '../api/client';
import { RinneganColors as C } from '../constants/Colors';

export default function SettingsScreen() {
  const [url, setUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [status, setStatus] = useState(null);
  const defaultUrl = getDefaultApiUrl();

  useEffect(() => {
    getApiBaseUrl().then(setUrl);
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const saved = await setApiBaseUrl(url);
      setUrl(saved);
      setStatus({ kind: 'ok', msg: 'URL guardada.' });
    } catch (e) {
      setStatus({ kind: 'err', msg: e.message });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setStatus(null);
    try {
      await setApiBaseUrl(url);
      const leagues = await api.listLeagues();
      const count = leagues?.leagues?.length ?? 0;
      setStatus({
        kind: 'ok',
        msg: `Conexión OK — ${count} ligas disponibles.`,
      });
    } catch (e) {
      setStatus({ kind: 'err', msg: `Falló: ${e.message}` });
    } finally {
      setTesting(false);
    }
  };

  const handleReset = () => {
    Alert.alert('Resetear URL', `Volver al default: ${defaultUrl}?`, [
      { text: 'Cancelar', style: 'cancel' },
      {
        text: 'Resetear',
        onPress: async () => {
          await setApiBaseUrl('');
          setUrl(defaultUrl);
          setStatus({ kind: 'ok', msg: 'URL restaurada al default.' });
        },
      },
    ]);
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.section}>
            <Text style={styles.label}>URL del backend</Text>
            <TextInput
              style={styles.input}
              value={url}
              onChangeText={setUrl}
              placeholder="http://192.168.1.x:8000"
              placeholderTextColor={C.textMuted}
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="url"
            />
            <Text style={styles.hint}>Default: {defaultUrl}</Text>
          </View>

          {status && (
            <View
              style={[
                styles.statusBox,
                status.kind === 'ok' ? styles.statusOk : styles.statusErr,
              ]}
            >
              <Ionicons
                name={
                  status.kind === 'ok'
                    ? 'checkmark-circle'
                    : 'alert-circle'
                }
                size={18}
                color={
                  status.kind === 'ok' ? C.success : C.error
                }
              />
              <Text style={styles.statusText}>{status.msg}</Text>
            </View>
          )}

          <View style={styles.actions}>
            <TouchableOpacity
              style={[styles.btn, styles.btnPrimary]}
              onPress={handleTest}
              disabled={testing || saving}
            >
              <Text style={styles.btnPrimaryText}>
                {testing ? 'Probando...' : 'Probar conexión'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.btn, styles.btnSecondary]}
              onPress={handleSave}
              disabled={testing || saving}
            >
              <Text style={styles.btnSecondaryText}>
                {saving ? 'Guardando...' : 'Guardar'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.btn, styles.btnGhost]}
              onPress={handleReset}
            >
              <Text style={styles.btnGhostText}>Resetear al default</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, gap: 20 },
  section: { gap: 8 },
  label: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  input: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: C.textPrimary,
    fontFamily: 'monospace',
    fontSize: 14,
  },
  hint: {
    color: C.textMuted,
    fontSize: 11,
    fontFamily: 'monospace',
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  statusOk: {
    backgroundColor: 'rgba(0, 245, 160, 0.08)',
    borderColor: C.accent,
  },
  statusErr: {
    backgroundColor: 'rgba(255, 85, 119, 0.08)',
    borderColor: C.error,
  },
  statusText: {
    flex: 1,
    color: C.textPrimary,
    fontSize: 13,
  },
  actions: { gap: 10 },
  btn: {
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnPrimary: { backgroundColor: C.accent },
  btnPrimaryText: {
    color: C.bg,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  btnSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: C.accent,
  },
  btnSecondaryText: {
    color: C.accent,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  btnGhost: { backgroundColor: 'transparent' },
  btnGhostText: { color: C.textMuted, fontSize: 12 },
});
