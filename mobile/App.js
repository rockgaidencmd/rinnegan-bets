import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import AppNavigator from './components/AppNavigator';
import { RinneganColors } from './constants/Colors';

export default function App() {
  return (
    <SafeAreaProvider>
      <AppNavigator />
      <StatusBar style="light" backgroundColor={RinneganColors.bg} />
    </SafeAreaProvider>
  );
}
