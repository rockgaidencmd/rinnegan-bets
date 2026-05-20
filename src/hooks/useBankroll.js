import { useCallback, useEffect, useState } from 'react';
import { api, ApiError } from '../utils/api.js';


/**
 * useBankroll — loads current balance on mount, exposes mutations.
 *
 * Returns: { balance, loading, error, deposit, withdraw, refresh }
 */
export function useBankroll() {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBankroll();
      setBalance(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    let ignore = false;
    (async () => {
      try {
        const data = await api.getBankroll();
        if (!ignore) {
          setBalance(data);
        }
      } catch (err) {
        if (!ignore) {
          setError(err);
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    })();
    return () => { ignore = true; };
  }, []);

  const deposit = useCallback(async (amount) => {
    await api.deposit(amount);
    await refresh();
  }, [refresh]);

  const withdraw = useCallback(async (amount) => {
    await api.withdraw(amount);
    await refresh();
  }, [refresh]);

  return { balance, loading, error, deposit, withdraw, refresh };
}
