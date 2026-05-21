import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { RinneganColors as C } from '../constants/Colors';

export default function PrediccionScreen() {
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.placeholder}>
        <Ionicons name="analytics-outline" size={64} color={C.accentDim} />
        <Text style={styles.title}>Predicción</Text>
        <Text style={styles.subtitle}>
          Próximamente: selector de liga, picker de equipos y EV con Kelly.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  placeholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    gap: 16,
  },
  title: {
    color: C.textPrimary,
    fontSize: 22,
    fontWeight: '700',
    letterSpacing: 1,
  },
  subtitle: {
    color: C.textSecondary,
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});
