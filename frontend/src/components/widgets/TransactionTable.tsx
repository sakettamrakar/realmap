/**
 * TransactionTable Component (Point 23)
 * 
 * Displays transaction history with:
 * - Outlier highlighting (price_per_sqft > 20% deviation from median)
 * - Verification source badges
 * - Sortable columns
 * - Filtering capabilities
 * 
 * Requirements:
 * - Highlight rows where price_per_sqft > 20% deviation from median
 * - Add Verification Source badge (RERA, IGR, Self-Reported)
 */

import { useState, useMemo, useCallback } from 'react';
import './TransactionTable.css';

// ====================
// Types
// ====================

export type VerificationSource = 'rera' | 'igr' | 'self_reported' | 'bank' | 'unverified';

export interface Transaction {
  /** Unique transaction ID */
  id: string;
  /** Unit number/identifier */
  unit_number: string;
  /** Transaction date */
  date: string;
  /** Sale price in INR */
  sale_price: number;
  /** Area in square feet (carpet) */
  area_sqft: number;
  /** Price per square foot */
  price_per_sqft: number;
  /** Floor number */
  floor?: number;
  /** Unit type (1BHK, 2BHK, etc.) */
  unit_type?: string;
  /** Verification source */
  verification_source: VerificationSource;
  /** Registration number (if verified) */
  registration_number?: string;
  /** Buyer category (if available) */
  buyer_category?: 'individual' | 'company' | 'nri';
  /** Is this an outlier? (calculated) */
  is_outlier?: boolean;
  /** Deviation from median (percentage) */
  deviation_percent?: number;
}

export interface TransactionTableProps {
  /** List of transactions */
  transactions: Transaction[];
  /** Project name for context */
  projectName?: string;
  /** Outlier threshold percentage (default: 20) */
  outlierThreshold?: number;
  /** Callback when transaction is selected */
  onSelect?: (transaction: Transaction) => void;
  /** Show verification details */
  showVerificationDetails?: boolean;
  /** Compact variant */
  compact?: boolean;
}

export type SortField = 'date' | 'sale_price' | 'price_per_sqft' | 'area_sqft' | 'floor';
export type SortDirection = 'asc' | 'desc';

// ====================
// Constants
// ====================

const VERIFICATION_CONFIG: Record<VerificationSource, {
  label: string;
  shortLabel: string;
  icon: string;
  color: string;
  bgColor: string;
  description: string;
}> = {
  rera: {
    label: 'RERA Verified',
    shortLabel: 'RERA',
    icon: '✓',
    color: '#166534',
    bgColor: '#dcfce7',
    description: 'Verified through RERA portal registration data',
  },
  igr: {
    label: 'IGR Verified',
    shortLabel: 'IGR',
    icon: '📋',
    color: '#1e40af',
    bgColor: '#dbeafe',
    description: 'Verified through Inspector General of Registration records',
  },
  bank: {
    label: 'Bank Verified',
    shortLabel: 'Bank',
    icon: '🏦',
    color: '#7c3aed',
    bgColor: '#ede9fe',
    description: 'Verified through banking/loan records',
  },
  self_reported: {
    label: 'Self Reported',
    shortLabel: 'Reported',
    icon: '📝',
    color: '#92400e',
    bgColor: '#fef3c7',
    description: 'Reported by buyer/seller, not independently verified',
  },
  unverified: {
    label: 'Unverified',
    shortLabel: 'Unverified',
    icon: '?',
    color: '#6b7280',
    bgColor: '#f3f4f6',
    description: 'Source not verified',
  },
};

// ====================
// Utility Functions
// ====================

/**
 * Format currency in Indian style
 */
