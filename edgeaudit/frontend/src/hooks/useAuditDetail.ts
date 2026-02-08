import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import type { AuditResult } from '../types/audit';

export function useAuditDetail(auditId: string | undefined) {
  const [data, setData] = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auditId) {
      setLoading(false);
      return;
    }

    let mounted = true;

    async function fetchAudit() {
      try {
        setLoading(true);
        const result = await apiService.getAuditDetail(auditId);
        if (mounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load audit details');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    fetchAudit();

    return () => {
      mounted = false;
    };
  }, [auditId]);

  return { data, loading, error };
}
