import React from 'react';

interface ListingHeroProps {
    title: string;
    subtitle?: string;
    badges?: React.ReactNode;
    backgroundImage?: string;
    className?: string;
    children?: React.ReactNode;
}

export const ListingHero: React.FC<ListingHeroProps> = ({
    title,
    subtitle,
    badges,
    backgroundImage,
    className = '',
    children
}) => {
    return (
        <div className={`relative w-full bg-slate-900 text-white rounded-2xl overflow-hidden shadow-2xl ${className}`}>
            {backgroundImage && (
                <div className="absolute inset-0 z-0">
                    <img
                        src={backgroundImage}
                        alt={title}
                        className="w-full h-full object-cover opacity-40 mix-blend-overlay"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-transparent" />
                </div>
            )}

            <div className="relative z-10 p-6 md:p-8 flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                    {badges && <div className="flex flex-wrap gap-2 mb-2">{badges}</div>}
                    <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white text-shadow">{title}</h1>
                    {subtitle && <p className="text-slate-300 text-lg font-medium">{subtitle}</p>}
                </div>

                {children && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                        {children}
                    </div>
                )}
            </div>
        </div>
    );
};
