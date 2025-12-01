import React from 'react';

interface NavItemProps {
    icon: React.ReactNode;
    label: string;
    isActive?: boolean;
    onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon, label, isActive, onClick }) => (
    <button
        onClick={onClick}
        className={`nav-item ${isActive ? 'active' : ''}`}
        style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'none',
            border: 'none',
            padding: '8px',
            flex: 1,
            color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'color 0.2s ease',
        }}
    >
        <div style={{ marginBottom: '4px' }}>{icon}</div>
        <span style={{ fontSize: '11px', fontWeight: 500 }}>{label}</span>
    </button>
);

const HomeIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
    </svg>
);

const CheckIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </svg>
);

const CompareIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10"></line>
        <line x1="12" y1="20" x2="12" y2="4"></line>
        <line x1="6" y1="20" x2="6" y2="14"></line>
    </svg>
);

const SavedIcon = () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
    </svg>
);

interface BottomNavProps {
    activeTab: 'home' | 'check' | 'compare' | 'saved';
    onTabChange: (tab: 'home' | 'check' | 'compare' | 'saved') => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, onTabChange }) => {
    return (
        <div
            className="mobile-bottom-nav"
            style={{
                position: 'fixed',
                bottom: 0,
                left: 0,
                right: 0,
                height: '64px',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                borderTop: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-around',
                alignItems: 'center',
                zIndex: 1000,
                paddingBottom: 'env(safe-area-inset-bottom)',
                boxShadow: '0 -4px 20px rgba(0,0,0,0.04)',
            }}
        >
            <NavItem
                icon={<HomeIcon />}
                label="Home"
                isActive={activeTab === 'home'}
                onClick={() => onTabChange('home')}
            />
            <NavItem
                icon={<CheckIcon />}
                label="Check"
                isActive={activeTab === 'check'}
                onClick={() => onTabChange('check')}
            />
            <NavItem
                icon={<CompareIcon />}
                label="Compare"
                isActive={activeTab === 'compare'}
                onClick={() => onTabChange('compare')}
            />
            <NavItem
                icon={<SavedIcon />}
                label="Saved"
                isActive={activeTab === 'saved'}
                onClick={() => onTabChange('saved')}
            />
        </div>
    );
};
