import { useCallback, useState } from 'react';
import { api, ApiError } from '../utils/api.js';


/**
 * usePredictionForm — manages the prediction form's state machine.
 *
 * Single hook owns all form state + the API call. Components just
 * render and dispatch — no duplication of validation/loading logic
 * across child components.
 */
export function usePredictionForm() {
  const [home, setHome] = useState(null);
  const [away, setAway] = useState(null);
  const [importance, setImportance] = useState('normal');
  const [homeAbsences, setHomeAbsences] = useState(false);
  const [awayAbsences, setAwayAbsences] = useState(false);
  const [quota, setQuota] = useState('');
  const [stake, setStake] = useState('10');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Derived during render — no effects needed
  const quotaNum = parseFloat(quota);
  const stakeNum = parseFloat(stake);
  const canPredict =
    !!home && !!away &&
    Number.isFinite(quotaNum) && quotaNum > 1 &&
    Number.isFinite(stakeNum) && stakeNum > 0;

  const reset = useCallback(() => {
    setHome(null);
    setAway(null);
    setImportance('normal');
    setHomeAbsences(false);
    setAwayAbsences(false);
    setQuota('');
    setStake('10');
    setPrediction(null);
    setError(null);
  }, []);

  const submit = useCallback(async () => {
    if (!canPredict) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.predict({
        home_team: home.name,
        away_team: away.name,
        quota: quotaNum,
        stake: stakeNum,
        importance,
        home_key_absences: homeAbsences,
        away_key_absences: awayAbsences,
      });
      setPrediction(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : 'Error inesperado. ¿Backend corriendo?',
      );
    } finally {
      setLoading(false);
    }
  }, [
    canPredict, home, away, quotaNum, stakeNum,
    importance, homeAbsences, awayAbsences,
  ]);

  return {
    // State
    home, setHome,
    away, setAway,
    importance, setImportance,
    homeAbsences, setHomeAbsences,
    awayAbsences, setAwayAbsences,
    quota, setQuota,
    stake, setStake,
    prediction, loading, error,
    // Derived
    canPredict,
    // Actions
    submit,
    reset,
  };
}
