import { useParams, Link } from 'react-router-dom';
import { Container } from '../components/layout/Container';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Spinner } from '../components/ui/Spinner';
import { ErrorMessage } from '../components/ui/ErrorMessage';
import { EdgeScoreGauge } from '../components/charts/EdgeScoreGauge';
import { SubScoresBarChart } from '../components/charts/SubScoresBarChart';
import { RegimeChart } from '../components/charts/RegimeChart';
import { MonteCarloChart } from '../components/charts/MonteCarloChart';
import { useAuditDetail } from '../hooks/useAuditDetail';

export function DetailPage() {
  const { auditId } = useParams<{ auditId: string }>();
  const { data: audit, loading, error } = useAuditDetail(auditId);

  if (loading) {
    return (
      <Container>
        <Spinner />
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <ErrorMessage message={error} />
        <Link to="/" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
          ← Back to Dashboard
        </Link>
      </Container>
    );
  }

  if (!audit) {
    return (
      <Container>
        <ErrorMessage message="Audit not found" />
        <Link to="/" className="mt-4 inline-block text-primary-600 hover:text-primary-700">
          ← Back to Dashboard
        </Link>
      </Container>
    );
  }

  return (
    <Container>
      {/* Header */}
      <div className="mb-8">
        <Link to="/" className="text-primary-600 hover:text-primary-700 mb-4 inline-block">
          ← Back to Dashboard
        </Link>
        <h1 className="text-3xl font-bold text-gray-900">{audit.strategy_name}</h1>
        <div className="mt-2 flex items-center gap-4">
          <Badge label={audit.overfit_score.label} />
          <span className="text-sm text-gray-600">Audit ID: {audit.audit_id}</span>
        </div>
      </div>

      {/* Edge Score Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <h2 className="text-xl font-semibold mb-4">Edge Score</h2>
          <EdgeScoreGauge score={audit.edge_score.edge_score} />
        </Card>

        <Card>
          <h2 className="text-xl font-semibold mb-4">Overfit Analysis</h2>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-gray-600">Probability</p>
              <p className="text-2xl font-bold text-gray-900">
                {(audit.overfit_score.probability * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Confidence</p>
              <p className="text-2xl font-bold text-gray-900">
                {(audit.overfit_score.confidence * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Risk Level</p>
              <Badge label={audit.overfit_score.label} />
            </div>
          </div>
        </Card>
      </div>

      {/* Sub-Scores */}
      <Card className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Score Breakdown</h2>
        <SubScoresBarChart scores={audit.edge_score} />
      </Card>

      {/* Monte Carlo & Regime Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <MonteCarloChart monteCarlo={audit.monte_carlo} />

        <Card>
          <h3 className="text-lg font-semibold mb-4">Regime Analysis</h3>
          <RegimeChart regime={audit.regime_analysis} />
        </Card>
      </div>

      {/* AI Narrative */}
      <Card className="mb-8">
        <h2 className="text-xl font-semibold mb-4">AI Narrative</h2>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{audit.narrative}</p>
        </div>
      </Card>

      {/* Recommendations */}
      {audit.recommendations && audit.recommendations.length > 0 && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Recommendations</h2>
          <ul className="space-y-2">
            {audit.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-primary-600 mr-2">•</span>
                <span className="text-gray-700">{rec}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </Container>
  );
}
