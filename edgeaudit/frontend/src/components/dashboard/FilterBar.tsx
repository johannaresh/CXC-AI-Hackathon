import { useState, useEffect } from 'react';
import { useDebounce } from '../../hooks/useDebounce';

interface FilterBarProps {
  onFilterChange: (strategyName: string) => void;
  onSortChange: (sortBy: string, sortOrder: string) => void;
}

export function FilterBar({ onFilterChange, onSortChange }: FilterBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 500);

  // Trigger filter when debounced value changes
  useEffect(() => {
    onFilterChange(debouncedSearch);
  }, [debouncedSearch, onFilterChange]);

  return (
    <div className="bg-white p-4 rounded-lg shadow-md mb-6">
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
            Search Strategy
          </label>
          <input
            id="search"
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Filter by strategy name..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label htmlFor="sort" className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select
            id="sort"
            onChange={(e) => {
              const val = e.target.value;
              const lastUnderscore = val.lastIndexOf('_');
              const sortBy = val.substring(0, lastUnderscore);
              const sortOrder = val.substring(lastUnderscore + 1);
              onSortChange(sortBy, sortOrder);
            }}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="submitted_at_desc">Date (Newest)</option>
            <option value="submitted_at_asc">Date (Oldest)</option>
            <option value="edge_score_desc">Edge Score (High to Low)</option>
            <option value="edge_score_asc">Edge Score (Low to High)</option>
            <option value="overfit_probability_desc">Risk (High to Low)</option>
            <option value="overfit_probability_asc">Risk (Low to High)</option>
          </select>
        </div>
      </div>
    </div>
  );
}
