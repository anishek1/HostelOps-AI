/**
 * pages/student/Onboarding.tsx — Sprint F
 * 3-step feature tour shown once to new students.
 * Final step calls PATCH /api/users/me/onboarding-seen and navigates to /student.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../../api/client';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    card: '#FFFFFF',
    success: '#1A9B6C',
    amber: '#D48C00',
    amberLight: 'rgba(212,140,0,0.10)',
};

interface Step {
    pill: string;
    icon: string;
    iconColor: string;
    iconBg: string;
    floatIcon?: string;
    heading: string;
    sub: string;
}

const STEPS: Step[] = [
    {
        pill: '1 OF 3',
        icon: 'auto_awesome',
        iconColor: C.primary,
        iconBg: C.primaryLight,
        heading: 'AI-powered complaint resolution',
        sub: 'Describe your issue in plain words. Our AI classifies, routes, and tracks it to the right person — no forms, no guessing.',
    },
    {
        pill: '2 OF 3',
        icon: 'local_laundry_service',
        iconColor: C.primary,
        iconBg: C.primaryLight,
        floatIcon: 'calendar_today',
        heading: 'Book laundry slots — fair and transparent.',
        sub: 'Reserve washing machine time in advance. No more waiting around or arguments — everyone gets a fair turn.',
    },
    {
        pill: '3 OF 3',
        icon: 'restaurant',
        iconColor: C.amber,
        iconBg: C.amberLight,
        heading: 'Rate your mess, improve your meals.',
        sub: 'Quick daily feedback on food quality, quantity, hygiene, and more. Your ratings drive real improvements.',
    },
];

export default function Onboarding() {
    const navigate = useNavigate();
    const [step, setStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const current = STEPS[step];
    const isLast = step === STEPS.length - 1;

    async function handleNext() {
        if (!isLast) {
            setStep((s) => s + 1);
            return;
        }
        setLoading(true);
        try {
            await client.patch('/users/me/onboarding-seen');
        } catch {
            // Non-critical — proceed anyway
        } finally {
            setLoading(false);
        }
        navigate('/student', { replace: true });
    }

    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0 24px 48px',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Decorative arcs */}
            <div style={{ position: 'absolute', top: -60, right: -60, width: 240, height: 240, borderRadius: '50%', border: '40px solid rgba(70,71,211,0.04)', pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', bottom: -40, left: -40, width: 160, height: 160, borderRadius: '50%', border: '28px solid rgba(70,71,211,0.04)', pointerEvents: 'none' }} />

            {/* Step pill */}
            <div
                style={{
                    background: C.primaryLight,
                    color: C.primary,
                    fontSize: 11,
                    fontWeight: 700,
                    letterSpacing: '0.12em',
                    padding: '5px 14px',
                    borderRadius: 999,
                    marginBottom: 40,
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {current.pill}
            </div>

            {/* Illustration area */}
            <div
                style={{
                    position: 'relative',
                    width: 140,
                    height: 140,
                    marginBottom: 36,
                    zIndex: 1,
                }}
            >
                {/* Halo */}
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        background: current.iconBg,
                    }}
                />
                {/* Main icon */}
                <div
                    style={{
                        position: 'absolute',
                        inset: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{
                            fontSize: 64,
                            color: current.iconColor,
                            fontVariationSettings: "'FILL' 1",
                        }}
                    >
                        {current.icon}
                    </span>
                </div>
                {/* Floating badge icon */}
                {current.floatIcon && (
                    <div
                        style={{
                            position: 'absolute',
                            bottom: 4,
                            right: 4,
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            background: C.card,
                            boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.primary }}>
                            {current.floatIcon}
                        </span>
                    </div>
                )}
            </div>

            {/* Heading */}
            <h1
                style={{
                    fontSize: 26,
                    fontWeight: 800,
                    color: C.textPrimary,
                    textAlign: 'center',
                    lineHeight: 1.25,
                    margin: '0 0 14px',
                    maxWidth: 320,
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {current.heading}
            </h1>

            {/* Sub-text */}
            <p
                style={{
                    fontSize: 14,
                    color: C.textSecondary,
                    textAlign: 'center',
                    lineHeight: 1.65,
                    margin: '0 0 48px',
                    maxWidth: 300,
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {current.sub}
            </p>

            {/* Progress dots */}
            <div
                style={{
                    display: 'flex',
                    gap: 8,
                    marginBottom: 36,
                    alignItems: 'center',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {STEPS.map((_, i) => (
                    <div
                        key={i}
                        style={{
                            height: 8,
                            borderRadius: 999,
                            background: i === step ? C.primary : 'rgba(70,71,211,0.20)',
                            width: i === step ? 28 : 8,
                            transition: 'all 0.3s ease',
                        }}
                    />
                ))}
            </div>

            {/* CTA Button */}
            <button
                onClick={handleNext}
                disabled={loading}
                style={{
                    width: '100%',
                    maxWidth: 342,
                    height: 54,
                    background: C.primary,
                    color: '#fff',
                    border: 'none',
                    borderRadius: 14,
                    fontSize: 15,
                    fontWeight: 700,
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.7 : 1,
                    fontFamily: 'inherit',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    boxShadow: '0 6px 20px rgba(70,71,211,0.25)',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {loading ? 'Getting started…' : isLast ? "Let's go →" : 'Next →'}
            </button>

            {/* Skip link */}
            {!isLast && (
                <button
                    onClick={() => setStep(STEPS.length - 1)}
                    style={{
                        marginTop: 16,
                        background: 'none',
                        border: 'none',
                        fontSize: 13,
                        color: C.textSecondary,
                        cursor: 'pointer',
                        fontFamily: 'inherit',
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    Skip tour
                </button>
            )}
        </div>
    );
}
