interface BadgeProps {
  label: 'low' | 'medium' | 'high';
}

export function Badge({ label }: BadgeProps) {
  const colors = {
    low: 'bg-success-100 text-success-700',
    medium: 'bg-warning-100 text-warning-700',
    high: 'bg-danger-100 text-danger-700',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[label]}`}>
      {label.toUpperCase()}
    </span>
  );
}
