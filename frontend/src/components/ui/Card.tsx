import React from 'react';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    onClick?: () => void;
    hoverEffect?: boolean;
    selected?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick, hoverEffect = false, selected = false }) => {
    return (
        <div
            className={`
        group relative bg-white rounded-xl border transition-all duration-300
        ${selected
                    ? 'border-sky-500 ring-2 ring-sky-500/20 shadow-md transform -translate-y-1'
                    : 'border-slate-200 shadow-sm hover:border-sky-300'
                }
        ${hoverEffect && !selected ? 'hover:shadow-lg hover:-translate-y-1 cursor-pointer' : ''}
        ${className}
      `}
            onClick={onClick}
        >
            {children}
        </div>
    );
};

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
    <div className={`p-5 border-b border-slate-100 ${className}`}>
        {children}
    </div>
);

export const CardBody: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
    <div className={`p-5 ${className}`}>
        {children}
    </div>
);

export const CardFooter: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = '' }) => (
    <div className={`p-4 border-t border-slate-100 bg-slate-50/50 rounded-b-xl ${className}`}>
        {children}
    </div>
);
