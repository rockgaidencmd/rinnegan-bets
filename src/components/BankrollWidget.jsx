import { useState } from 'react';
import { useBankroll } from '../hooks/useBankroll.js';


/**
 * BankrollWidget — header strip showing current balance + quick deposit/withdraw.
 */
export function BankrollWidget() {
  const { balance, loading, error, deposit, withdraw } = useBankroll();
  const [showActions, setShowActions] = useState(false);
  const [amount, setAmount] = useState('');
  const [actionError, setActionError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const handleAction = async (type) => {
    const value = parseFloat(amount);
    if (!Number.isFinite(value) || value <= 0) {
      setActionError('Ingresa un monto válido');
      return;
    }
    setActionLoading(true);
    setActionError(null);
    try {
      if (type === 'deposit') {
        await deposit(value);
      } else {
        await withdraw(value);
      }
      setAmount('');
      setShowActions(false);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="bankroll-widget bankroll-loading">Cargando bankroll...</div>;
  }

  if (error) {
    return (
      <div className="bankroll-widget bankroll-error">
        ❌ Sin conexión al backend ({error.message})
        <div className="bankroll-hint">¿Está corriendo en http://localhost:8000?</div>
      </div>
    );
  }

  return (
    <div className="bankroll-widget">
      <div className="bankroll-row">
        <div className="bankroll-summary">
          <span className="bankroll-label">Bankroll</span>
          <span className="bankroll-value mono">${balance.current.toFixed(2)}</span>
        </div>
        <div className="bankroll-summary">
          <span className="bankroll-label">Disponible</span>
          <span className="bankroll-value mono">${balance.available.toFixed(2)}</span>
        </div>
        {balance.pending_commitment > 0 && (
          <div className="bankroll-summary">
            <span className="bankroll-label">Comprometido</span>
            <span className="bankroll-value mono">${balance.pending_commitment.toFixed(2)}</span>
          </div>
        )}
        <button className="bankroll-toggle" onClick={() => setShowActions(!showActions)} type="button">
          {showActions ? '−' : '+'}
        </button>
      </div>
      {showActions && (
        <div className="bankroll-actions">
          <input
            className="inp"
            type="number"
            placeholder="Monto"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            min="0"
            step="1"
          />
          <button
            className="btn-small btn-green"
            onClick={() => handleAction('deposit')}
            disabled={actionLoading || !amount}
            type="button"
          >
            Depositar
          </button>
          <button
            className="btn-small btn-outline"
            onClick={() => handleAction('withdraw')}
            disabled={actionLoading || !amount}
            type="button"
          >
            Retirar
          </button>
          {actionError && <span className="bankroll-error-msg">{actionError}</span>}
        </div>
      )}
    </div>
  );
}
