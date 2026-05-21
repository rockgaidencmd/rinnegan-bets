import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';
import { RinneganColors as C } from '../constants/Colors';

const PAGE_SIZE = 25;
const TZ = 'America/Guayaquil';

function formatDateShort(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('es-EC', {
      timeZone: TZ,
      day: '2-digit',
      month: 'short',
    });
  } catch {
    return '—';
  }
}

export default function PartidosScreen() {
  const [matches, setMatches] = useState([]);
  const [totalAvailable, setTotalAvailable] = useState(0);
  const [filterLeague, setFilterLeague] = useState('');
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Cargar catálogo de ligas una sola vez
  useEffect(() => {
    let ignore = false;
    api
      .listLeagues()
      .then((data) => {
        if (!ignore) setLeagues(data.leagues || []);
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, []);

  const fetchPage = useCallback(
    async (offset) => {
      return api.listMatches({
        league: filterLeague || undefined,
        limit: PAGE_SIZE,
        offset,
      });
    },
    [filterLeague],
  );

  // Reset al cambiar filtro
  useEffect(() => {
    let ignore = false;
    setLoading(true);
    setError(null);
    fetchPage(0)
      .then((data) => {
        if (ignore) return;
        setMatches(data.matches);
        setTotalAvailable(data.total_available);
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
  }, [fetchPage]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const data = await fetchPage(0);
      setMatches(data.matches);
      setTotalAvailable(data.total_available);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  }, [fetchPage]);

  const loadMore = useCallback(async () => {
    if (loadingMore || matches.length >= totalAvailable) return;
    setLoadingMore(true);
    try {
      const data = await fetchPage(matches.length);
      setMatches((prev) => [...prev, ...data.matches]);
      setTotalAvailable(data.total_available);
    } catch {
      // best-effort
    } finally {
      setLoadingMore(false);
    }
  }, [fetchPage, loadingMore, matches.length, totalAvailable]);

  const renderItem = ({ item: m }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <Text style={styles.date}>{formatDateShort(m.match_date)}</Text>
        <Text style={styles.leagueChip}>{m.league}</Text>
      </View>
      <View style={styles.teamsRow}>
        <Text
          style={[styles.team, styles.teamHome]}
          numberOfLines={1}
        >
          {m.home_team_name}
        </Text>
        <Text style={styles.score}>
          {m.home_goals}-{m.away_goals}
        </Text>
        <Text
          style={[styles.team, styles.teamAway]}
          numberOfLines={1}
        >
          {m.away_team_name}
        </Text>
      </View>
      {m.home_xg !== null && m.home_xg !== undefined && (
        <Text style={styles.xg}>
          xG: {m.home_xg?.toFixed(2)} - {m.away_xg?.toFixed(2)}
        </Text>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <View style={styles.header}>
        <Text style={styles.subtitle}>
          {matches.length} de {totalAvailable} resultados
        </Text>
      </View>

      <View style={styles.filterRow}>
        <FilterChip
          label="Todas"
          active={!filterLeague}
          onPress={() => setFilterLeague('')}
        />
        {leagues.map((l) => (
          <FilterChip
            key={l.code}
            label={l.code}
            active={filterLeague === l.code}
            onPress={() =>
              setFilterLeague(filterLeague === l.code ? '' : l.code)
            }
          />
        ))}
      </View>

      {loading && !refreshing && (
        <ActivityIndicator
          style={styles.loader}
          size="large"
          color={C.accent}
        />
      )}

      {!loading && error && (
        <Text style={styles.error}>{error}</Text>
      )}

      {!loading && !error && matches.length === 0 && (
        <Text style={styles.empty}>No hay partidos para este filtro.</Text>
      )}

      <FlatList
        data={matches}
        keyExtractor={(m) => String(m.id)}
        renderItem={renderItem}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={C.accent}
          />
        }
        onEndReached={loadMore}
        onEndReachedThreshold={0.4}
        ListFooterComponent={
          loadingMore ? (
            <ActivityIndicator
              style={styles.footerLoader}
              color={C.accent}
            />
          ) : null
        }
      />
    </SafeAreaView>
  );
}

function FilterChip({ label, active, onPress }) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.chip, active && styles.chipActive]}
    >
      <Text
        style={[styles.chipText, active && styles.chipTextActive]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  subtitle: {
    color: C.textSecondary,
    fontSize: 13,
    letterSpacing: 0.5,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 6,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
  },
  chipActive: {
    borderColor: C.accent,
    backgroundColor: 'rgba(0, 245, 160, 0.12)',
  },
  chipText: {
    color: C.textSecondary,
    fontSize: 12,
    fontWeight: '600',
  },
  chipTextActive: {
    color: C.accent,
  },
  list: {
    padding: 12,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: C.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: C.border,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  date: {
    color: C.textMuted,
    fontSize: 12,
    fontFamily: 'monospace',
  },
  leagueChip: {
    color: C.accent,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    backgroundColor: 'rgba(0, 245, 160, 0.1)',
  },
  teamsRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  team: {
    flex: 1,
    color: C.textPrimary,
    fontSize: 14,
    fontWeight: '600',
  },
  teamHome: {
    textAlign: 'left',
  },
  teamAway: {
    textAlign: 'right',
  },
  score: {
    color: C.accent,
    fontSize: 18,
    fontWeight: '800',
    fontFamily: 'monospace',
    paddingHorizontal: 12,
  },
  xg: {
    color: C.textMuted,
    fontSize: 11,
    fontFamily: 'monospace',
    marginTop: 6,
    textAlign: 'center',
  },
  loader: {
    marginTop: 32,
  },
  footerLoader: {
    marginVertical: 16,
  },
  error: {
    color: C.error,
    textAlign: 'center',
    padding: 16,
  },
  empty: {
    color: C.textMuted,
    textAlign: 'center',
    padding: 24,
  },
});
