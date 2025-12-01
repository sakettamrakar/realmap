import React, { useEffect, useState } from 'react';

const STEPS = [
    "Checking Registration...",
    "Scraping RERA Data...",
    "Matching Amenities...",
    "Validating Documents..."
];

interface Props {
    onComplete?: () => void;
}

export const ComplianceProgress: React.FC<Props> = ({ onComplete }) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const stepDuration = 800; // ms per step
        const totalDuration = stepDuration * STEPS.length;

        const stepInterval = setInterval(() => {
            setCurrentStep(prev => {
                if (prev < STEPS.length - 1) return prev + 1;
                return prev;
            });
        }, stepDuration);

        const progressInterval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 100) {
                    clearInterval(progressInterval);
                    clearInterval(stepInterval);
                    setTimeout(() => onComplete?.(), 500);
                    return 100;
                }
                return prev + (100 / (totalDuration / 50));
            });
        }, 50);

        return () => {
            clearInterval(stepInterval);
            clearInterval(progressInterval);
        };
    }, [onComplete]);

    return (
        <div style={{
            position: 'fixed',
            inset: 0,
            background: 'white',
            zIndex: 2000,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px'
        }}>
            <div style={{
                width: '64px',
                height: '64px',
                marginBottom: '32px',
                position: 'relative'
            }}>
                <svg className="animate-spin" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" opacity="0.25" />
                    <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
                </svg>
            </div>

            <h2 className="animate-fade-in" style={{
                fontSize: '20px',
                fontWeight: 600,
                marginBottom: '8px',
                textAlign: 'center',
                minHeight: '30px'
            }}>
                {STEPS[currentStep]}
            </h2>

            <div style={{
                width: '100%',
                maxWidth: '280px',
                height: '6px',
                background: '#f1f5f9',
                borderRadius: '999px',
                overflow: 'hidden',
                marginTop: '24px'
            }}>
                <div style={{
                    height: '100%',
                    background: 'var(--color-primary)',
                    width: `${progress}%`,
                    transition: 'width 0.1s linear'
                }} />
            </div>
        </div>
    );
};
