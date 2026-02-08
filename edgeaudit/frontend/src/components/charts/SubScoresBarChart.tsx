import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import type { EdgeScoreBreakdown } from '../../types/audit';

interface SubScoresBarChartProps {
  scores: EdgeScoreBreakdown;
}

export function SubScoresBarChart({ scores }: SubScoresBarChartProps) {
  const data = [
    { name: 'Overfit', value: scores.overfit_sub_score },
    { name: 'Regime', value: scores.regime_sub_score },
    { name: 'Statistical Sig', value: scores.stat_sig_sub_score },
    { name: 'Data Leakage', value: scores.data_leakage_sub_score },
    { name: 'Explainability', value: scores.explainability_sub_score },
  ];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Bar dataKey="value" fill="#0ea5e9" />
      </BarChart>
    </ResponsiveContainer>
  );
}
