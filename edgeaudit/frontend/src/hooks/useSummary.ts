import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { AuditsSummaryResponse } from '../types/audit';

export function useSummary() {
  const [data, setData] = useState<AuditsSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchSummary() {
      try {
        setLoading(true);
        const result = await apiService.getAuditsSummary();
        if (mounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load summary');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchSummary();

    return () => {
      mounted = false;
    };
  }, []);

  return { data, loading, error };
}
