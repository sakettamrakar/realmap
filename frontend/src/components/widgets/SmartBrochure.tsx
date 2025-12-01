/**
 * SmartBrochure Component (Point 21)
 * 
 * Intelligent brochure access with lead-gated download.
 * 
 * States:
 * - Public: OCR-extracted content preview available
 * - Gated: Lead capture form for full PDF access
 * - Locked: Icon indicating premium content
 * 
 * Integrates with POST /access/brochure API for signed URL generation.
 */

import React, { useState, useCallback } from 'react';
import './SmartBrochure.css';

// ====================
// Types
// ====================

export type BrochureAccessState = 'public' | 'gated' | 'locked' | 'loading' | 'ready';

export interface BrochureMetadata {
  /** Brochure ID for API calls */
  id: string;
  /** Display title */
  title: string;
  /** File size in bytes */
  fileSize?: number;
  /** Number of pages */
  pageCount?: number;
  /** Last updated date */
  updatedAt?: string;
  /** Preview thumbnail URL */
  thumbnailUrl?: string;
  /** OCR extracted content (if public) */
  ocrPreview?: string;
  /** Access state */
  state: BrochureAccessState;
}

export interface LeadFormData {
  name: string;
  email: string;
  phone: string;
  consent: boolean;
}

export interface SmartBrochureProps {
  /** Brochure metadata */
  brochure: BrochureMetadata;
  /** Project ID for context */
  projectId: number;
  /** Callback when brochure download is triggered */
  onDownload?: (signedUrl: string) => void;
  /** Callback when lead is captured */
  onLeadCapture?: (data: LeadFormData) => void;
  /** API handler for brochure access */
  requestAccess?: (
    brochureId: string,
    leadData: LeadFormData
  ) => Promise<{ signed_url: string; expires_at: string }>;
  /** Display variant */
  variant?: 'card' | 'inline' | 'mini';
}

// ====================
// Utility Functions
// ====================

/**
 * Format file size for display
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return 'Unknown size';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Validate email format
 */
function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate phone format (Indian mobile)
 */
function validatePhone(phone: string): boolean {
  return /^[6-9]\d{9}$/.test(phone.replace(/\D/g, ''));
}

// ====================
// Sub-Components
// ====================

interface LeadFormProps {
  onSubmit: (data: LeadFormData) => void;
  onCancel: () => void;
  loading?: boolean;
}

/**
 * Lead capture form for gated content
 */
function LeadForm({ onSubmit, onCancel, loading }: LeadFormProps) {
  const [formData, setFormData] = useState<LeadFormData>({
    name: '',
    email: '',
    phone: '',
    consent: false,
  });
  const [errors, setErrors] = useState<Partial<LeadFormData>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    // Clear error when user types
    if (errors[name as keyof LeadFormData]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const newErrors: Partial<Record<keyof LeadFormData, string>> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.email || !validateEmail(formData.email)) {
      newErrors.email = 'Valid email is required';
    }
    if (!formData.phone || !validatePhone(formData.phone)) {
      newErrors.phone = 'Valid 10-digit mobile number required';
    }
    if (!formData.consent) {
      newErrors.consent = 'Consent is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors as Partial<LeadFormData>);
      return;
    }

    onSubmit(formData);
  };

  return (
    <form className="lead-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h4>📄 Get Full Brochure</h4>
        <p>Fill in your details to download the complete brochure</p>
      </div>

      <div className={`form-field ${errors.name ? 'error' : ''}`}>
        <label htmlFor="lead-name">Full Name *</label>
        <input
          id="lead-name"
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Enter your name"
          disabled={loading}
        />
        {errors.name && <span className="field-error">{errors.name}</span>}
      </div>

      <div className={`form-field ${errors.email ? 'error' : ''}`}>
        <label htmlFor="lead-email">Email Address *</label>
        <input
          id="lead-email"
          type="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          placeholder="your@email.com"
          disabled={loading}
        />
        {errors.email && <span className="field-error">{errors.email}</span>}
      </div>

      <div className={`form-field ${errors.phone ? 'error' : ''}`}>
        <label htmlFor="lead-phone">Mobile Number *</label>
        <input
          id="lead-phone"
          type="tel"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          placeholder="10-digit mobile number"
          disabled={loading}
        />
        {errors.phone && <span className="field-error">{errors.phone}</span>}
      </div>

      <div className={`form-field checkbox ${errors.consent ? 'error' : ''}`}>
        <label>
          <input
            type="checkbox"
            name="consent"
            checked={formData.consent}
            onChange={handleChange}
            disabled={loading}
          />
          <span>
            I agree to receive project updates and marketing communications.
            I understand my data will be processed per the privacy policy.
          </span>
        </label>
        {errors.consent && <span className="field-error">{errors.consent}</span>}
      </div>

      <div className="form-actions">
        <button type="button" className="btn-cancel" onClick={onCancel} disabled={loading}>
          Cancel
        </button>
        <button type="submit" className="btn-submit" disabled={loading}>
          {loading ? 'Processing...' : 'Download Brochure'}
        </button>
      </div>
    </form>
  );
}

interface OcrPreviewProps {
  content: string;
  onRequestFull: () => void;
}

/**
 * OCR extracted content preview
 */
function OcrPreview({ content, onRequestFull }: OcrPreviewProps) {
  const truncated = content.length > 500 ? content.slice(0, 500) + '...' : content;
  
  return (
    <div className="ocr-preview">
      <div className="preview-header">
        <span className="preview-badge">📖 Preview</span>
        <span className="preview-note">OCR-extracted content</span>
      </div>
      <div className="preview-content">
        {truncated}
      </div>
      <button className="preview-expand" onClick={onRequestFull}>
        View Full Brochure →
      </button>
    </div>
  );
}

