import { useBankroll } from '../hooks/useBankroll.js';
import { usePredictionForm } from '../hooks/usePredictionForm.js';
import { ContextStep } from './ContextStep.jsx';
import { FixturePicker } from './FixturePicker.jsx';
import { PredictionResult } from './PredictionResult.jsx';
import { QuotaStakeStep } from './QuotaStakeStep.jsx';


/**
 * SmartPredict — orchestrates the 3-step prediction flow.
 *
 * All form state lives in usePredictionForm (a single source of truth
 * accessible without prop-drilling through the steps).
 */
export function SmartPredict() {
  const { balance } = useBankroll();
  const form = usePredictionForm();

  if (form.prediction) {
    return (
      <PredictionResult
        prediction={form.prediction}
        availableBalance={balance?.available || 0}
        homeTeam={form.home}
        awayTeam={form.away}
        onReset={form.reset}
      />
    );
  }

  return (
    <>
      <FixturePicker
        home={form.home}
        away={form.away}
        onHomeChange={form.setHome}
        onAwayChange={form.setAway}
      />

      <ContextStep
        importance={form.importance}
        onImportanceChange={form.setImportance}
        homeAbsences={form.homeAbsences}
        onHomeAbsencesChange={form.setHomeAbsences}
        awayAbsences={form.awayAbsences}
        onAwayAbsencesChange={form.setAwayAbsences}
      />

      <QuotaStakeStep
        quota={form.quota}
        onQuotaChange={form.setQuota}
        stake={form.stake}
        onStakeChange={form.setStake}
      />

      {form.error && (
        <div className="card" style={{ borderColor: 'var(--red)' }}>
          <div style={{ color: 'var(--red)' }}>❌ {form.error}</div>
        </div>
      )}

      <button
        className="btn btn-green"
        onClick={form.submit}
        disabled={!form.canPredict || form.loading}
        type="button"
      >
        {form.loading ? 'Analizando...' : 'Predecir →'}
      </button>
    </>
  );
}
