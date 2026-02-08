import type { MonteCarloResult } from '../../types/audit';
import { Card } from '../ui/Card';

interface MonteCarloChartProps {
  monteCarlo: MonteCarloResult;
}

export function MonteCarloChart({ monteCarlo }: MonteCarloChartProps) {
  const {
    simulated_sharpe_mean,
    simulated_sharpe_std,
    p_value,
    confidence_interval_95,
    num_simulations
  } = monteCarlo;

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Monte Carlo Analysis</h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">Simulated Mean</p>
          <p className="text-2xl font-bold text-gray-900">{simulated_sharpe_mean.toFixed(3)}</p>
        </div>

        <div>
          <p className="text-sm text-gray-600">Std Deviation</p>
          <p className="text-2xl font-bold text-gray-900">{simulated_sharpe_std.toFixed(3)}</p>
        </div>

        <div>
          <p className="text-sm text-gray-600">P-Value</p>
          <p className={`text-2xl font-bold ${
            p_value < 0.05 ? 'text-success-600' : 'text-warning-600'
          }`}>
            {p_value.toFixed(4)}
          </p>
        </div>

        <div>
          <p className="text-sm text-gray-600">Simulations</p>
          <p className="text-2xl font-bold text-gray-900">{num_simulations.toLocaleString()}</p>
        </div>
      </div>

      {confidence_interval_95.length === 2 && (
        <div className="mt-4 p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">95% Confidence Interval</p>
          <p className="text-lg font-semibold text-gray-900">
            [{confidence_interval_95[0].toFixed(3)}, {confidence_interval_95[1].toFixed(3)}]
          </p>
        </div>
      )}
    </Card>
  );
}
