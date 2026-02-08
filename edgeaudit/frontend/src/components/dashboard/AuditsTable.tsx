import { useReactTable, getCoreRowModel, flexRender } from '@tanstack/react-table';
import type { ColumnDef } from '@tanstack/react-table';
import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import type { AuditSummary } from '../../types/audit';
import { Badge } from '../ui/Badge';

interface AuditsTableProps {
  audits: AuditSummary[];
}

export function AuditsTable({ audits }: AuditsTableProps) {
  const navigate = useNavigate();

  const columns: ColumnDef<AuditSummary>[] = [
    {
      accessorKey: 'strategy_name',
      header: 'Strategy Name',
      cell: (info) => (
        <span className="font-medium text-gray-900">{info.getValue() as string}</span>
      ),
    },
    {
      accessorKey: 'edge_score',
      header: 'Edge Score',
      cell: (info) => {
        const score = info.getValue() as number;
        return (
          <span className={`font-semibold ${
            score >= 70 ? 'text-success-600' :
            score >= 50 ? 'text-warning-600' :
            'text-danger-600'
          }`}>
            {score.toFixed(1)}
          </span>
        );
      },
    },
    {
      accessorKey: 'overfit_probability',
      header: 'Overfit Risk',
      cell: (info) => {
        const prob = info.getValue() as number;
        return <span className="text-gray-900">{(prob * 100).toFixed(1)}%</span>;
      },
    },
    {
      accessorKey: 'overfit_label',
      header: 'Risk Label',
      cell: (info) => <Badge label={info.getValue() as 'low' | 'medium' | 'high'} />,
    },
    {
      accessorKey: 'submitted_at',
      header: 'Date',
      cell: (info) => {
        const dateStr = info.getValue() as string;
        if (!dateStr) return <span className="text-gray-600 text-sm">N/A</span>;
        try {
          const date = new Date(dateStr);
          return (
            <span className="text-gray-600 text-sm">
              {format(date, 'MMM dd, yyyy HH:mm')}
            </span>
          );
        } catch {
          return <span className="text-gray-600 text-sm">N/A</span>;
        }
      },
    },
    {
      id: 'actions',
      header: '',
      cell: (info) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/audit/${info.row.original.audit_id}`);
          }}
          className="text-primary-600 hover:text-primary-700 font-medium text-sm"
        >
          View Details →
        </button>
      ),
    },
  ];

  const table = useReactTable({
    data: audits,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-white shadow-md rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/audit/${row.original.audit_id}`)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-6 py-4 whitespace-nowrap">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
