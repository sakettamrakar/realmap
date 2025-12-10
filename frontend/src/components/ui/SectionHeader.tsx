import React from 'react';

interface SectionHeaderProps {
    title: string;
    subtitle?: string;
    action?: React.ReactNode;
    className?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title, subtitle, action, className = '' }) => {
    return (
        <div className={`flex flex-wrap items-end justify-between py-4 border-b border-slate-100 mb-6 gap-4 ${className}`}>
            <div>
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h2>
                {subtitle && <p className="text-sm text-slate-500 mt-1 font-medium">{subtitle}</p>}
            </div>
            {action && <div className="ml-auto">{action}</div>}
        </div>
    );
};
