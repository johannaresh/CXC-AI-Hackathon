import type { AuditResult, AuditsListResponse, AuditsSummaryResponse } from '../types/audit';
import type { QueryParams } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiService {
  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(error.detail || 'An error occurred');
    }

    return response.json();
  }

  async getAuditsSummary(): Promise<AuditsSummaryResponse> {
    return this.fetch<AuditsSummaryResponse>('/audits/summary');
  }

  async getAuditsList(params?: QueryParams): Promise<AuditsListResponse> {
    const queryString = new URLSearchParams(
      Object.entries(params || {})
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();

    const endpoint = queryString ? `/audits?${queryString}` : '/audits';
    return this.fetch<AuditsListResponse>(endpoint);
  }

  async getAuditDetail(auditId: string): Promise<AuditResult> {
    return this.fetch<AuditResult>(`/audit/${auditId}`);
  }

  async submitAudit(payload: unknown): Promise<AuditResult> {
    return this.fetch<AuditResult>('/audit', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
}

export const apiService = new ApiService();
