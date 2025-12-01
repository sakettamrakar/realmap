/**
 * PriceComparisonWidget Component (Point 20)
 * 
 * Displays a project's price comparison against neighborhood averages
 * with explicit normalization to price_per_sqft_carpet.
 * 
 * Requirements:
 * - Plot Project Price vs. Neighborhood Average
 * - Ensure both data points normalized to price_per_sqft_carpet
 * - Visual indicators for above/below average
 * - Sparkline or bar chart visualization
 */

import { useMemo } from 'react';
import './PriceComparisonWidget.css';

// ====================
// Types
// ====================

export interface PricePoint {
  /** Price per square foot (carpet area) */
  price_per_sqft_carpet: number;
  /** Label for the data point */
  label: string;
  /** Optional date for time-series data */
  date?: string;
}

export interface NeighborhoodStats {
  /** Average price per sqft carpet in neighborhood */
  average: number;
  /** Minimum price per sqft carpet */
  min: number;
  /** Maximum price per sqft carpet */
  max: number;
  /** Number of projects in comparison */
  sample_size: number;
  /** Neighborhood name */
  area_name: string;
}

export interface PriceComparisonWidgetProps {
  /** Project's current price per sqft carpet */
  projectPrice: number;
  /** Project name for display */
  projectName: string;
  /** Neighborhood statistics for comparison */
  neighborhoodStats: NeighborhoodStats;
  /** Optional historical price trend */
  priceTrend?: PricePoint[];
  /** Optional click handler for detailed view */
  onViewDetails?: () => void;
  /** Display variant */
  variant?: 'card' | 'compact' | 'inline';
  /** Show trend sparkline */
  showTrend?: boolean;
}

// ====================
// Utility Functions
// ====================

/**
 * Calculate percentage difference from average
 */
export function calculateDifferencePercent(
  projectPrice: number,
  averagePrice: number
): number {
  if (averagePrice === 0) return 0;
  return ((projectPrice - averagePrice) / averagePrice) * 100;
}

/**
 * Format currency in Indian style (lakhs/crores)
 */
