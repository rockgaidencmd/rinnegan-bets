import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { RinneganColors } from '../constants/Colors';

import PartidosScreen from '../screens/PartidosScreen';
import PrediccionScreen from '../screens/PrediccionScreen';
import BankrollScreen from '../screens/BankrollScreen';
import LigasScreen from '../screens/LigasScreen';
import SettingsScreen from '../screens/SettingsScreen';

const Tab = createBottomTabNavigator();

const NavTheme = {
  ...DefaultTheme,
  dark: true,
  colors: {
    ...DefaultTheme.colors,
    background: RinneganColors.bg,
    card: RinneganColors.surface,
    text: RinneganColors.textPrimary,
    border: RinneganColors.border,
    primary: RinneganColors.accent,
  },
};

const ICON_BY_ROUTE = {
  Partidos: ['football', 'football-outline'],
  Ligas: ['trophy', 'trophy-outline'],
  Predicción: ['analytics', 'analytics-outline'],
  Bankroll: ['wallet', 'wallet-outline'],
  Ajustes: ['settings', 'settings-outline'],
};

export default function AppNavigator() {
  const insets = useSafeAreaInsets();
  return (
    <NavigationContainer theme={NavTheme}>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            const [active, inactive] = ICON_BY_ROUTE[route.name] || [];
            return (
              <Ionicons
                name={focused ? active : inactive}
                size={size}
                color={color}
              />
            );
          },
          tabBarActiveTintColor: RinneganColors.accent,
          tabBarInactiveTintColor: RinneganColors.textMuted,
          tabBarStyle: {
            backgroundColor: RinneganColors.surface,
            borderTopColor: RinneganColors.border,
            paddingTop: 6,
            paddingBottom: 6 + insets.bottom,
            height: 64 + insets.bottom,
          },
          headerStyle: {
            backgroundColor: RinneganColors.surface,
            borderBottomColor: RinneganColors.border,
            borderBottomWidth: 1,
          },
          headerTintColor: RinneganColors.textPrimary,
          headerTitleStyle: {
            fontWeight: '700',
            letterSpacing: 0.5,
          },
        })}
      >
        <Tab.Screen name="Partidos" component={PartidosScreen} />
        <Tab.Screen name="Ligas" component={LigasScreen} />
        <Tab.Screen name="Predicción" component={PrediccionScreen} />
        <Tab.Screen name="Bankroll" component={BankrollScreen} />
        <Tab.Screen name="Ajustes" component={SettingsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
