/**
 * Tag Filter Component (Point 24)
 * 
 * Faceted search sidebar for tag-based filtering.
 * Displays tags grouped by category with project counts.
 */
import { useState, useMemo } from 'react';
import './TagFilter.css';

export type TagCategory = 
  | 'PROXIMITY'
  | 'INFRASTRUCTURE'
  | 'INVESTMENT'
  | 'LIFESTYLE'
  | 'CERTIFICATION';

export interface TagWithCount {
  id: number;
  slug: string;
  name: string;
  category: TagCategory;
  icon_emoji?: string | null;
  color_hex?: string | null;
  is_featured: boolean;
  project_count: number;
}

export interface TagsByCategory {
  category: TagCategory;
  category_label: string;
  tags: TagWithCount[];
}

export interface FacetedTagsResponse {
  categories: TagsByCategory[];
  featured_tags: TagWithCount[];
  total_tags: number;
}

export interface TagFilterProps {
  /** Currently selected tag slugs */
  selectedTags: string[];
  
  /** Callback when tags change */
  onTagsChange: (tags: string[]) => void;
  
  /** Whether to require all tags (AND) or any tag (OR) */
  matchAll?: boolean;
  
  /** Callback when match mode changes */
  onMatchAllChange?: (matchAll: boolean) => void;
  
  /** Pre-loaded faceted tags data */
  facetedTags?: FacetedTagsResponse | null;
  
  /** Loading state */
  loading?: boolean;
  
  /** Collapsed categories */
  collapsedCategories?: TagCategory[];
  
  /** Additional class name */
  className?: string;
}

const CATEGORY_ICONS: Record<TagCategory, string> = {
  PROXIMITY: '📍',
  INFRASTRUCTURE: '🏗️',
  INVESTMENT: '📈',
  LIFESTYLE: '🏡',
  CERTIFICATION: '✅',
};

export function TagFilter({
  selectedTags,
  onTagsChange,
  matchAll = false,
  onMatchAllChange,
  facetedTags,
  loading = false,
  collapsedCategories: initialCollapsed = [],
  className = '',
}: TagFilterProps) {
  const [collapsed, setCollapsed] = useState<Set<TagCategory>>(
    new Set(initialCollapsed)
  );
  
  const toggleCategory = (category: TagCategory) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };
  
  const toggleTag = (slug: string) => {
    if (selectedTags.includes(slug)) {
      onTagsChange(selectedTags.filter((s) => s !== slug));
    } else {
      onTagsChange([...selectedTags, slug]);
    }
  };
  
  const clearTags = () => {
    onTagsChange([]);
  };
  
  // Count selected tags per category
  const selectedCountByCategory = useMemo(() => {
    if (!facetedTags) return {} as Record<TagCategory, number>;
    
    const counts = {} as Record<TagCategory, number>;
    
    for (const cat of facetedTags.categories) {
      counts[cat.category] = cat.tags.filter(
        (t) => selectedTags.includes(t.slug)
      ).length;
    }
    
    return counts;
  }, [facetedTags, selectedTags]);
  
  if (loading) {
    return (
      <div className={`tag-filter tag-filter--loading ${className}`}>
        <div className="tag-filter__skeleton">
          <div className="skeleton-line skeleton-line--header" />
          <div className="skeleton-line" />
          <div className="skeleton-line" />
          <div className="skeleton-line" />
        </div>
      </div>
    );
  }
  
  if (!facetedTags || facetedTags.total_tags === 0) {
    return null;
  }
  
  return (
    <div className={`tag-filter ${className}`}>
      <div className="tag-filter__header">
        <h4 className="tag-filter__title">Filter by Tags</h4>
        {selectedTags.length > 0 && (
          <button 
            className="tag-filter__clear"
            onClick={clearTags}
          >
            Clear ({selectedTags.length})
          </button>
        )}
      </div>
      
      {/* Match mode toggle */}
      {onMatchAllChange && selectedTags.length > 1 && (
        <div className="tag-filter__match-mode">
          <label className="match-mode-toggle">
            <input
              type="checkbox"
              checked={matchAll}
              onChange={(e) => onMatchAllChange(e.target.checked)}
            />
            <span>Match all selected tags</span>
          </label>
        </div>
      )}
      
      {/* Featured tags */}
      {facetedTags.featured_tags.length > 0 && (
        <div className="tag-filter__featured">
          <div className="tag-filter__featured-tags">
            {facetedTags.featured_tags.map((tag) => (
              <TagChip
                key={tag.slug}
                tag={tag}
                selected={selectedTags.includes(tag.slug)}
                onClick={() => toggleTag(tag.slug)}
                featured
              />
            ))}
          </div>
        </div>
      )}
      
      {/* Categories */}
      <div className="tag-filter__categories">
        {facetedTags.categories.map((cat) => (
          <div 
            key={cat.category} 
            className={`tag-category ${collapsed.has(cat.category) ? 'tag-category--collapsed' : ''}`}
          >
            <button
              className="tag-category__header"
              onClick={() => toggleCategory(cat.category)}
            >
              <span className="tag-category__icon">
                {CATEGORY_ICONS[cat.category]}
              </span>
              <span className="tag-category__label">
                {cat.category_label}
              </span>
              {selectedCountByCategory[cat.category] > 0 && (
                <span className="tag-category__selected-count">
                  {selectedCountByCategory[cat.category]}
                </span>
              )}
              <span className="tag-category__chevron">
                {collapsed.has(cat.category) ? '▸' : '▾'}
              </span>
            </button>
            
            {!collapsed.has(cat.category) && (
              <div className="tag-category__tags">
                {cat.tags.map((tag) => (
                  <TagChip
                    key={tag.slug}
                    tag={tag}
                    selected={selectedTags.includes(tag.slug)}
                    onClick={() => toggleTag(tag.slug)}
                  />
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

interface TagChipProps {
  tag: TagWithCount;
  selected: boolean;
  onClick: () => void;
  featured?: boolean;
}

function TagChip({ tag, selected, onClick, featured = false }: TagChipProps) {
  return (
    <button
      className={`tag-chip ${selected ? 'tag-chip--selected' : ''} ${featured ? 'tag-chip--featured' : ''}`}
      onClick={onClick}
      style={tag.color_hex ? { '--tag-color': tag.color_hex } as React.CSSProperties : undefined}
    >
      {tag.icon_emoji && (
        <span className="tag-chip__emoji">{tag.icon_emoji}</span>
      )}
      <span className="tag-chip__name">{tag.name}</span>
      <span className="tag-chip__count">({tag.project_count})</span>
    </button>
  );
}

/**
 * Compact tag display for search results
 */
export function TagList({ 
  tags,
  limit = 3,
  className = '',
}: { 
  tags: string[];
  limit?: number;
  className?: string;
}) {
  if (!tags || tags.length === 0) return null;
  
  const displayed = tags.slice(0, limit);
  const remaining = tags.length - limit;
  
  return (
    <div className={`tag-list ${className}`}>
      {displayed.map((slug) => (
        <span key={slug} className="tag-pill">
          {slug.replace(/-/g, ' ')}
        </span>
      ))}
      {remaining > 0 && (
        <span className="tag-pill tag-pill--more">+{remaining}</span>
      )}
    </div>
  );
}

export default TagFilter;
