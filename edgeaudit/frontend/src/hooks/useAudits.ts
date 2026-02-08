import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { AuditsListResponse } from '../types/audit';
import type { QueryParams } from '../types/api';

export function useAudits(params?: QueryParams) {
  const [data, setData] = useState<AuditsListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function fetchAudits() {
      try {
        setLoading(true);
        const result = await apiService.getAuditsList(params);
        if (mounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load audits');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchAudits();

    return () => {
      mounted = false;
    };
  }, [params?.page, params?.page_size, params?.strategy_name, params?.sort_by, params?.sort_order]);

  const refetch = () => {
    setLoading(true);
    apiService.getAuditsList(params)
      .then(result => {
        setData(result);
        setError(null);
      })
      .catch(err => {
        setError(err instanceof Error ? err.message : 'Failed to load audits');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return { data, loading, error, refetch };
}
