import { useState, useCallback } from 'react';
import { Container } from '../components/layout/Container';
import { KPICard } from '../components/dashboard/KPICard';
import { FilterBar } from '../components/dashboard/FilterBar';
import { AuditsTable } from '../components/dashboard/AuditsTable';
import { Spinner } from '../components/ui/Spinner';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { useSummary } from '../hooks/useSummary';
import { useAudits } from '../hooks/useAudits';

export function DashboardPage() {
  const [filterParams, setFilterParams] = useState({
    page: 1,
    page_size: 20,
    strategy_name: '',
    sort_by: 'submitted_at' as const,
    sort_order: 'desc' as const,
  });

  const { data: summary, loading: summaryLoading, error: summaryError } = useSummary();
  const { data: audits, loading: auditsLoading, error: auditsError } = useAudits(filterParams);

  const handleFilterChange = useCallback((strategyName: string) => {
    setFilterParams(prev => ({ ...prev, strategy_name: strategyName, page: 1 }));
  }, []);

  const handleSortChange = useCallback((sortBy: string, sortOrder: string) => {
    setFilterParams(prev => ({
      ...prev,
      sort_by: sortBy as any,
      sort_order: sortOrder as any,
      page: 1,
    }));
  }, []);

  return (
    <Container>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Audit Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Overview of all strategy audits and performance metrics
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {summaryLoading ? (
          <div className="col-span-4">
            <Spinner />
          </div>
        ) : summaryError ? (
          <div className="col-span-4">
            <ErrorMessage message={summaryError} />
          </div>
        ) : summary ? (
          <>
            <KPICard
              title="Total Audits"
              value={summary.total_audits}
              subtitle={`${summary.unique_strategies} unique strategies`}
            />
            <KPICard
              title="Avg Edge Score"
              value={summary.average_edge_score.toFixed(1)}
              subtitle="Out of 100"
            />
            <KPICard
              title="High Risk"
              value={summary.high_risk_count}
              subtitle={`${summary.medium_risk_count} medium, ${summary.low_risk_count} low`}
            />
            <KPICard
              title="Avg Overfit Risk"
              value={`${(summary.average_overfit_probability * 100).toFixed(1)}%`}
              subtitle="Across all audits"
            />
          </>
        ) : null}
      </div>

      {/* Filters */}
      <FilterBar
        onFilterChange={handleFilterChange}
        onSortChange={handleSortChange}
      />

      {/* Audits Table */}
      {auditsLoading ? (
        <Spinner />
      ) : auditsError ? (
        <ErrorMessage message={auditsError} />
      ) : audits && audits.audits.length > 0 ? (
        <>
          <AuditsTable audits={audits.audits} />

          {/* Pagination */}
          <div className="mt-6 flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {(audits.page - 1) * audits.page_size + 1} to{' '}
              {Math.min(audits.page * audits.page_size, audits.total)} of {audits.total} results
            </p>

            <div className="flex gap-2">
              <button
                onClick={() => setFilterParams(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={audits.page === 1}
                className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <button
                onClick={() => setFilterParams(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={audits.page * audits.page_size >= audits.total}
                className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No audits found</p>
        </div>
      )}
    </Container>
  );
}
