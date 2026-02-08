import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface EdgeScoreGaugeProps {
  score: number;
}

export function EdgeScoreGauge({ score }: EdgeScoreGaugeProps) {
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score },
  ];

  const getColor = (score: number) => {
    if (score >= 70) return '#22c55e'; // green
    if (score >= 50) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className="flex flex-col items-center">
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            dataKey="value"
          >
            <Cell fill={getColor(score)} />
            <Cell fill="#e5e7eb" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="text-center mt-4">
        <p className="text-4xl font-bold" style={{ color: getColor(score) }}>
          {score.toFixed(1)}
        </p>
        <p className="text-sm text-gray-600 mt-1">Edge Score</p>
      </div>
    </div>
  );
}
