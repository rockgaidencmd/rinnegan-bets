import './styles/app.css';
import { Header } from './components/Header.jsx';
import { MatchSelector } from './components/MatchSelector.jsx';
import { PhaseStepper } from './components/PhaseStepper.jsx';
import { PreMatchPhase } from './components/PreMatchPhase.jsx';
import { ContextPhase } from './components/ContextPhase.jsx';
import { LivePhase } from './components/LivePhase.jsx';
import { useMatchState } from './hooks/useMatchState.js';

export default function App() {
  const state = useMatchState();
  const match = state.match;

  return (
    <div className="app">
      <Header />
      <MatchSelector matches={state.matches} active={state.active} onSelect={state.setActive} onAdd={state.addMatch} />
      <PhaseStepper currentPhase={match.phase} onPhaseChange={state.setPhase} />

      {match.phase === 0 && (
        <PreMatchPhase
          match={match}
          onMatchChange={state.setMatch}
          onPhaseChange={state.setPhase}
        />
      )}

      {match.phase === 1 && (
        <ContextPhase
          match={match}
          onMatchChange={state.setMatch}
          preScore={state.preScore}
          quota={state.quota}
          stake={state.stake}
          impliedProb={state.impliedProb}
          myProb={state.myProb}
          ev={state.ev}
          onPhaseChange={state.setPhase}
        />
      )}

      {match.phase === 2 && (
        <LivePhase
          match={match}
          onMatchChange={state.setMatch}
          finalScore={state.finalScore}
          verdict={state.verdict}
          liveEV={state.liveEV}
          liveImpliedProb={state.liveImpliedProb}
          liveMyProb={state.liveMyProb}
          liveEdge={state.liveEdge}
          quota={state.quota}
          liveQuota={state.liveQuota}
          onPhaseChange={state.setPhase}
        />
      )}
    </div>
  );
}
