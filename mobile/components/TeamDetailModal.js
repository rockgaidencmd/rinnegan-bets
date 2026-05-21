import React, { useEffect, useState } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api/client';
import { RinneganColors as C } from '../constants/Colors';

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

function resultFor(match, teamId) {
  if (match.home_goals == null || match.away_goals == null) return null;
  const isHome = match.home_team_id === teamId;
  const my = isHome ? match.home_goals : match.away_goals;
  const op = isHome ? match.away_goals : match.home_goals;
  if (my > op) return 'G';
  if (my < op) return 'P';
  return 'E';
}

export default function TeamDetailModal({ team, onClose }) {
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Mantenemos el último team válido para que el body no crashee
  // durante la animación de cierre del Modal (team pasa a null pero
  // el contenido sigue en pantalla unos frames).
  const [renderTeam, setRenderTeam] = useState(team);

  useEffect(() => {
    if (!team) return;
    setRenderTeam(team);
    let ignore = false;
    setLoading(true);
    setError(null);
    Promise.all([
      api.getTeamStats(team.id),
      api.listMatches({ team_id: team.id, limit: 10 }),
    ])
      .then(([s, m]) => {
        if (ignore) return;
        setStats(s);
        setMatches(m.matches || []);
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
  }, [team]);

  return (
    <Modal
      visible={!!team}
      animationType="slide"
      transparent
      onRequestClose={onClose}
    >
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <View style={styles.header}>
            <View style={{ flex: 1 }}>
              <Text style={styles.teamName}>{renderTeam?.name}</Text>
              <Text style={styles.teamMeta}>
                {renderTeam?.league} · {renderTeam?.country || '—'}
              </Text>
            </View>
            <TouchableOpacity onPress={onClose} hitSlop={12}>
              <Ionicons name="close" size={26} color={C.textPrimary} />
            </TouchableOpacity>
          </View>

          <ScrollView contentContainerStyle={styles.body}>
            {loading && (
              <ActivityIndicator
                style={{ marginTop: 24 }}
                color={C.accent}
                size="large"
              />
            )}

            {!loading && error && (
              <Text style={styles.error}>{error}</Text>
            )}

            {!loading && stats && renderTeam && (
              <>
                <Section title={`Últimos ${stats.matches_analyzed} partidos`}>
                  <View style={styles.statsRow}>
                    <StatMini value={`${stats.wins}G`} label="Gana" color={C.success} />
                    <StatMini value={`${stats.draws}E`} label="Emp" color={C.warning} />
                    <StatMini value={`${stats.losses}P`} label="Pier" color={C.error} />
                    <StatMini
                      value={stats.form_score?.toFixed(0)}
                      label="Forma"
                    />
                  </View>
                  <View style={[styles.statsRow, { marginTop: 8 }]}>
                    <StatMini
                      value={stats.avg_goals_for?.toFixed(2)}
                      label="GF/p"
                    />
                    <StatMini
                      value={stats.avg_goals_against?.toFixed(2)}
                      label="GC/p"
                    />
                    {stats.avg_xg_for != null && (
                      <StatMini
                        value={stats.avg_xg_for?.toFixed(2)}
                        label="xG/p"
                      />
                    )}
                    {stats.avg_xg_against != null && (
                      <StatMini
                        value={stats.avg_xg_against?.toFixed(2)}
                        label="xGc/p"
                      />
                    )}
                  </View>
                </Section>

                {matches.length > 0 && (
                  <Section title={`Últimos ${matches.length} partidos jugados`}>
                    {matches.map((m) => {
                      const r = resultFor(m, renderTeam.id);
                      const isHome = m.home_team_id === renderTeam.id;
                      const rival = isHome ? m.away_team_name : m.home_team_name;
                      return (
                        <View key={m.id} style={styles.matchRow}>
                          <Text style={styles.matchDate}>
                            {formatDateShort(m.match_date)}
                          </Text>
                          <View
                            style={[
                              styles.resultBadge,
                              r === 'G' && { backgroundColor: C.success },
                              r === 'P' && { backgroundColor: C.error },
                              r === 'E' && { backgroundColor: C.warning },
                            ]}
                          >
                            <Text style={styles.resultBadgeText}>
                              {r || '—'}
                            </Text>
                          </View>
                          <Text style={styles.matchVs} numberOfLines={1}>
                            {isHome ? 'vs' : '@'} {rival}
                          </Text>
                          <Text style={styles.matchScore}>
                            {m.home_goals}-{m.away_goals}
                          </Text>
                        </View>
                      );
                    })}
                  </Section>
                )}
              </>
            )}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function StatMini({ value, label, color }) {
  return (
    <View style={styles.statMini}>
      <Text
        style={[
          styles.statMiniValue,
          color && { color },
        ]}
      >
        {value}
      </Text>
      <Text style={styles.statMiniLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: C.bg,
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    maxHeight: '88%',
    borderTopWidth: 1,
    borderColor: C.border,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  teamName: {
    color: C.textPrimary,
    fontSize: 18,
    fontWeight: '800',
  },
  teamMeta: {
    color: C.accent,
    fontSize: 12,
    marginTop: 2,
    letterSpacing: 0.5,
  },
  body: { padding: 16, paddingBottom: 32 },
  error: { color: C.error, textAlign: 'center', padding: 16 },

  section: { marginBottom: 20 },
  sectionTitle: {
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  statsRow: { flexDirection: 'row', gap: 6 },
  statMini: {
    flex: 1,
    backgroundColor: C.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    padding: 10,
    alignItems: 'center',
  },
  statMiniValue: {
    color: C.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  statMiniLabel: {
    color: C.textMuted,
    fontSize: 10,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginTop: 2,
  },

  matchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    gap: 10,
  },
  matchDate: {
    color: C.textMuted,
    fontSize: 11,
    fontFamily: 'monospace',
    width: 50,
  },
  resultBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.surfaceAlt,
  },
  resultBadgeText: {
    color: C.bg,
    fontSize: 11,
    fontWeight: '800',
  },
  matchVs: {
    flex: 1,
    color: C.textPrimary,
    fontSize: 13,
  },
  matchScore: {
    color: C.accent,
    fontFamily: 'monospace',
    fontWeight: '700',
    fontSize: 13,
  },
});
