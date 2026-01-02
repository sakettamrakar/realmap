/**
 * AreaLabel Component (Point 19: Area Transparency)
 * 
 * Displays area values with explicit type labels and tooltips.
 * Ensures compliance by clearly distinguishing carpet, builtup, and super_builtup areas.
 */
import { useState } from 'react';
import './AreaLabel.css';

export type AreaType = 'carpet' | 'builtup' | 'super_builtup' | 'unknown';

interface AreaLabelProps {
  /** Area value in square feet or a range string */
  value: number | string;
  /** Type of area measurement */
  areaType: AreaType;
  /** Unit to display (default: sqft) */
  unit?: 'sqft' | 'sqm';
  /** Show full label or compact badge */
  variant?: 'badge' | 'inline' | 'full';
  /** Additional CSS class */
  className?: string;
}

const AREA_CONFIG: Record<AreaType, {
  label: string;
  shortLabel: string;
  tooltip: string;
  className: string;
}> = {
  carpet: {
    label: 'Carpet Area',
    shortLabel: 'Carpet',
    tooltip: 'Carpet Area (RERA Standard): The actual usable floor area within the walls. This is the legally mandated measurement under RERA regulations.',
    className: 'area-carpet',
  },
  builtup: {
    label: 'Built-up Area',
    shortLabel: 'Built-up',
    tooltip: 'Built-up Area: Carpet area plus wall thickness and balcony area. Typically 10-15% more than carpet area.',
    className: 'area-builtup',
  },
  super_builtup: {
    label: 'Super Built-up Area',
    shortLabel: 'Super Built-up',
    tooltip: 'Super Built-up Area (Loading Included): Includes your share of common areas like lobby, staircase, and amenities. Can be 20-40% more than carpet area.',
    className: 'area-super-builtup',
  },
  unknown: {
    label: 'Area',
    shortLabel: 'Area',
    tooltip: 'Area type not specified. Verify with developer whether this is carpet, built-up, or super built-up area.',
    className: 'area-unknown',
  },
};

export function AreaLabel({
  value,
  areaType,
  unit = 'sqft',
  variant = 'badge',
  className = '',
}: AreaLabelProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const config = AREA_CONFIG[areaType];

  const formattedValue = typeof value === 'number' ? value.toLocaleString('en-IN') : value;
  const unitLabel = unit === 'sqft' ? 'sq.ft' : 'sq.m';

  if (variant === 'inline') {
    return (
      <span className={`area-label-inline ${className}`}>
        {formattedValue} {unitLabel}
        <span
          className={`area-type-badge ${config.className}`}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          {config.shortLabel}
          {showTooltip && (
            <span className="area-tooltip">{config.tooltip}</span>
          )}
        </span>
      </span>
    );
  }

  if (variant === 'full') {
    return (
      <div className={`area-label-full ${config.className} ${className}`}>
        <div className="area-value">{formattedValue} {unitLabel}</div>
        <div
          className="area-type-label"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          {config.label}
          <span className="info-icon">ⓘ</span>
          {showTooltip && (
            <div className="area-tooltip-box">{config.tooltip}</div>
          )}
        </div>
      </div>
    );
  }

  // Default: badge variant
  return (
    <div
      className={`area-label-badge ${config.className} ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <span className="area-value">{formattedValue}</span>
      <span className="area-unit">{unitLabel}</span>
      <span className="area-type">{config.shortLabel}</span>
      {showTooltip && (
        <div className="area-tooltip-popup">
          <div className="tooltip-title">{config.label}</div>
          <div className="tooltip-content">{config.tooltip}</div>
        </div>
      )}
    </div>
  );
}

/**
 * Area Comparison Warning Banner
 * 
 * Shows when comparing units with different area types.
 */
interface AreaComparisonWarningProps {
  areaTypes: AreaType[];
  className?: string;
}

export function AreaComparisonWarning({ areaTypes, className = '' }: AreaComparisonWarningProps) {
  const uniqueTypes = [...new Set(areaTypes.filter(t => t !== 'unknown'))];

  if (uniqueTypes.length <= 1) return null;

  return (
    <div className={`area-comparison-warning ${className}`}>
      <span className="warning-icon">⚠️</span>
      <div className="warning-content">
        <strong>Area Type Mismatch</strong>
        <p>
          You are comparing units with different area definitions:
          {uniqueTypes.map((t, i) => (
            <span key={t}>
              {i > 0 && (i === uniqueTypes.length - 1 ? ' and ' : ', ')}
              <strong>{AREA_CONFIG[t].label}</strong>
            </span>
          ))}
          . Prices per sq.ft may not be directly comparable.
        </p>
      </div>
    </div>
  );
}

/**
 * Utility: Normalize area to carpet equivalent
 * 
 * Applies standard conversion factors for comparison purposes.
 */
export function normalizeToCarept(value: number, areaType: AreaType): number {
  const CONVERSION_FACTORS: Record<AreaType, number> = {
    carpet: 1.0,
    builtup: 0.87,      // Builtup is ~15% more than carpet
    super_builtup: 0.75, // SBUA is ~33% more than carpet
    unknown: 1.0,
  };

  return value * CONVERSION_FACTORS[areaType];
}

export default AreaLabel;
