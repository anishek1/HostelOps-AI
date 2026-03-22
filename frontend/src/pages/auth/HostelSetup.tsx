/**
 * pages/auth/HostelSetup.tsx — S-01
 * One-time hostel creation. Warden creates hostel, auto-logs in, gets hostel code.
 * Rebuilt to match Stitch design: "Hostel Setup - Form" and "Hostel Setup - Success"
 */

import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { getMe, setupHostel } from '../../api/authApi';
import { useAuth } from '../../hooks/useAuth';
import type { HostelMode } from '../../types/user';

const C = {
    bg: '#FFF8F4',
    bgAlt: '#FCF2EB',
    primary: '#4647D3',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    inputBg: '#F6ECE5',
    success: '#16A085',
    danger: '#E83B2A',
};

// ── Reusable field components ────────────────────────────────────────────────

function SectionLabel({ children }: { children: React.ReactNode }) {
    return (
        <h2
            style={{
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'rgba(70,69,84,0.7)',
                margin: '0 0 12px',
            }}
        >
            {children}
        </h2>
    );
}

interface InputFieldProps {
    icon: string;
    placeholder: string;
    value: string;
    onChange: (v: string) => void;
    type?: string;
    autoComplete?: string;
    helperText?: string;
}

function InputField({ icon, placeholder, value, onChange, type = 'text', autoComplete, helperText }: InputFieldProps) {
    return (
        <div>
            <div
                style={{
                    position: 'relative',
                    display: 'flex',
                    alignItems: 'center',
                    height: 52,
                    background: C.inputBg,
                    borderRadius: 12,
                }}
            >
                <div
                    style={{
                        position: 'absolute',
                        left: 16,
                        top: '50%',
                        transform: 'translateY(-50%)',
                        pointerEvents: 'none',
                        display: 'flex',
                        alignItems: 'center',
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{ fontSize: 20, color: C.textSecondary }}
                    >
                        {icon}
                    </span>
                </div>
                <input
                    type={type}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder}
                    autoComplete={autoComplete}
                    style={{
                        width: '100%',
                        height: '100%',
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        paddingLeft: 48,
                        paddingRight: 16,
                        fontSize: 15,
                        color: C.textPrimary,
                        fontFamily: 'inherit',
                        fontWeight: 500,
                        boxSizing: 'border-box',
                    }}
                />
            </div>
            {helperText && (
                <p style={{ fontSize: 11, color: C.textSecondary, margin: '6px 4px 0', lineHeight: 1.4 }}>
                    {helperText}
                </p>
            )}
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function HostelSetup() {
    const navigate = useNavigate();
    const { setSession } = useAuth();

    const [hostelName, setHostelName] = useState('');
    const [hostelMode, setHostelMode] = useState<HostelMode>('college');
    const [totalFloors, setTotalFloors] = useState('3');
    const [capacity, setCapacity] = useState('200');
    const [wardenName, setWardenName] = useState('');
    const [wardenRoom, setWardenRoom] = useState('');
    const [wardenPassword, setWardenPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hostelCode, setHostelCode] = useState<string | null>(null);
    const [hostelNameSaved, setHostelNameSaved] = useState('');
    const [modeSaved, setModeSaved] = useState<HostelMode>('college');
    const [copied, setCopied] = useState(false);
    const [countdown, setCountdown] = useState<number | null>(null);
    const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        if (countdown === null) return;
        if (countdown <= 0) {
            navigate('/warden', { replace: true });
            return;
        }
        countdownRef.current = setInterval(() => {
            setCountdown((c) => (c !== null ? c - 1 : null));
        }, 1000);
        return () => {
            if (countdownRef.current) clearInterval(countdownRef.current);
        };
    }, [countdown, navigate]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        const floors = parseInt(totalFloors, 10);
        const cap = parseInt(capacity, 10);
        if (isNaN(floors) || floors < 1 || floors > 50) {
            setError('Total floors must be between 1 and 50.');
            setIsLoading(false);
            return;
        }

        try {
            const res = await setupHostel({
                hostel_name: hostelName.trim(),
                hostel_mode: hostelMode,
                total_floors: floors,
                total_students_capacity: isNaN(cap) ? 200 : cap,
                warden_name: wardenName.trim(),
                warden_room_number: wardenRoom.trim(),
                warden_password: wardenPassword,
            });

            localStorage.setItem('access_token', res.access_token);
            localStorage.setItem('refresh_token', res.refresh_token);
            const userProfile = await getMe();
            setSession(res.access_token, res.refresh_token, userProfile);

            setHostelNameSaved(hostelName.trim());
            setModeSaved(hostelMode);
            setHostelCode(res.hostel.code);
            setCountdown(4);
        } catch (err: unknown) {
            if (isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                setError(typeof detail === 'string' ? detail : 'Setup failed. Please try again.');
            } else {
                setError('Something went wrong. Please try again.');
            }
        } finally {
            setIsLoading(false);
        }
    }

    function copyCode() {
        if (!hostelCode) return;
        navigator.clipboard.writeText(hostelCode).then(() => {
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        });
    }

    // ── Success screen ────────────────────────────────────────────────────────
    if (hostelCode) {
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
                {/* Background accent blobs */}
                <div
                    style={{
                        position: 'absolute',
                        top: '25%',
                        right: -80,
                        width: 256,
                        height: 256,
                        background: '#FEB700',
                        opacity: 0.08,
                        borderRadius: '50%',
                        filter: 'blur(48px)',
                        pointerEvents: 'none',
                    }}
                />
                <div
                    style={{
                        position: 'absolute',
                        bottom: '25%',
                        left: -80,
                        width: 256,
                        height: 256,
                        background: C.primary,
                        opacity: 0.05,
                        borderRadius: '50%',
                        filter: 'blur(48px)',
                        pointerEvents: 'none',
                    }}
                />

                {/* Header */}
                <header
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '16px 24px',
                        background: C.bgAlt,
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        <button
                            type="button"
                            onClick={() => navigate('/warden', { replace: true })}
                            style={{
                                background: 'none',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                color: C.primary,
                                padding: 0,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
                                arrow_back
                            </span>
                        </button>
                        <h1
                            style={{
                                fontSize: 18,
                                fontWeight: 600,
                                color: C.primary,
                                letterSpacing: '-0.01em',
                                margin: 0,
                            }}
                        >
                            Set up your hostel
                        </h1>
                    </div>
                </header>

                {/* Success card */}
                <main
                    style={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '24px',
                        position: 'relative',
                        zIndex: 1,
                    }}
                >
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 20,
                            padding: 32,
                            width: '100%',
                            boxShadow: '0 4px 40px rgba(26,26,46,0.04)',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            textAlign: 'center',
                        }}
                    >
                        {/* Check icon */}
                        <div
                            style={{
                                width: 56,
                                height: 56,
                                borderRadius: '50%',
                                background: 'rgba(70,71,211,0.08)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: 24,
                            }}
                        >
                            <span
                                className="material-symbols-outlined"
                                style={{
                                    fontSize: 28,
                                    color: C.primary,
                                    fontVariationSettings: "'wght' 600",
                                }}
                            >
                                check
                            </span>
                        </div>

                        <h2
                            style={{
                                fontSize: 24,
                                fontWeight: 800,
                                color: C.textPrimary,
                                letterSpacing: '-0.02em',
                                lineHeight: 1.2,
                                margin: '0 0 8px',
                            }}
                        >
                            Your hostel is live.
                        </h2>
                        <p
                            style={{
                                fontSize: 14,
                                color: C.textSecondary,
                                lineHeight: 1.65,
                                margin: '0 0 28px',
                                padding: '0 8px',
                            }}
                        >
                            Share this code with your students so they can register.
                        </p>

                        {/* Code block */}
                        <div
                            style={{
                                width: '100%',
                                background: C.inputBg,
                                borderRadius: 12,
                                padding: 24,
                                marginBottom: 16,
                            }}
                        >
                            <span
                                style={{
                                    display: 'block',
                                    fontSize: 11,
                                    fontWeight: 700,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.08em',
                                    color: C.textMuted,
                                    marginBottom: 8,
                                }}
                            >
                                HOSTEL CODE
                            </span>
                            <div
                                style={{
                                    fontSize: 36,
                                    fontWeight: 800,
                                    color: C.textPrimary,
                                    letterSpacing: 4,
                                    lineHeight: 1,
                                    marginBottom: 16,
                                    fontFamily: 'monospace',
                                }}
                            >
                                {hostelCode}
                            </div>
                            <button
                                type="button"
                                onClick={copyCode}
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 8,
                                    padding: '8px 24px',
                                    background: copied ? 'rgba(22,160,133,0.08)' : 'rgba(70,71,211,0.08)',
                                    color: copied ? C.success : C.primary,
                                    border: 'none',
                                    borderRadius: 999,
                                    fontSize: 13,
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                }}
                            >
                                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                                    {copied ? 'check' : 'content_copy'}
                                </span>
                                {copied ? 'Copied!' : 'Copy code'}
                            </button>
                        </div>

                        {/* Metadata */}
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                marginBottom: 32,
                            }}
                        >
                            <span style={{ fontSize: 13, fontWeight: 500, color: C.textSecondary }}>
                                {hostelNameSaved}
                            </span>
                            <div
                                style={{
                                    width: 4,
                                    height: 4,
                                    borderRadius: '50%',
                                    background: C.textMuted,
                                }}
                            />
                            <span style={{ fontSize: 13, fontWeight: 500, color: C.textSecondary }}>
                                {modeSaved} mode
                            </span>
                        </div>

                        {/* Go to Dashboard */}
                        <button
                            type="button"
                            onClick={() => navigate('/warden', { replace: true })}
                            style={{
                                width: '100%',
                                height: 52,
                                background: C.primary,
                                color: '#fff',
                                border: 'none',
                                borderRadius: 12,
                                fontSize: 14,
                                fontWeight: 600,
                                cursor: 'pointer',
                                fontFamily: 'inherit',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: 8,
                                boxShadow: '0 8px 24px rgba(70,71,211,0.25)',
                            }}
                        >
                            Go to Dashboard
                            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                                arrow_forward
                            </span>
                        </button>

                        <p style={{ fontSize: 12, color: C.textMuted, marginTop: 12 }}>
                            Taking you there automatically in {countdown}s…
                        </p>
                    </div>
                </main>
            </div>
        );
    }

    // ── Setup form ────────────────────────────────────────────────────────────
    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                display: 'flex',
                flexDirection: 'column',
                maxWidth: 390,
                margin: '0 auto',
            }}
        >
            {/* Header */}
            <header
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '16px 24px',
                    background: C.bg,
                }}
            >
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <Link
                        to="/auth/landing"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            color: C.textSecondary,
                            textDecoration: 'none',
                        }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
                            arrow_back
                        </span>
                    </Link>
                </div>
            </header>

            {/* Scrollable form */}
            <form
                onSubmit={handleSubmit}
                style={{ flex: 1, overflowY: 'auto', padding: '0 24px', paddingBottom: 0 }}
            >
                {/* Hero */}
                <div style={{ marginBottom: 24 }}>
                    <h1
                        style={{
                            fontSize: 28,
                            fontWeight: 800,
                            color: C.textPrimary,
                            letterSpacing: '-0.02em',
                            lineHeight: 1.2,
                            margin: '0 0 8px',
                        }}
                    >
                        Set up your hostel
                    </h1>
                    <p style={{ fontSize: 14, color: C.textSecondary, margin: 0, lineHeight: 1.6 }}>
                        Takes 60 seconds. You'll get a unique hostel code to share with your students.
                    </p>
                </div>

                {/* Section 1: Hostel details */}
                <section style={{ marginBottom: 20 }}>
                    <SectionLabel>HOSTEL DETAILS</SectionLabel>
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 16,
                            padding: 20,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 16,
                        }}
                    >
                        {/* Hostel name */}
                        <InputField
                            icon="home"
                            placeholder="Hostel Name"
                            value={hostelName}
                            onChange={setHostelName}
                        />

                        {/* Mode toggle */}
                        <div>
                            <div
                                style={{
                                    display: 'flex',
                                    padding: 4,
                                    background: C.inputBg,
                                    borderRadius: 12,
                                    height: 48,
                                }}
                            >
                                {(['college', 'autonomous'] as HostelMode[]).map((m) => (
                                    <button
                                        key={m}
                                        type="button"
                                        onClick={() => setHostelMode(m)}
                                        style={{
                                            flex: 1,
                                            borderRadius: 10,
                                            border: 'none',
                                            background: hostelMode === m ? C.primary : 'transparent',
                                            color: hostelMode === m ? '#fff' : C.textSecondary,
                                            fontSize: 13,
                                            fontWeight: 600,
                                            cursor: 'pointer',
                                            fontFamily: 'inherit',
                                            transition: 'background 0.15s',
                                        }}
                                    >
                                        {m.charAt(0).toUpperCase() + m.slice(1)}
                                    </button>
                                ))}
                            </div>
                            {hostelMode === 'college' && (
                                <p style={{ fontSize: 11, color: C.textSecondary, margin: '8px 4px 0' }}>
                                    College mode requires roll number on student registration
                                </p>
                            )}
                        </div>

                        {/* Floors & Capacity row */}
                        <div style={{ display: 'flex', gap: 12 }}>
                            <div style={{ flex: 1 }}>
                                <InputField
                                    icon="stairs"
                                    placeholder="Floors"
                                    value={totalFloors}
                                    onChange={setTotalFloors}
                                    type="number"
                                />
                            </div>
                            <div style={{ flex: 1 }}>
                                <InputField
                                    icon="group"
                                    placeholder="Capacity"
                                    value={capacity}
                                    onChange={setCapacity}
                                    type="number"
                                />
                            </div>
                        </div>
                    </div>
                </section>

                {/* Section 2: Warden account */}
                <section style={{ marginBottom: 20 }}>
                    <SectionLabel>YOUR WARDEN ACCOUNT</SectionLabel>
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 16,
                            padding: 20,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 16,
                        }}
                    >
                        <InputField
                            icon="person"
                            placeholder="Full name"
                            value={wardenName}
                            onChange={setWardenName}
                            autoComplete="name"
                        />
                        <InputField
                            icon="door_front"
                            placeholder="Room/Office Number"
                            value={wardenRoom}
                            onChange={setWardenRoom}
                            autoComplete="username"
                            helperText="This becomes your login identifier"
                        />

                        {/* Password with visibility toggle */}
                        <div
                            style={{
                                position: 'relative',
                                display: 'flex',
                                alignItems: 'center',
                                height: 52,
                                background: C.inputBg,
                                borderRadius: 12,
                            }}
                        >
                            <div
                                style={{
                                    position: 'absolute',
                                    left: 16,
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    pointerEvents: 'none',
                                    display: 'flex',
                                }}
                            >
                                <span
                                    className="material-symbols-outlined"
                                    style={{ fontSize: 20, color: C.textSecondary }}
                                >
                                    lock
                                </span>
                            </div>
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={wardenPassword}
                                onChange={(e) => setWardenPassword(e.target.value)}
                                placeholder="Password"
                                autoComplete="new-password"
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    background: 'transparent',
                                    border: 'none',
                                    outline: 'none',
                                    paddingLeft: 48,
                                    paddingRight: 48,
                                    fontSize: 15,
                                    color: C.textPrimary,
                                    fontFamily: 'inherit',
                                    fontWeight: 500,
                                    boxSizing: 'border-box',
                                }}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((s) => !s)}
                                style={{
                                    position: 'absolute',
                                    right: 12,
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    color: C.textSecondary,
                                    display: 'flex',
                                    alignItems: 'center',
                                    padding: 0,
                                }}
                            >
                                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                                    {showPassword ? 'visibility_off' : 'visibility'}
                                </span>
                            </button>
                        </div>
                    </div>
                </section>

                {/* Error */}
                {error && (
                    <div
                        role="alert"
                        style={{
                            marginBottom: 16,
                            background: 'rgba(232,59,42,0.06)',
                            borderLeft: `3px solid ${C.danger}`,
                            borderRadius: '0 8px 8px 0',
                            padding: '10px 14px',
                            fontSize: 13,
                            color: C.danger,
                        }}
                    >
                        {error}
                    </div>
                )}

                <div style={{ height: 120 }} />
            </form>

            {/* Sticky CTA */}
            <footer
                style={{
                    position: 'sticky',
                    bottom: 0,
                    background: 'rgba(255,248,244,0.95)',
                    backdropFilter: 'blur(8px)',
                    padding: '12px 24px 28px',
                    borderTop: '1px solid rgba(0,0,0,0.04)',
                }}
            >
                <button
                    type="submit"
                    onClick={handleSubmit}
                    disabled={isLoading || !hostelName || !wardenName || !wardenRoom || !wardenPassword}
                    style={{
                        width: '100%',
                        height: 52,
                        background: C.primary,
                        color: '#fff',
                        border: 'none',
                        borderRadius: 999,
                        fontSize: 14,
                        fontWeight: 600,
                        cursor: isLoading ? 'not-allowed' : 'pointer',
                        opacity: isLoading || !hostelName || !wardenName || !wardenRoom || !wardenPassword ? 0.6 : 1,
                        fontFamily: 'inherit',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        boxShadow: '0 4px 16px rgba(70,71,211,0.15)',
                    }}
                >
                    {isLoading ? 'Creating hostel…' : 'Create Hostel'}
                    {!isLoading && (
                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                            arrow_forward
                        </span>
                    )}
                </button>
                <p style={{ textAlign: 'center', fontSize: 13, color: C.textSecondary, margin: '10px 0 0' }}>
                    Already registered?{' '}
                    <Link to="/auth/login" style={{ color: C.primary, fontWeight: 600, textDecoration: 'none' }}>
                        Sign in
                    </Link>
                </p>
            </footer>
        </div>
    );
}