export function formatIndianCurrency(amount: number, compact = false): string {
  if (compact) {
    if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} L`;
  }
  return `₹${amount.toLocaleString('en-IN')}`;
}

/**
 * Format date for display
 */
export function formatDate(dateStr: string, short = false): string {
  const date = new Date(dateStr);
  if (short) {
    return date.toLocaleDateString('en-IN', { month: 'short', year: '2-digit' });
  }
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Calculate median value
 */
function calculateMedian(values: number[]): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0
    ? sorted[mid]
    : (sorted[mid - 1] + sorted[mid]) / 2;
}

/**
 * Determine if a value is an outlier
 */
function isOutlier(value: number, median: number, threshold: number): boolean {
  if (median === 0) return false;
  const deviation = Math.abs((value - median) / median) * 100;
  return deviation > threshold;
}

/**
 * Calculate deviation percentage
 */
function calculateDeviation(value: number, median: number): number {
  if (median === 0) return 0;
  return ((value - median) / median) * 100;
}

// ====================
// Sub-Components
// ====================

interface VerificationBadgeProps {
  source: VerificationSource;
  registrationNumber?: string;
  showTooltip?: boolean;
}

/**
 * Badge showing verification source
 */
export function VerificationBadge({ 
  source, 
  registrationNumber,
  showTooltip = true 
}: VerificationBadgeProps) {
  const config = VERIFICATION_CONFIG[source];
  const [showTip, setShowTip] = useState(false);

  return (
    <span 
      className={`verification-badge source-${source}`}
      style={{ 
        background: config.bgColor, 
        color: config.color 
      }}
      onMouseEnter={() => setShowTip(true)}
      onMouseLeave={() => setShowTip(false)}
    >
      <span className="badge-icon">{config.icon}</span>
      <span className="badge-label">{config.shortLabel}</span>
      
      {showTooltip && showTip && (
        <div className="verification-tooltip">
          <strong>{config.label}</strong>
          <p>{config.description}</p>
          {registrationNumber && (
            <span className="reg-number">Reg: {registrationNumber}</span>
          )}
        </div>
      )}
    </span>
  );
}

interface OutlierIndicatorProps {
  deviation: number;
  threshold: number;
}

/**
 * Indicator showing outlier status
 */
function OutlierIndicator({ deviation, threshold }: OutlierIndicatorProps) {
  const isHigh = deviation > threshold;
  const isLow = deviation < -threshold;
  
  if (!isHigh && !isLow) return null;

  return (
    <span className={`outlier-indicator ${isHigh ? 'high' : 'low'}`}>
      <span className="outlier-icon">{isHigh ? '↑' : '↓'}</span>
      <span className="outlier-value">{Math.abs(deviation).toFixed(1)}%</span>
      <span className="outlier-label">{isHigh ? 'above' : 'below'} median</span>
    </span>
  );
}

interface TableHeaderProps {
  field: SortField;
  label: string;
  currentSort: SortField;
  direction: SortDirection;
  onSort: (field: SortField) => void;
  align?: 'left' | 'right' | 'center';
}

/**
 * Sortable table header
 */
function TableHeader({ 
  field, 
  label, 
  currentSort, 
  direction, 
  onSort,
  align = 'left' 
}: TableHeaderProps) {
  const isActive = currentSort === field;
  
  return (
    <th 
      className={`sortable ${align} ${isActive ? 'active' : ''}`}
      onClick={() => onSort(field)}
    >
      <span className="header-content">
        {label}
        <span className="sort-indicator">
          {isActive && (direction === 'asc' ? '↑' : '↓')}
        </span>
      </span>
    </th>
  );
}

// ====================
// Main Component
// ====================

export function TransactionTable({
  transactions,
  projectName,
  outlierThreshold = 20,
  onSelect,
  showVerificationDetails = true,
  compact = false,
}: TransactionTableProps) {
  // State
  const [sortField, setSortField] = useState<SortField>('date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filterSource, setFilterSource] = useState<VerificationSource | 'all'>('all');
  const [showOutliersOnly, setShowOutliersOnly] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // Calculate median and process transactions
  const { processedTransactions, medianPrice, stats } = useMemo(() => {
    const prices = transactions.map(t => t.price_per_sqft);
    const median = calculateMedian(prices);
    
    const processed = transactions.map(t => ({
      ...t,
      deviation_percent: calculateDeviation(t.price_per_sqft, median),
      is_outlier: isOutlier(t.price_per_sqft, median, outlierThreshold),
    }));

    const outlierCount = processed.filter(t => t.is_outlier).length;
    const verifiedCount = processed.filter(t => 
      t.verification_source === 'rera' || t.verification_source === 'igr'
    ).length;

    return {
      processedTransactions: processed,
      medianPrice: median,
      stats: {
        total: transactions.length,
        outliers: outlierCount,
        verified: verifiedCount,
        verificationRate: transactions.length > 0 
          ? ((verifiedCount / transactions.length) * 100).toFixed(0) 
          : '0',
      },
    };
  }, [transactions, outlierThreshold]);

  // Filter and sort
  const displayTransactions = useMemo(() => {
    let filtered = [...processedTransactions];

    // Apply source filter
    if (filterSource !== 'all') {
      filtered = filtered.filter(t => t.verification_source === filterSource);
    }

    // Apply outlier filter
    if (showOutliersOnly) {
      filtered = filtered.filter(t => t.is_outlier);
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'date':
          comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
          break;
        case 'sale_price':
          comparison = a.sale_price - b.sale_price;
          break;
        case 'price_per_sqft':
          comparison = a.price_per_sqft - b.price_per_sqft;
          break;
        case 'area_sqft':
          comparison = a.area_sqft - b.area_sqft;
          break;
        case 'floor':
          comparison = (a.floor || 0) - (b.floor || 0);
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [processedTransactions, filterSource, showOutliersOnly, sortField, sortDirection]);

  // Handlers
  const handleSort = useCallback((field: SortField) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  }, [sortField]);

  const handleRowClick = useCallback((transaction: Transaction) => {
    setSelectedId(transaction.id);
    onSelect?.(transaction);
  }, [onSelect]);

  return (
    <div className={`transaction-table-container ${compact ? 'compact' : ''}`}>
      {/* Header with stats */}
      <div className="table-header">
        <div className="header-title">
          <h4>📊 Transaction History</h4>
          {projectName && <span className="project-name">{projectName}</span>}
        </div>
        <div className="header-stats">
          <span className="stat">
            <strong>{stats.total}</strong> transactions
          </span>
          <span className="stat">
            <strong>{stats.verificationRate}%</strong> verified
          </span>
          {stats.outliers > 0 && (
            <span className="stat outliers">
              <strong>{stats.outliers}</strong> outliers
            </span>
          )}
          <span className="stat median">
            Median: <strong>{formatIndianCurrency(medianPrice)}/sq.ft</strong>
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="table-filters">
        <div className="filter-group">
          <label>Source:</label>
          <select 
            value={filterSource} 
            onChange={e => setFilterSource(e.target.value as VerificationSource | 'all')}
          >
            <option value="all">All Sources</option>
            {Object.entries(VERIFICATION_CONFIG).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>

        <label className="filter-checkbox">
          <input
            type="checkbox"
            checked={showOutliersOnly}
            onChange={e => setShowOutliersOnly(e.target.checked)}
          />
          <span>Show outliers only ({'>'}±{outlierThreshold}% from median)</span>
        </label>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="transaction-table">
          <thead>
            <tr>
              <TableHeader
                field="date"
                label="Date"
                currentSort={sortField}
                direction={sortDirection}
                onSort={handleSort}
              />
              <th>Unit</th>
              <TableHeader
                field="area_sqft"
                label="Area (sq.ft)"
                currentSort={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <TableHeader
                field="sale_price"
                label="Sale Price"
                currentSort={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              <TableHeader
                field="price_per_sqft"
                label="₹/sq.ft"
                currentSort={sortField}
                direction={sortDirection}
                onSort={handleSort}
                align="right"
              />
              {!compact && <th>Deviation</th>}
              {showVerificationDetails && <th>Source</th>}
            </tr>
          </thead>
          <tbody>
            {displayTransactions.map(transaction => (
              <tr
                key={transaction.id}
                className={`
                  ${transaction.is_outlier ? 'outlier-row' : ''}
                  ${transaction.deviation_percent && transaction.deviation_percent > 0 ? 'high' : 'low'}
                  ${selectedId === transaction.id ? 'selected' : ''}
                `}
                onClick={() => handleRowClick(transaction)}
              >
                <td className="date-cell">
                  {formatDate(transaction.date, compact)}
                </td>
                <td className="unit-cell">
                  <span className="unit-number">{transaction.unit_number}</span>
                  {transaction.unit_type && (
                    <span className="unit-type">{transaction.unit_type}</span>
                  )}
                  {transaction.floor !== undefined && !compact && (
                    <span className="floor-info">Floor {transaction.floor}</span>
                  )}
                </td>
                <td className="number-cell">{transaction.area_sqft.toLocaleString()}</td>
                <td className="number-cell price-cell">
                  {formatIndianCurrency(transaction.sale_price, compact)}
                </td>
                <td className="number-cell sqft-price-cell">
                  {formatIndianCurrency(transaction.price_per_sqft)}
                  {transaction.is_outlier && (
                    <span className="outlier-flag">⚠</span>
                  )}
                </td>
                {!compact && (
                  <td className="deviation-cell">
                    {transaction.deviation_percent !== undefined && (
                      <OutlierIndicator
                        deviation={transaction.deviation_percent}
                        threshold={outlierThreshold}
                      />
                    )}
                  </td>
                )}
                {showVerificationDetails && (
                  <td className="source-cell">
                    <VerificationBadge
                      source={transaction.verification_source}
                      registrationNumber={transaction.registration_number}
                    />
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {displayTransactions.length === 0 && (
          <div className="empty-state">
            <span className="empty-icon">📭</span>
            <p>No transactions match the current filters</p>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="table-legend">
        <div className="legend-item">
          <span className="legend-swatch outlier-high"></span>
          <span>Above median by {'>'}{outlierThreshold}%</span>
        </div>
        <div className="legend-item">
          <span className="legend-swatch outlier-low"></span>
          <span>Below median by {'>'}{outlierThreshold}%</span>
        </div>
        <div className="legend-sources">
          {Object.entries(VERIFICATION_CONFIG).slice(0, 3).map(([key, config]) => (
            <span key={key} className="legend-source" style={{ color: config.color }}>
              {config.icon} {config.shortLabel}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ====================
// Exports
// ====================

export { VERIFICATION_CONFIG };
export default TransactionTable;
