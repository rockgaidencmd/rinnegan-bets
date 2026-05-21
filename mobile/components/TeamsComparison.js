import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../api/client';
import { RinneganColors as C } from '../constants/Colors';
import TeamDetailModal from './TeamDetailModal';

function useTeamStats(team) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!team?.id) return;
    let ignore = false;
    setLoading(true);
    api
      .getTeamStats(team.id)
      .then((s) => {
        if (!ignore) setStats(s);
      })
      .catch(() => {
        if (!ignore) setStats(null);
      })
      .finally(() => {
        if (!ignore) setLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [team?.id]);

  return { stats, loading };
}

export default function TeamsComparison({ home, away }) {
  const homeData = useTeamStats(home);
  const awayData = useTeamStats(away);
  const [detailTeam, setDetailTeam] = useState(null);

  if (homeData.loading || awayData.loading) {
    return (
      <View style={styles.card}>
        <ActivityIndicator color={C.accent} />
        <Text style={styles.loadingText}>Cargando stats...</Text>
      </View>
    );
  }

  if (!homeData.stats || !awayData.stats) return null;

  const hs = homeData.stats;
  const as = awayData.stats;
  const hasXg = hs.avg_xg_for != null && as.avg_xg_for != null;

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.title}>COMPARACIÓN</Text>

        <View style={styles.headerRow}>
          <View style={styles.headerCol}>
            <Text style={styles.teamName} numberOfLines={1}>
              {home.name}
            </Text>
            <Text style={styles.teamRole}>LOCAL</Text>
          </View>
          <View style={styles.headerCol}>
            <Text
              style={[styles.teamName, { textAlign: 'right' }]}
              numberOfLines={1}
            >
              {away.name}
            </Text>
            <Text style={[styles.teamRole, { textAlign: 'right' }]}>
              VISITANTE
            </Text>
          </View>
        </View>

        <Row
          label="Forma (G/E/P)"
          home={`${hs.wins}G ${hs.draws}E ${hs.losses}P`}
          away={`${as.wins}G ${as.draws}E ${as.losses}P`}
        />
        <Row
          label="Score de forma"
          home={hs.form_score.toFixed(0)}
          away={as.form_score.toFixed(0)}
          homeNum={hs.form_score}
          awayNum={as.form_score}
          higherIsBetter
        />
        <Row
          label="Goles a favor /p"
          home={hs.avg_goals_for.toFixed(2)}
          away={as.avg_goals_for.toFixed(2)}
          homeNum={hs.avg_goals_for}
          awayNum={as.avg_goals_for}
          higherIsBetter
        />
        <Row
          label="Goles concedidos /p"
          home={hs.avg_goals_against.toFixed(2)}
          away={as.avg_goals_against.toFixed(2)}
          homeNum={hs.avg_goals_against}
          awayNum={as.avg_goals_against}
          higherIsBetter={false}
        />
        {hasXg && (
          <Row
            label="xG /p"
            home={hs.avg_xg_for.toFixed(2)}
            away={as.avg_xg_for.toFixed(2)}
            homeNum={hs.avg_xg_for}
            awayNum={as.avg_xg_for}
            higherIsBetter
          />
        )}

        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={styles.detailBtn}
            onPress={() => setDetailTeam(home)}
          >
            <Ionicons name="time-outline" size={14} color={C.accent} />
            <Text style={styles.detailBtnText} numberOfLines={1}>
              Últimos partidos · Local
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.detailBtn}
            onPress={() => setDetailTeam(away)}
          >
            <Ionicons name="time-outline" size={14} color={C.accent} />
            <Text style={styles.detailBtnText} numberOfLines={1}>
              Últimos partidos · Visit
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <TeamDetailModal
        team={detailTeam}
        onClose={() => setDetailTeam(null)}
      />
    </>
  );
}

function pickWinner({ higherIsBetter, homeNum, awayNum }) {
  if (higherIsBetter === undefined || homeNum == null || awayNum == null) {
    return { homeBetter: false, awayBetter: false };
  }
  if (homeNum === awayNum) return { homeBetter: false, awayBetter: false };
  const homeWins = higherIsBetter ? homeNum > awayNum : homeNum < awayNum;
  return { homeBetter: homeWins, awayBetter: !homeWins };
}

function Row({ label, home, away, homeNum, awayNum, higherIsBetter }) {
  const { homeBetter, awayBetter } = pickWinner({
    higherIsBetter,
    homeNum,
    awayNum,
  });
  return (
    <View style={styles.row}>
      <Text
        style={[
          styles.value,
          { textAlign: 'left' },
          homeBetter && styles.valueWinner,
        ]}
      >
        {home}
      </Text>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text
        style={[
          styles.value,
          { textAlign: 'right' },
          awayBetter && styles.valueWinner,
        ]}
      >
        {away}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    padding: 14,
    gap: 8,
  },
  title: {
    color: C.textMuted,
    fontSize: 11,
    letterSpacing: 1,
    fontWeight: '700',
    marginBottom: 6,
  },
  loadingText: {
    color: C.textMuted,
    fontSize: 12,
    marginTop: 8,
    textAlign: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  },
  headerCol: { flex: 1 },
  teamName: {
    color: C.textPrimary,
    fontSize: 14,
    fontWeight: '700',
  },
  teamRole: {
    color: C.accent,
    fontSize: 10,
    letterSpacing: 1,
    marginTop: 2,
  },

  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  rowLabel: {
    flex: 1.4,
    color: C.textMuted,
    fontSize: 11,
    textAlign: 'center',
    letterSpacing: 0.3,
    paddingHorizontal: 6,
  },
  value: {
    flex: 1,
    color: C.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  valueWinner: {
    color: C.accent,
  },

  actionsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: C.border,
  },
  detailBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 6,
  },
  detailBtnText: {
    color: C.accent,
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
});