export function formatIndianCurrency(amount: number): string {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`;
  } else {
    return `₹${amount.toLocaleString('en-IN')}`;
  }
}

/**
 * Format price per sqft
 */
export function formatPricePerSqft(price: number): string {
  return `₹${Math.round(price).toLocaleString('en-IN')}/sq.ft`;
}

/**
 * Get comparison status
 */
export function getComparisonStatus(
  diffPercent: number
): 'below' | 'average' | 'above' | 'premium' {
  if (diffPercent <= -10) return 'below';
  if (diffPercent <= 10) return 'average';
  if (diffPercent <= 25) return 'above';
  return 'premium';
}

/**
 * Get status label
 */
function getStatusLabel(status: ReturnType<typeof getComparisonStatus>): string {
  const labels = {
    below: 'Below Average',
    average: 'At Market Rate',
    above: 'Above Average',
    premium: 'Premium Pricing',
  };
  return labels[status];
}

/**
 * Get status description
 */
function getStatusDescription(
  status: ReturnType<typeof getComparisonStatus>,
  diffPercent: number,
  areaName: string
): string {
  const absPercent = Math.abs(diffPercent).toFixed(1);
  const descriptions = {
    below: `${absPercent}% below ${areaName} average. Good value proposition.`,
    average: `Within market range for ${areaName}.`,
    above: `${absPercent}% above ${areaName} average. Check amenities and location premium.`,
    premium: `${absPercent}% premium over ${areaName} average. Verify luxury positioning.`,
  };
  return descriptions[status];
}

// ====================
// Sub-Components
// ====================

interface ComparisonBarProps {
  projectPrice: number;
  stats: NeighborhoodStats;
}

/**
 * Visual bar showing price position within range
 */
function ComparisonBar({ projectPrice, stats }: ComparisonBarProps) {
  const range = stats.max - stats.min;
  const projectPosition = range > 0 
    ? Math.min(100, Math.max(0, ((projectPrice - stats.min) / range) * 100))
    : 50;
  const avgPosition = range > 0
    ? ((stats.average - stats.min) / range) * 100
    : 50;

  return (
    <div className="comparison-bar-container">
      <div className="comparison-bar">
        <div className="bar-fill" />
        <div 
          className="bar-marker average-marker"
          style={{ left: `${avgPosition}%` }}
          title={`Neighborhood Average: ${formatPricePerSqft(stats.average)}`}
        >
          <span className="marker-label">Avg</span>
        </div>
        <div 
          className="bar-marker project-marker"
          style={{ left: `${projectPosition}%` }}
          title={`This Project: ${formatPricePerSqft(projectPrice)}`}
        >
          <span className="marker-arrow">▼</span>
        </div>
      </div>
      <div className="bar-labels">
        <span className="bar-min">{formatPricePerSqft(stats.min)}</span>
        <span className="bar-max">{formatPricePerSqft(stats.max)}</span>
      </div>
    </div>
  );
}

interface TrendSparklineProps {
  data: PricePoint[];
  width?: number;
  height?: number;
}

/**
 * Simple SVG sparkline for price trend
 */
function TrendSparkline({ data, width = 120, height = 32 }: TrendSparklineProps) {
  if (!data || data.length < 2) return null;

  const prices = data.map(d => d.price_per_sqft_carpet);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice || 1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((d.price_per_sqft_carpet - minPrice) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const isUptrend = prices[prices.length - 1] > prices[0];

  return (
    <div className="trend-sparkline">
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
        <polyline
          fill="none"
          stroke={isUptrend ? '#22c55e' : '#ef4444'}
          strokeWidth="2"
          points={points}
        />
        <circle
          cx={(data.length - 1) / (data.length - 1) * width}
          cy={height - ((prices[prices.length - 1] - minPrice) / range) * height}
          r="3"
          fill={isUptrend ? '#22c55e' : '#ef4444'}
        />
      </svg>
      <span className={`trend-indicator ${isUptrend ? 'up' : 'down'}`}>
        {isUptrend ? '↑' : '↓'}
        {Math.abs(((prices[prices.length - 1] - prices[0]) / prices[0]) * 100).toFixed(1)}%
      </span>
    </div>
  );
}

// ====================
// Main Component
// ====================

export function PriceComparisonWidget({
  projectPrice,
  projectName,
  neighborhoodStats,
  priceTrend,
  onViewDetails,
  variant = 'card',
  showTrend = true,
}: PriceComparisonWidgetProps) {
  const diffPercent = useMemo(
    () => calculateDifferencePercent(projectPrice, neighborhoodStats.average),
    [projectPrice, neighborhoodStats.average]
  );

  const status = useMemo(() => getComparisonStatus(diffPercent), [diffPercent]);

  if (variant === 'inline') {
    return (
      <span className={`price-comparison-inline status-${status}`}>
        {formatPricePerSqft(projectPrice)}
        <span className="comparison-badge">
          {diffPercent > 0 ? '+' : ''}{diffPercent.toFixed(1)}% vs avg
        </span>
      </span>
    );
  }

  if (variant === 'compact') {
    return (
      <div className={`price-comparison-compact status-${status}`}>
        <div className="compact-header">
          <span className="compact-price">{formatPricePerSqft(projectPrice)}</span>
          <span className="compact-badge">{getStatusLabel(status)}</span>
        </div>
        <div className="compact-diff">
          {diffPercent > 0 ? '+' : ''}{diffPercent.toFixed(1)}% vs {neighborhoodStats.area_name}
        </div>
      </div>
    );
  }

  // Full card variant
  return (
    <div className={`price-comparison-widget status-${status}`}>
      <div className="widget-header">
        <h4>Price Comparison</h4>
        <span className="normalization-note">
          📐 Normalized to Carpet Area
        </span>
      </div>

      <div className="price-display">
        <div className="project-price">
          <span className="price-value">{formatPricePerSqft(projectPrice)}</span>
          <span className="price-label">{projectName}</span>
        </div>
        <div className="vs-separator">vs</div>
        <div className="average-price">
          <span className="price-value">{formatPricePerSqft(neighborhoodStats.average)}</span>
          <span className="price-label">{neighborhoodStats.area_name} Avg</span>
        </div>
      </div>

      <ComparisonBar projectPrice={projectPrice} stats={neighborhoodStats} />

      <div className={`status-banner status-${status}`}>
        <span className="status-icon">
          {status === 'below' && '✓'}
          {status === 'average' && '≈'}
          {status === 'above' && '↑'}
          {status === 'premium' && '★'}
        </span>
        <div className="status-content">
          <strong>{getStatusLabel(status)}</strong>
          <p>{getStatusDescription(status, diffPercent, neighborhoodStats.area_name)}</p>
        </div>
        <span className="diff-badge">
          {diffPercent > 0 ? '+' : ''}{diffPercent.toFixed(1)}%
        </span>
      </div>

      {showTrend && priceTrend && priceTrend.length > 1 && (
        <div className="trend-section">
          <span className="trend-label">6-Month Trend</span>
          <TrendSparkline data={priceTrend} />
        </div>
      )}

      <div className="widget-footer">
        <span className="sample-info">
          Based on {neighborhoodStats.sample_size} projects in {neighborhoodStats.area_name}
        </span>
        {onViewDetails && (
          <button className="details-link" onClick={onViewDetails}>
            View Analysis →
          </button>
        )}
      </div>
    </div>
  );
}

// ====================
// Exports
// ====================

export default PriceComparisonWidget;
