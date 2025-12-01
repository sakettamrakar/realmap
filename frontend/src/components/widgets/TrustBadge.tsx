/**
 * Trust Badge Component (Point 25)
 * 
 * Displays RERA verification status as a visual badge.
 * Designed for use in project cards and detail pages.
 */
import { useMemo } from 'react';
import './TrustBadge.css';

export type ReraVerificationStatus = 
  | 'VERIFIED'
  | 'PENDING'
  | 'REVOKED'
  | 'EXPIRED'
  | 'NOT_FOUND'
  | 'UNKNOWN';

export interface TrustBadgeData {
  status: ReraVerificationStatus;
  status_label: string;
  status_color: string;
  is_verified: boolean;
  official_link?: string | null;
  verified_at?: string | null;
  expiry_date?: string | null;
  days_until_expiry?: number | null;
  has_warnings: boolean;
  warning_message?: string | null;
}

export interface TrustBadgeProps {
  /** Trust badge data from API */
  badge?: TrustBadgeData | null;
  
  /** Fallback verification status if no badge data */
  verificationStatus?: ReraVerificationStatus | null;
  
  /** Display size */
  size?: 'sm' | 'md' | 'lg';
  
  /** Show detailed info on hover */
  showTooltip?: boolean;
  
  /** Show official link */
  showLink?: boolean;
  
  /** Compact mode - icon only */
  compact?: boolean;
  
  /** Additional class name */
  className?: string;
}

const STATUS_CONFIG: Record<ReraVerificationStatus, {
  label: string;
  color: string;
  bgColor: string;
  icon: string;
}> = {
  VERIFIED: {
    label: 'Verified',
    color: '#10B981',
    bgColor: '#ECFDF5',
    icon: '✓',
  },
  PENDING: {
    label: 'Pending',
    color: '#F59E0B',
    bgColor: '#FFFBEB',
    icon: '⏳',
  },
  REVOKED: {
    label: 'Revoked',
    color: '#EF4444',
    bgColor: '#FEF2F2',
    icon: '✕',
  },
  EXPIRED: {
    label: 'Expired',
    color: '#EF4444',
    bgColor: '#FEF2F2',
    icon: '⏰',
  },
  NOT_FOUND: {
    label: 'Not Found',
    color: '#EF4444',
    bgColor: '#FEF2F2',
    icon: '?',
  },
  UNKNOWN: {
    label: 'Not Verified',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    icon: '•',
  },
};

export function TrustBadge({
  badge,
  verificationStatus,
  size = 'md',
  showTooltip = true,
  showLink = false,
  compact = false,
  className = '',
}: TrustBadgeProps) {
  const effectiveStatus = useMemo(() => {
    if (badge) return badge.status;
    if (verificationStatus) return verificationStatus;
    return 'UNKNOWN';
  }, [badge, verificationStatus]);
  
  const config = STATUS_CONFIG[effectiveStatus];
  const displayLabel = badge?.status_label || config.label;
  const displayColor = badge?.status_color || config.color;
  
  const tooltipText = useMemo(() => {
    if (!showTooltip) return undefined;
    
    const parts: string[] = [`RERA Status: ${displayLabel}`];
    
    if (badge?.verified_at) {
      const date = new Date(badge.verified_at).toLocaleDateString();
      parts.push(`Last verified: ${date}`);
    }
    
    if (badge?.days_until_expiry !== null && badge?.days_until_expiry !== undefined) {
      if (badge.days_until_expiry < 0) {
        parts.push(`Expired ${Math.abs(badge.days_until_expiry)} days ago`);
      } else if (badge.days_until_expiry < 90) {
        parts.push(`Expires in ${badge.days_until_expiry} days`);
      }
    }
    
    if (badge?.warning_message) {
      parts.push(`⚠️ ${badge.warning_message}`);
    }
    
    return parts.join('\n');
  }, [badge, displayLabel, showTooltip]);
  
  const sizeClass = `trust-badge--${size}`;
  const statusClass = `trust-badge--${effectiveStatus.toLowerCase()}`;
  
  return (
    <div 
      className={`trust-badge ${sizeClass} ${statusClass} ${className}`}
      style={{ 
        '--badge-color': displayColor,
        '--badge-bg': config.bgColor,
      } as React.CSSProperties}
      title={tooltipText}
    >
      <span className="trust-badge__icon">{config.icon}</span>
      
      {!compact && (
        <span className="trust-badge__label">{displayLabel}</span>
      )}
      
      {badge?.has_warnings && (
        <span className="trust-badge__warning">⚠️</span>
      )}
      
      {showLink && badge?.official_link && (
        <a 
          href={badge.official_link}
          target="_blank"
          rel="noopener noreferrer"
          className="trust-badge__link"
          onClick={(e) => e.stopPropagation()}
        >
          <span className="trust-badge__link-icon">↗</span>
        </a>
      )}
    </div>
  );
}

/**
 * Inline verification indicator for lists
 */
export function VerifiedIcon({ 
  status,
  size = 16,
}: { 
  status?: ReraVerificationStatus | null;
  size?: number;
}) {
  if (!status || status === 'UNKNOWN') return null;
  
  const config = STATUS_CONFIG[status];
  
  return (
    <span 
      className="verified-icon"
      style={{ 
        color: config.color,
        fontSize: size,
      }}
      title={`RERA: ${config.label}`}
    >
      {status === 'VERIFIED' ? '✓' : config.icon}
    </span>
  );
}

export default TrustBadge;