// ====================
// Main Component
// ====================

export function SmartBrochure({
  brochure,
  projectId: _projectId,
  onDownload,
  onLeadCapture,
  requestAccess,
  variant = 'card',
}: SmartBrochureProps) {
  const [state, setState] = useState<BrochureAccessState>(brochure.state);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [signedUrl, setSignedUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRequestAccess = useCallback(() => {
    if (state === 'public') {
      // Public content, show form to get full version
      setShowForm(true);
    } else if (state === 'gated') {
      setShowForm(true);
    } else if (state === 'ready' && signedUrl) {
      // Already have URL, trigger download
      onDownload?.(signedUrl);
      window.open(signedUrl, '_blank');
    }
  }, [state, signedUrl, onDownload]);

  const handleLeadSubmit = useCallback(async (data: LeadFormData) => {
    setLoading(true);
    setError(null);

    try {
      if (requestAccess) {
        const result = await requestAccess(brochure.id, data);
        setSignedUrl(result.signed_url);
        setExpiresAt(result.expires_at);
        setState('ready');
        onLeadCapture?.(data);
        onDownload?.(result.signed_url);
        window.open(result.signed_url, '_blank');
      } else {
        // Mock success for demo
        setTimeout(() => {
          const mockUrl = `/api/v1/access/brochure/${brochure.id}/download`;
          setSignedUrl(mockUrl);
          setState('ready');
          onLeadCapture?.(data);
          setLoading(false);
        }, 1500);
        return;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request access');
    } finally {
      setLoading(false);
    }
  }, [brochure.id, requestAccess, onLeadCapture, onDownload]);

  // Mini variant
  if (variant === 'mini') {
    return (
      <button 
        className={`smart-brochure-mini state-${state}`}
        onClick={handleRequestAccess}
        title={brochure.title}
      >
        {state === 'locked' && '🔒'}
        {state === 'gated' && '📄'}
        {state === 'public' && '📖'}
        {state === 'ready' && '⬇️'}
        {state === 'loading' && '⏳'}
      </button>
    );
  }

  // Inline variant
  if (variant === 'inline') {
    return (
      <div className={`smart-brochure-inline state-${state}`}>
        <span className="brochure-icon">
          {state === 'locked' && '🔒'}
          {state === 'gated' && '📄'}
          {state === 'public' && '📖'}
          {state === 'ready' && '✓'}
        </span>
        <span className="brochure-title">{brochure.title}</span>
        {brochure.pageCount && (
          <span className="brochure-meta">{brochure.pageCount} pages</span>
        )}
        <button 
          className="brochure-action"
          onClick={handleRequestAccess}
          disabled={loading}
        >
          {state === 'locked' && 'Unlock'}
          {state === 'gated' && 'Get Access'}
          {state === 'public' && 'View'}
          {state === 'ready' && 'Download'}
          {loading && 'Loading...'}
        </button>
      </div>
    );
  }

  // Full card variant
  return (
    <div className={`smart-brochure-card state-${state}`}>
      {showForm ? (
        <LeadForm
          onSubmit={handleLeadSubmit}
          onCancel={() => setShowForm(false)}
          loading={loading}
        />
      ) : (
        <>
          <div className="brochure-header">
            <div className="brochure-thumbnail">
              {brochure.thumbnailUrl ? (
                <img src={brochure.thumbnailUrl} alt={brochure.title} />
              ) : (
                <div className="thumbnail-placeholder">
                  <span>📄</span>
                </div>
              )}
              <div className={`state-badge state-${state}`}>
                {state === 'locked' && '🔒 Locked'}
                {state === 'gated' && '📝 Sign Up'}
                {state === 'public' && '📖 Preview'}
                {state === 'ready' && '✓ Ready'}
              </div>
            </div>
            <div className="brochure-info">
              <h4>{brochure.title}</h4>
              <div className="brochure-meta">
                {brochure.pageCount && <span>{brochure.pageCount} pages</span>}
                {brochure.fileSize && <span>{formatFileSize(brochure.fileSize)}</span>}
                {brochure.updatedAt && (
                  <span>Updated {new Date(brochure.updatedAt).toLocaleDateString()}</span>
                )}
              </div>
            </div>
          </div>

          {state === 'public' && brochure.ocrPreview && (
            <OcrPreview 
              content={brochure.ocrPreview} 
              onRequestFull={() => setShowForm(true)}
            />
          )}

          {error && (
            <div className="brochure-error">
              <span>⚠️ {error}</span>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}

          {state === 'ready' && signedUrl && (
            <div className="brochure-ready">
              <span className="ready-icon">✓</span>
              <span className="ready-text">Your download is ready!</span>
              {expiresAt && (
                <span className="expires-note">
                  Link expires {new Date(expiresAt).toLocaleTimeString()}
                </span>
              )}
            </div>
          )}

          <div className="brochure-actions">
            <button
              className={`btn-primary state-${state}`}
              onClick={handleRequestAccess}
              disabled={loading || state === 'locked'}
            >
              {loading && 'Processing...'}
              {!loading && state === 'locked' && '🔒 Premium Content'}
              {!loading && state === 'gated' && 'Get Free Access'}
              {!loading && state === 'public' && 'Download Full PDF'}
              {!loading && state === 'ready' && 'Download Now'}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ====================
// Exports
// ====================

export default SmartBrochure;
