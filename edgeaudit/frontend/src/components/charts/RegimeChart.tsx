import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { RegimeAnalysis } from '../../types/audit';

interface RegimeChartProps {
  regime: RegimeAnalysis;
}

export function RegimeChart({ regime }: RegimeChartProps) {
  const data = Object.entries(regime.per_regime_sharpe).map(([name, sharpe]) => ({
    regime: name,
    sharpe: sharpe,
  }));

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Current Regime: <span className="font-semibold text-gray-900">{regime.current_regime}</span>
        </p>
        <p className="text-sm text-gray-600">
          Sensitivity: <span className="font-semibold text-gray-900">{(regime.regime_sensitivity * 100).toFixed(1)}%</span>
        </p>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="regime" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="sharpe" fill="#8b5cf6" name="Sharpe Ratio" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
