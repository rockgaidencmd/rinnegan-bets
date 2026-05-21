import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api/client';
import { RinneganColors as C } from '../constants/Colors';

const DEBOUNCE_MS = 300;
const TZ = 'America/Guayaquil';

function formatFixtureDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString('es-EC', {
      timeZone: TZ,
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}

export default function PrediccionScreen() {
  const [mode, setMode] = useState('search'); // 'search' | 'fixtures'
  const [home, setHome] = useState(null);
  const [away, setAway] = useState(null);
  const [quota, setQuota] = useState('');
  const [stake, setStake] = useState('');
  const [predicting, setPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const canPredict =
    home &&
    away &&
    parseFloat(quota) > 1 &&
    parseFloat(stake) > 0;

  const runPredict = async () => {
    setPredicting(true);
    setResult(null);
    setError(null);
    try {
      const res = await api.predict({
        home_team: home.name,
        away_team: away.name,
        quota: parseFloat(quota),
        stake: parseFloat(stake),
      });
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setPredicting(false);
    }
  };

  const reset = () => {
    setHome(null);
    setAway(null);
    setQuota('');
    setStake('');
    setResult(null);
    setError(null);
  };

  const pickFromFixture = (fixture) => {
    if (!fixture.home_team_id || !fixture.away_team_id) {
      setError('Este partido aún no tiene equipos enlazados en BD.');
      return;
    }
    setHome({
      id: fixture.home_team_id,
      name: fixture.home_team_name,
      league: fixture.league,
    });
    setAway({
      id: fixture.away_team_id,
      name: fixture.away_team_name,
      league: fixture.league,
    });
    setMode('search');
    setError(null);
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.modeTabs}>
            <ModeTab
              icon="search"
              label="Buscar equipos"
              active={mode === 'search'}
              onPress={() => setMode('search')}
            />
            <ModeTab
              icon="calendar"
              label="Próximos partidos"
              active={mode === 'fixtures'}
              onPress={() => setMode('fixtures')}
            />
          </View>

          {mode === 'fixtures' && (
            <FixtureBrowser onPick={pickFromFixture} />
          )}

          {mode === 'search' && (
            <>
              <TeamPicker
                label="Equipo local"
                selected={home}
                onSelect={(t) => {
                  setHome(t);
                  if (away && away.league !== t.league) setAway(null);
                }}
                onClear={() => setHome(null)}
                allowedLeague={away?.league}
                excludeId={away?.id}
              />

              <TeamPicker
                label="Equipo visitante"
                selected={away}
                onSelect={(t) => {
                  setAway(t);
                  if (home && home.league !== t.league) setHome(null);
                }}
                onClear={() => setAway(null)}
                allowedLeague={home?.league}
                excludeId={home?.id}
              />

              <View style={styles.row}>
                <View style={styles.col}>
                  <Text style={styles.label}>Cuota</Text>
                  <TextInput
                    style={styles.input}
                    value={quota}
                    onChangeText={setQuota}
                    placeholder="2.50"
                    placeholderTextColor={C.textMuted}
                    keyboardType="decimal-pad"
                  />
                </View>
                <View style={styles.col}>
                  <Text style={styles.label}>Monto</Text>
                  <TextInput
                    style={styles.input}
                    value={stake}
                    onChangeText={setStake}
                    placeholder="10"
                    placeholderTextColor={C.textMuted}
                    keyboardType="decimal-pad"
                  />
                </View>
              </View>

              <TouchableOpacity
                style={[
                  styles.predictBtn,
                  !canPredict && styles.predictBtnDisabled,
                ]}
                onPress={runPredict}
                disabled={!canPredict || predicting}
              >
                <Text style={styles.predictBtnText}>
                  {predicting ? 'Calculando...' : 'Predecir'}
                </Text>
              </TouchableOpacity>

              {error && (
                <View style={styles.errorBox}>
                  <Ionicons name="alert-circle" size={18} color={C.error} />
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              )}

              {result && <ResultCard result={result} onReset={reset} />}
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// --- ModeTab: toggle entre "Buscar equipos" y "Próximos partidos" ---

function ModeTab({ icon, label, active, onPress }) {
  return (
    <TouchableOpacity
      style={[styles.modeTab, active && styles.modeTabActive]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Ionicons
        name={icon}
        size={16}
        color={active ? C.accent : C.textMuted}
      />
      <Text
        style={[
          styles.modeTabText,
          active && styles.modeTabTextActive,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

// --- FixtureBrowser: liga -> lista de fixtures próximos -> onPick ---

function FixtureBrowser({ onPick }) {
  const [leagues, setLeagues] = useState([]);
  const [league, setLeague] = useState('');
  const [fixtures, setFixtures] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .listLeagues()
      .then((d) => setLeagues(d.leagues || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!league) {
      setFixtures([]);
      return;
    }
    let ignore = false;
    setLoading(true);
    api
      .listFixtures({ league, days: 14, limit: 30 })
      .then((d) => {
        if (!ignore) setFixtures(d.fixtures || []);
      })
      .catch(() => {
        if (!ignore) setFixtures([]);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [league]);

  return (
    <View style={styles.section}>
      <Text style={styles.label}>Liga</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.leagueChipsRow}
      >
        {leagues.map((l) => (
          <TouchableOpacity
            key={l.code}
            style={[
              styles.leagueChip,
              league === l.code && styles.leagueChipActive,
            ]}
            onPress={() => setLeague(league === l.code ? '' : l.code)}
          >
            <Text
              style={[
                styles.leagueChipText,
                league === l.code && styles.leagueChipTextActive,
              ]}
            >
              {l.code}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {!league && (
        <Text style={styles.emptyHint}>
          Elige una liga para ver próximos partidos.
        </Text>
      )}

      {loading && (
        <ActivityIndicator
          style={{ marginTop: 16 }}
          color={C.accent}
        />
      )}

      {!loading && league && fixtures.length === 0 && (
        <Text style={styles.emptyHint}>
          No hay partidos programados en los próximos 14 días.
        </Text>
      )}

      {!loading && fixtures.length > 0 && (
        <View style={{ marginTop: 8 }}>
          {fixtures.map((f, i) => (
            <TouchableOpacity
              key={`${f.match_date}-${i}`}
              style={styles.fixtureCard}
              onPress={() => onPick(f)}
              activeOpacity={0.7}
            >
              <Text style={styles.fixtureDate}>
                {formatFixtureDate(f.match_date)}
              </Text>
              <View style={styles.fixtureTeams}>
                <Text
                  style={styles.fixtureTeam}
                  numberOfLines={1}
                >
                  {f.home_team_name}
                </Text>
                <Text style={styles.fixtureVs}>vs</Text>
                <Text
                  style={[styles.fixtureTeam, { textAlign: 'right' }]}
                  numberOfLines={1}
                >
                  {f.away_team_name}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

// --- TeamPicker: typeahead search ---

function TeamPicker({
  label,
  selected,
  onSelect,
  onClear,
  allowedLeague,
  excludeId,
}) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    if (selected || query.trim().length < 2) {
      setResults([]);
      return;
    }
    const id = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await api.searchTeams(query.trim());
        const filtered = (data.results || []).filter((t) => {
          // Bloqueamos elegir el mismo equipo en ambos lados,
          // y forzamos misma liga cuando el otro picker ya tiene equipo.
          if (excludeId && t.id === excludeId) return false;
          if (allowedLeague && t.league !== allowedLeague) return false;
          return true;
        });
        setResults(filtered);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [query, selected, allowedLeague, excludeId]);

  if (selected) {
    return (
      <View style={styles.section}>
        <Text style={styles.label}>{label}</Text>
        <View style={styles.selectedRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.selectedName}>{selected.name}</Text>
            <Text style={styles.selectedMeta}>{selected.league}</Text>
          </View>
          <TouchableOpacity
            onPress={() => {
              onClear();
              setQuery('');
            }}
            hitSlop={10}
          >
            <Ionicons
              name="close-circle"
              size={22}
              color={C.textMuted}
            />
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.section}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        value={query}
        onChangeText={setQuery}
        placeholder={
          allowedLeague
            ? `Buscar en ${allowedLeague}...`
            : 'Buscar equipo...'
        }
        placeholderTextColor={C.textMuted}
        autoCapitalize="words"
        autoCorrect={false}
      />
      {searching && (
        <ActivityIndicator
          size="small"
          color={C.accent}
          style={{ marginTop: 6 }}
        />
      )}
      {!searching &&
        query.trim().length >= 2 &&
        results.length === 0 &&
        allowedLeague && (
          <Text style={styles.emptyHint}>
            Ningún equipo de {allowedLeague} con ese nombre.
          </Text>
        )}
      {results.length > 0 && (
        <View style={styles.suggestions}>
          {results.map((t) => (
            <TouchableOpacity
              key={t.id}
              style={styles.suggestion}
              onPress={() => {
                onSelect(t);
                setQuery('');
                setResults([]);
              }}
            >
              <Text style={styles.suggestionName}>{t.name}</Text>
              <Text style={styles.suggestionMeta}>{t.league}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

// --- ResultCard ---

function ResultCard({ result, onReset }) {
  const verdictColor =
    result.verdict === 'apostar'
      ? C.success
      : result.verdict === 'esperar'
        ? C.warning
        : C.error;

  return (
    <View style={styles.resultCard}>
      <View style={[styles.verdictBadge, { borderColor: verdictColor }]}>
        <Text style={[styles.verdictText, { color: verdictColor }]}>
          {result.verdict.toUpperCase()}
        </Text>
      </View>

      <Text style={styles.matchup}>
        {result.home_team} <Text style={styles.vs}>vs</Text>{' '}
        {result.away_team}
      </Text>
      <Text style={styles.leagueLine}>
        {result.league} · {result.model_version}
      </Text>

      <View style={styles.metricsGrid}>
        <Metric label="Mi prob" value={`${(result.my_prob * 100).toFixed(1)}%`} />
        <Metric label="Implícita" value={`${(result.implied_prob * 100).toFixed(1)}%`} />
        <Metric
          label="Edge"
          value={`${(result.edge * 100).toFixed(1)}%`}
          highlight={result.edge > 0 ? C.success : C.error}
        />
        <Metric label="Pre-score" value={result.pre_score?.toFixed(1)} />
        <Metric
          label="EV"
          value={`$${result.ev.toFixed(2)}`}
          highlight={result.ev > 0 ? C.success : C.error}
        />
        <Metric
          label="Kelly"
          value={`${(result.kelly * 100).toFixed(1)}%`}
        />
      </View>

      <Text style={styles.reason}>{result.verdict_reason}</Text>

      <TouchableOpacity style={styles.resetBtn} onPress={onReset}>
        <Text style={styles.resetBtnText}>Nueva predicción</Text>
      </TouchableOpacity>
    </View>
  );
}

function Metric({ label, value, highlight }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text
        style={[
          styles.metricValue,
          highlight && { color: highlight },
        ]}
      >
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, gap: 16, paddingBottom: 32 },
  section: { gap: 6 },
  label: {
    color: C.textPrimary,
    fontSize: 12,
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
    fontSize: 14,
  },
  modeTabs: {
    flexDirection: 'row',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    padding: 4,
    marginBottom: 4,
  },
  modeTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 6,
  },
  modeTabActive: {
    backgroundColor: 'rgba(0, 245, 160, 0.12)',
  },
  modeTabText: {
    color: C.textMuted,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  modeTabTextActive: {
    color: C.accent,
  },

  leagueChipsRow: {
    gap: 6,
    paddingVertical: 2,
  },
  leagueChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
  },
  leagueChipActive: {
    borderColor: C.accent,
    backgroundColor: 'rgba(0, 245, 160, 0.12)',
  },
  leagueChipText: {
    color: C.textSecondary,
    fontSize: 12,
    fontWeight: '700',
  },
  leagueChipTextActive: {
    color: C.accent,
  },

  fixtureCard: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    padding: 12,
    marginBottom: 6,
  },
  fixtureDate: {
    color: C.textMuted,
    fontSize: 11,
    fontFamily: 'monospace',
    marginBottom: 6,
    textTransform: 'capitalize',
  },
  fixtureTeams: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  fixtureTeam: {
    flex: 1,
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '600',
  },
  fixtureVs: {
    color: C.textMuted,
    fontSize: 11,
    paddingHorizontal: 10,
  },

  row: { flexDirection: 'row', gap: 12 },
  col: { flex: 1, gap: 6 },

  selectedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.accent,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  selectedName: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  selectedMeta: {
    color: C.accent,
    fontSize: 11,
    marginTop: 2,
    letterSpacing: 0.5,
  },

  emptyHint: {
    color: C.textMuted,
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 6,
    paddingHorizontal: 4,
  },
  suggestions: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    marginTop: 6,
    overflow: 'hidden',
  },
  suggestion: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  suggestionName: {
    color: C.textPrimary,
    fontSize: 14,
    fontWeight: '600',
  },
  suggestionMeta: {
    color: C.textMuted,
    fontSize: 11,
    marginTop: 2,
  },

  predictBtn: {
    backgroundColor: C.accent,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  predictBtnDisabled: {
    backgroundColor: C.surfaceAlt,
  },
  predictBtnText: {
    color: C.bg,
    fontWeight: '800',
    letterSpacing: 1,
    fontSize: 14,
  },

  errorBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(255, 85, 119, 0.08)',
    borderWidth: 1,
    borderColor: C.error,
    padding: 12,
    borderRadius: 8,
  },
  errorText: { color: C.textPrimary, flex: 1 },

  resultCard: {
    backgroundColor: C.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    padding: 18,
    gap: 12,
  },
  verdictBadge: {
    alignSelf: 'center',
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 2,
  },
  verdictText: {
    fontWeight: '800',
    letterSpacing: 1.5,
    fontSize: 13,
  },
  matchup: {
    color: C.textPrimary,
    fontSize: 16,
    fontWeight: '700',
    textAlign: 'center',
  },
  vs: {
    color: C.textMuted,
    fontWeight: '400',
  },
  leagueLine: {
    color: C.textMuted,
    fontSize: 11,
    textAlign: 'center',
    letterSpacing: 0.5,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 4,
  },
  metric: {
    flexBasis: '31%',
    flexGrow: 1,
    backgroundColor: C.surfaceAlt,
    borderRadius: 6,
    padding: 10,
    alignItems: 'center',
    gap: 2,
  },
  metricLabel: {
    color: C.textMuted,
    fontSize: 10,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  metricValue: {
    color: C.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  reason: {
    color: C.textSecondary,
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    paddingHorizontal: 8,
  },
  resetBtn: {
    alignSelf: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  resetBtnText: {
    color: C.textMuted,
    fontSize: 12,
    letterSpacing: 0.5,
  },
});
