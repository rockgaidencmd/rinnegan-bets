import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api/client';
import TeamDetailModal from '../components/TeamDetailModal';
import { RinneganColors as C } from '../constants/Colors';

export default function LigasScreen() {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(null);
  const [selectedTeam, setSelectedTeam] = useState(null);

  const load = async () => {
    setError(null);
    try {
      const data = await api.listLeagues();
      setLeagues(data.leagues || []);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    setLoading(true);
    load().finally(() => setLoading(false));
  }, []);

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

        {!loading && leagues.length > 0 && (
          <View>
            <Text style={styles.subtitle}>
              {leagues.length} ligas · tap para ver equipos
            </Text>
            {leagues.map((l) => (
              <LeagueCard
                key={l.code}
                league={l}
                expanded={expanded === l.code}
                onToggle={() =>
                  setExpanded(expanded === l.code ? null : l.code)
                }
                onTeamPress={setSelectedTeam}
              />
            ))}
          </View>
        )}
      </ScrollView>

      <TeamDetailModal
        team={selectedTeam}
        onClose={() => setSelectedTeam(null)}
      />
    </SafeAreaView>
  );
}

function LeagueCard({ league, expanded, onToggle, onTeamPress }) {
  return (
    <View
      style={[
        styles.leagueCard,
        expanded && styles.leagueCardExpanded,
      ]}
    >
      <TouchableOpacity
        style={styles.leagueHeader}
        onPress={onToggle}
        activeOpacity={0.7}
      >
        <View style={{ flex: 1 }}>
          <Text style={styles.leagueName}>{league.name}</Text>
          <Text style={styles.leagueCountry}>
            {league.country || '—'} · {league.code}
          </Text>
        </View>
        <View style={styles.leagueStatsRow}>
          <Stat value={league.team_count} label="equipos" />
          <Stat value={league.match_count} label="partidos" />
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={C.textMuted}
          />
        </View>
      </TouchableOpacity>

      {expanded && (
        <TeamsList leagueCode={league.code} onTeamPress={onTeamPress} />
      )}
    </View>
  );
}

function Stat({ value, label }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function TeamsList({ leagueCode, onTeamPress }) {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setError(null);
    api
      .getTeamsByLeague(leagueCode)
      .then((data) => {
        if (!ignore) setTeams(Array.isArray(data) ? data : []);
      })
      .catch((e) => {
        if (!ignore) setError(e.message);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [leagueCode]);

  if (loading) {
    return (
      <ActivityIndicator
        style={{ marginVertical: 12 }}
        color={C.accent}
      />
    );
  }

  if (error) {
    return <Text style={styles.teamsError}>{error}</Text>;
  }

  if (teams.length === 0) {
    return <Text style={styles.teamsEmpty}>Sin equipos cargados.</Text>;
  }

  return (
    <View style={styles.teamsGrid}>
      {teams.map((t) => (
        <TouchableOpacity
          key={t.id}
          style={styles.teamChip}
          onPress={() => onTeamPress?.(t)}
          activeOpacity={0.7}
        >
          <Text style={styles.teamChipText} numberOfLines={1}>
            {t.name}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, paddingBottom: 24 },
  loader: { marginTop: 32 },
  error: { color: C.error, textAlign: 'center', padding: 16 },
  subtitle: {
    color: C.textSecondary,
    fontSize: 13,
    marginBottom: 12,
  },

  leagueCard: {
    backgroundColor: C.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    marginBottom: 10,
    overflow: 'hidden',
  },
  leagueCardExpanded: {
    borderColor: C.accent,
  },
  leagueHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 8,
  },
  leagueName: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  leagueCountry: {
    color: C.textMuted,
    fontSize: 11,
    marginTop: 2,
    letterSpacing: 0.5,
  },
  leagueStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  stat: { alignItems: 'center' },
  statValue: {
    color: C.accent,
    fontFamily: 'monospace',
    fontWeight: '700',
    fontSize: 14,
  },
  statLabel: {
    color: C.textMuted,
    fontSize: 9,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },

  teamsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    padding: 12,
    paddingTop: 4,
    borderTopWidth: 1,
    borderTopColor: C.border,
  },
  teamChip: {
    backgroundColor: C.surfaceAlt,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    paddingHorizontal: 14,
    paddingVertical: 10,
    maxWidth: '100%',
  },
  teamChipText: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  teamsError: {
    color: C.error,
    fontSize: 12,
    padding: 12,
  },
  teamsEmpty: {
    color: C.textMuted,
    fontSize: 12,
    padding: 12,
    fontStyle: 'italic',
  },
});
