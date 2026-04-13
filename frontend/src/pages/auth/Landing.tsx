/**
 * pages/auth/Landing.tsx — S-02
 * Entry point: hostel code lookup → register / login / setup.
 * Rebuilt to match Stitch design: "Perfect Spacing - HostelOPS AI Landing Page"
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import SkeletonCard from '../../components/SkeletonCard';
import { useHostelLookup } from '../../hooks/useHostelLookup';
import { C } from '../../lib/theme';

export default function Landing() {
    const navigate = useNavigate();
    const [hostelCode, setHostelCode] = useState('');
    const { hostelInfo, isLoading, error } = useHostelLookup(hostelCode);

    function handleCodeChange(e: React.ChangeEvent<HTMLInputElement>) {
        setHostelCode(e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, ''));
    }

    function navigateWithCode(path: string) {
        navigate(path, { state: { hostelCode, hostelInfo } });
    }

    const showPreview = hostelCode.trim().length >= 4;

    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                display: 'flex',
                flexDirection: 'column',
                maxWidth: 390,
                margin: '0 auto',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Decorative glow */}
            <div
                style={{
                    position: 'fixed',
                    top: 0,
                    right: 0,
                    width: 300,
                    height: 300,
                    borderRadius: '50%',
                    background: C.primary,
                    filter: 'blur(80px)',
                    opacity: 0.06,
                    transform: 'translate(25%, -25%)',
                    pointerEvents: 'none',
                    zIndex: 0,
                }}
            />

            {/* Nav — brand pill */}
            <nav
                style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '16px 24px',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        background: C.primary,
                        padding: '8px 24px',
                        borderRadius: 999,
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{
                            fontSize: 16,
                            color: '#fff',
                            fontVariationSettings: "'FILL' 1",
                        }}
                    >
                        domain
                    </span>
                    <span
                        style={{
                            fontWeight: 700,
                            fontSize: 11,
                            letterSpacing: '0.1em',
                            textTransform: 'uppercase',
                            color: '#fff',
                        }}
                    >
                        HOSTELOPS AI
                    </span>
                </div>
            </nav>

            {/* Main */}
            <main
                style={{
                    flex: 1,
                    padding: '24px 32px 0',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                <h1
                    style={{
                        fontSize: 32,
                        fontWeight: 800,
                        color: C.textPrimary,
                        lineHeight: 1.2,
                        letterSpacing: '-0.02em',
                        margin: 0,
                    }}
                >
                    Your hostel,<br />managed smarter.
                </h1>
                <p
                    style={{
                        fontSize: 15,
                        color: C.textSecondary,
                        margin: '16px 0 0',
                        lineHeight: 1.65,
                        fontWeight: 500,
                    }}
                >
                    AI-powered complaint tracking, laundry booking, and mess feedback — all in one place.
                </p>

                <div style={{ height: 40 }} />

                {/* Input section */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <label
                        style={{
                            fontSize: 10,
                            fontWeight: 700,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                            color: C.textMuted,
                        }}
                    >
                        ENTER YOUR HOSTEL CODE
                    </label>

                    {/* Input with arrow button */}
                    <div style={{ position: 'relative' }}>
                        <span
                            className="material-symbols-outlined"
                            style={{
                                position: 'absolute',
                                left: 16,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                fontSize: 20,
                                color: C.textMuted,
                                pointerEvents: 'none',
                            }}
                        >
                            key
                        </span>
                        <input
                            type="text"
                            value={hostelCode}
                            onChange={handleCodeChange}
                            placeholder="e.g. ICEQ-3202"
                            maxLength={12}
                            style={{
                                width: '100%',
                                height: 52,
                                background: C.bgElevated,
                                border: `1px solid ${C.border}`,
                                borderRadius: 12,
                                paddingLeft: 48,
                                paddingRight: 52,
                                fontSize: 14,
                                fontFamily: 'monospace',
                                letterSpacing: '0.08em',
                                color: C.textPrimary,
                                fontWeight: 600,
                                outline: 'none',
                                boxSizing: 'border-box',
                            }}
                        />
                        <button
                            type="button"
                            onClick={() => navigateWithCode('/auth/register')}
                            style={{
                                position: 'absolute',
                                right: 8,
                                top: '50%',
                                transform: 'translateY(-50%)',
                                width: 36,
                                height: 36,
                                background: C.primary,
                                color: '#fff',
                                border: 'none',
                                borderRadius: 10,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                cursor: 'pointer',
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                                arrow_forward
                            </span>
                        </button>
                    </div>

                    {/* Error */}
                    {hostelCode && error && (
                        <p style={{ fontSize: 12, color: C.danger, margin: 0, fontWeight: 500 }}>
                            {error}
                        </p>
                    )}

                    {/* Preview card */}
                    {showPreview && !error && (
                        <div style={{ marginTop: 4 }}>
                            {isLoading ? (
                                <SkeletonCard lines={2} />
                            ) : hostelInfo ? (
                                <div
                                    style={{
                                        background: C.bgSurface,
                                        borderRadius: 20,
                                        padding: '16px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        border: `1px solid ${C.border}`,
                                    }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div
                                            style={{
                                                width: 40,
                                                height: 40,
                                                borderRadius: '50%',
                                                background: C.warningLight,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                            }}
                                        >
                                            <span
                                                className="material-symbols-outlined"
                                                style={{
                                                    fontSize: 20,
                                                    color: C.warning,
                                                    fontVariationSettings: "'FILL' 1",
                                                }}
                                            >
                                                school
                                            </span>
                                        </div>
                                        <p
                                            style={{
                                                fontSize: 14,
                                                fontWeight: 700,
                                                color: C.textPrimary,
                                                margin: 0,
                                            }}
                                        >
                                            {hostelInfo.name}
                                        </p>
                                    </div>
                                    <span
                                        style={{
                                            background: C.primary,
                                            color: '#fff',
                                            fontSize: 9,
                                            fontWeight: 800,
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.05em',
                                            padding: '3px 8px',
                                            borderRadius: 4,
                                        }}
                                    >
                                        {hostelInfo.mode}
                                    </span>
                                </div>
                            ) : null}
                        </div>
                    )}
                </div>

                <div style={{ height: 32 }} />

                {/* Action buttons */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <button
                        type="button"
                        onClick={() => navigateWithCode('/auth/register')}
                        style={{
                            width: '100%',
                            height: 52,
                            background: C.primary,
                            color: '#fff',
                            border: 'none',
                            borderRadius: 14,
                            fontSize: 15,
                            fontWeight: 700,
                            cursor: 'pointer',
                            fontFamily: 'inherit',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                        }}
                    >
                        Register as a student
                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                            arrow_right_alt
                        </span>
                    </button>

                    <Link
                        to="/auth/hostel-setup"
                        style={{
                            width: '100%',
                            height: 52,
                            background: C.card,
                            color: C.textPrimary,
                            border: `1.5px solid ${C.border}`,
                            borderRadius: 14,
                            fontSize: 15,
                            fontWeight: 700,
                            textDecoration: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                        }}
                    >
                        Set up my hostel
                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                            arrow_right_alt
                        </span>
                    </Link>
                </div>

                {/* Sign in link */}
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                    <button
                        type="button"
                        onClick={() => navigateWithCode('/auth/login')}
                        style={{
                            background: 'none',
                            border: 'none',
                            padding: 0,
                            fontSize: 15,
                            color: C.textSecondary,
                            cursor: 'pointer',
                            fontFamily: 'inherit',
                        }}
                    >
                        Already have an account?{' '}
                        <span
                            style={{
                                color: C.primary,
                                fontWeight: 700,
                                textDecoration: 'underline',
                                textUnderlineOffset: 4,
                                textDecorationThickness: 2,
                            }}
                        >
                            Sign in →
                        </span>
                    </button>
                </div>
            </main>

            {/* Footer */}
            <footer
                style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '40px 24px 24px',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                <p
                    style={{
                        fontSize: 10,
                        fontWeight: 500,
                        letterSpacing: '0.08em',
                        textTransform: 'uppercase',
                        color: C.textMuted,
                        opacity: 0.6,
                        margin: 0,
                    }}
                >
                    POWERED BY HOSTELOPS INTELLIGENCE • V1.0
                </p>
            </footer>
        </div>
    );
}
