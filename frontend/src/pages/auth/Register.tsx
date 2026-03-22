/**
 * pages/auth/Register.tsx — S-04
 * Student self-registration.
 * Rebuilt to match Stitch design: "Student Registration - Sticky Refined"
 */

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { register } from '../../api/authApi';
import { useHostelLookup } from '../../hooks/useHostelLookup';
import SkeletonCard from '../../components/SkeletonCard';
import type { HostelPublicInfo } from '../../types/user';

const C = {
    bg: '#FFF8F4',
    primary: '#4647D3',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    inputBg: '#F6ECE5',
    danger: '#E83B2A',
};

interface LocationState {
    hostelCode?: string;
    hostelInfo?: HostelPublicInfo;
}

export default function Register() {
    const navigate = useNavigate();
    const location = useLocation();
    const state = location.state as LocationState | null;

    const [hostelCode, setHostelCode] = useState(state?.hostelCode ?? '');
    const [name, setName] = useState('');
    const [roomNumber, setRoomNumber] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [rollNumber, setRollNumber] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { hostelInfo, isLoading: codeLoading, error: codeError } = useHostelLookup(hostelCode);
    const isCollege = hostelInfo?.mode === 'college';
    const showCodePreview = hostelCode.trim().length >= 4;

    function handleCodeChange(e: React.ChangeEvent<HTMLInputElement>) {
        setHostelCode(e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, ''));
        setError(null);
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!hostelInfo) return;
        setError(null);
        setIsLoading(true);

        try {
            await register({
                name: name.trim(),
                room_number: roomNumber.trim(),
                hostel_code: hostelCode.toUpperCase(),
                role: 'student',
                hostel_mode: hostelInfo.mode,
                password,
                roll_number: isCollege ? rollNumber.trim() : undefined,
            });
            navigate('/auth/pending', { replace: true });
        } catch (err: unknown) {
            if (isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                if (typeof detail === 'string') {
                    if (detail.includes('erp_document_url')) {
                        setError(
                            'Document upload is required for college mode. This feature arrives in V2 — please ask your warden to create your account.',
                        );
                    } else {
                        setError(detail);
                    }
                } else {
                    setError('Registration failed. Please try again.');
                }
            } else {
                setError('Something went wrong. Please try again.');
            }
        } finally {
            setIsLoading(false);
        }
    }

    const canSubmit =
        hostelCode && hostelInfo && name && roomNumber && password &&
        (!isCollege || rollNumber) && !isLoading;

    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                position: 'relative',
            }}
        >
            {/* Soft radial arc decoration */}
            <div
                style={{
                    position: 'fixed',
                    top: -50,
                    right: -50,
                    width: 200,
                    height: 200,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, rgba(70,71,211,0.05) 0%, transparent 70%)',
                    pointerEvents: 'none',
                    zIndex: 0,
                }}
            />

            {/* Fixed header */}
            <header
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    zIndex: 50,
                    display: 'flex',
                    alignItems: 'center',
                    padding: '0 24px',
                    height: 64,
                    background: C.bg,
                    maxWidth: 390,
                    margin: '0 auto',
                }}
            >
                <Link
                    to="/auth/landing"
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        color: C.primary,
                        textDecoration: 'none',
                    }}
                >
                    <span className="material-symbols-outlined" style={{ fontSize: 24 }}>
                        arrow_back
                    </span>
                </Link>
                <h1
                    style={{
                        marginLeft: 8,
                        fontSize: 18,
                        fontWeight: 600,
                        color: C.primary,
                        letterSpacing: '-0.01em',
                    }}
                >
                    Student Registration
                </h1>
            </header>

            {/* Scrollable content */}
            <main
                style={{
                    paddingTop: 96,
                    paddingBottom: 160,
                    paddingLeft: 24,
                    paddingRight: 24,
                    maxWidth: 390,
                    margin: '0 auto',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {/* Hero */}
                <section style={{ marginBottom: 36 }}>
                    <h2
                        style={{
                            fontSize: 28,
                            fontWeight: 800,
                            color: C.textPrimary,
                            lineHeight: 1.2,
                            letterSpacing: '-0.02em',
                            margin: 0,
                        }}
                    >
                        Create your account.
                    </h2>
                    <p
                        style={{
                            fontSize: 15,
                            color: C.textSecondary,
                            margin: '8px 0 0',
                            fontWeight: 500,
                            opacity: 0.8,
                        }}
                    >
                        Join your hostel community and manage your stay with ease.
                    </p>
                </section>

                {/* Hostel code section */}
                <section style={{ marginBottom: 28 }}>
                    <label style={sectionLabelStyle}>HOSTEL CODE</label>
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            height: 48,
                            background: C.inputBg,
                            borderRadius: 12,
                            paddingLeft: 4,
                            marginTop: 10,
                            border: codeError ? `1.5px solid ${C.danger}` : 'none',
                        }}
                    >
                        <span className="material-symbols-outlined" style={iconStyle}>numbers</span>
                        <input
                            type="text"
                            value={hostelCode}
                            onChange={handleCodeChange}
                            placeholder="Enter code"
                            maxLength={12}
                            style={{
                                ...inputInnerStyle,
                                fontFamily: 'monospace',
                                letterSpacing: '0.06em',
                                fontWeight: 600,
                            }}
                        />
                        {codeLoading && (
                            <span
                                className="material-symbols-outlined"
                                style={{ padding: '0 12px', color: C.textMuted, fontSize: 18 }}
                            >
                                progress_activity
                            </span>
                        )}
                    </div>

                    {/* Preview chips */}
                    {showCodePreview && !codeError && !codeLoading && hostelInfo && (
                        <div
                            style={{
                                marginTop: 14,
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                flexWrap: 'wrap',
                            }}
                        >
                            <div
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    background: C.card,
                                    padding: '8px 12px',
                                    borderRadius: 999,
                                    boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                                }}
                            >
                                <span
                                    className="material-symbols-outlined"
                                    style={{
                                        color: C.primary,
                                        fontSize: 18,
                                        marginRight: 8,
                                        fontVariationSettings: "'FILL' 1",
                                    }}
                                >
                                    domain
                                </span>
                                <span
                                    style={{
                                        fontSize: 14,
                                        fontWeight: 600,
                                        color: C.textPrimary,
                                    }}
                                >
                                    {hostelInfo.name}
                                </span>
                            </div>
                            <div
                                style={{
                                    background: '#FEB700',
                                    padding: '4px 12px',
                                    borderRadius: 999,
                                }}
                            >
                                <span
                                    style={{
                                        fontSize: 10,
                                        fontWeight: 800,
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.08em',
                                        color: '#6B4B00',
                                    }}
                                >
                                    {hostelInfo.mode} MODE
                                </span>
                            </div>
                        </div>
                    )}
                    {showCodePreview && codeLoading && (
                        <div style={{ marginTop: 10 }}><SkeletonCard lines={1} /></div>
                    )}
                    {codeError && (
                        <p style={{ fontSize: 12, color: C.danger, margin: '6px 0 0', fontWeight: 500 }}>
                            {codeError}
                        </p>
                    )}
                </section>

                {/* College mode explanation banner */}
                {isCollege && (
                    <div
                        style={{
                            background: '#FCF2EB',
                            borderRadius: 16,
                            padding: 20,
                            marginBottom: 28,
                            display: 'flex',
                            gap: 16,
                            border: '1px solid rgba(0,0,0,0.06)',
                        }}
                    >
                        <div
                            style={{
                                width: 40,
                                height: 40,
                                borderRadius: 12,
                                background: 'rgba(255,255,255,0.6)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ color: C.primary, fontSize: 20 }}>
                                school
                            </span>
                        </div>
                        <div>
                            <p style={{ fontSize: 14, fontWeight: 700, color: C.textPrimary, margin: '0 0 4px' }}>
                                Roll number required
                            </p>
                            <p style={{ fontSize: 12, color: C.textSecondary, margin: 0, lineHeight: 1.5 }}>
                                This hostel verifies students using their college roll number.
                            </p>
                        </div>
                    </div>
                )}

                {/* Main details card */}
                <div
                    style={{
                        background: C.card,
                        borderRadius: 20,
                        padding: 24,
                        marginBottom: 28,
                        border: '1px solid rgba(0,0,0,0.05)',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
                    }}
                >
                    {/* Full name */}
                    <div style={{ marginBottom: 24 }}>
                        <label style={sectionLabelStyle}>YOUR NAME</label>
                        <div style={{ ...fieldRowStyle, marginTop: 10 }}>
                            <span className="material-symbols-outlined" style={iconStyle}>person</span>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter your full name"
                                autoComplete="name"
                                style={inputInnerStyle}
                            />
                        </div>
                    </div>

                    {/* Room number */}
                    <div style={{ marginBottom: 24 }}>
                        <label style={sectionLabelStyle}>ROOM NUMBER</label>
                        <div style={{ ...fieldRowStyle, marginTop: 10 }}>
                            <span className="material-symbols-outlined" style={iconStyle}>door_open</span>
                            <input
                                type="text"
                                value={roomNumber}
                                onChange={(e) => setRoomNumber(e.target.value)}
                                placeholder="e.g. 201-A"
                                autoComplete="username"
                                style={inputInnerStyle}
                            />
                        </div>
                        <p style={{ fontSize: 11, color: C.textSecondary, margin: '8px 0 0', opacity: 0.7, lineHeight: 1.4 }}>
                            Rooms shared by multiple students use suffixes — 201-A, 201-B, 201-C
                        </p>
                    </div>

                    {/* Roll number (college only) */}
                    {isCollege && (
                        <div style={{ marginBottom: 24 }}>
                            <label style={sectionLabelStyle}>ROLL NUMBER</label>
                            <div style={{ ...fieldRowStyle, marginTop: 10 }}>
                                <span className="material-symbols-outlined" style={iconStyle}>badge</span>
                                <input
                                    type="text"
                                    value={rollNumber}
                                    onChange={(e) => setRollNumber(e.target.value)}
                                    placeholder="Enter your full college roll number"
                                    style={inputInnerStyle}
                                />
                            </div>
                        </div>
                    )}

                    {/* Password */}
                    <div>
                        <label style={sectionLabelStyle}>PASSWORD</label>
                        <div style={{ ...fieldRowStyle, marginTop: 10 }}>
                            <span className="material-symbols-outlined" style={iconStyle}>lock</span>
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Create a password"
                                autoComplete="new-password"
                                style={inputInnerStyle}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((s) => !s)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    padding: '0 12px',
                                    cursor: 'pointer',
                                    color: C.textMuted,
                                    display: 'flex',
                                    alignItems: 'center',
                                }}
                            >
                                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                                    {showPassword ? 'visibility_off' : 'visibility'}
                                </span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Error banner */}
                {error && (
                    <div
                        role="alert"
                        style={{
                            background: 'rgba(232,59,42,0.06)',
                            borderLeft: `3px solid ${C.danger}`,
                            borderRadius: '0 8px 8px 0',
                            padding: '10px 14px',
                            fontSize: 13,
                            color: C.danger,
                            marginBottom: 16,
                        }}
                    >
                        {error}
                    </div>
                )}

                {/* Sign in link */}
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <p style={{ fontSize: 14, fontWeight: 500, color: C.textSecondary, margin: 0 }}>
                        Already have an account?{' '}
                        <Link
                            to="/auth/login"
                            style={{ color: C.primary, fontWeight: 700, textDecoration: 'none' }}
                        >
                            Sign in
                        </Link>
                    </p>
                </div>
            </main>

            {/* Sticky bottom CTA */}
            <div
                style={{
                    position: 'fixed',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    zIndex: 50,
                    maxWidth: 390,
                    margin: '0 auto',
                }}
            >
                {/* Gradient fade */}
                <div
                    style={{
                        height: 48,
                        background: `linear-gradient(to top, ${C.bg}, transparent)`,
                    }}
                />
                <div style={{ background: C.bg, padding: '8px 24px 32px' }}>
                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={!canSubmit}
                        style={{
                            width: '100%',
                            height: 52,
                            background: canSubmit
                                ? 'linear-gradient(135deg, #2C29BB, #4647D3)'
                                : '#C4C4D4',
                            color: '#fff',
                            border: 'none',
                            borderRadius: 24,
                            fontSize: 16,
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                            cursor: !canSubmit ? 'not-allowed' : 'pointer',
                            fontFamily: 'inherit',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                            boxShadow: canSubmit ? '0 8px 24px rgba(70,71,211,0.2)' : 'none',
                        }}
                    >
                        <span>{isLoading ? 'Creating account…' : 'Register'}</span>
                        {!isLoading && (
                            <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                                arrow_forward
                            </span>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ── Shared styles ──────────────────────────────────────────────────────────────

const sectionLabelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    color: '#464554',
};

const fieldRowStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    height: 52,
    background: '#F6ECE5',
    borderRadius: 12,
    paddingLeft: 4,
};

const iconStyle: React.CSSProperties = {
    padding: '0 12px',
    color: '#767586',
    fontSize: 20,
    flexShrink: 0,
};

const inputInnerStyle: React.CSSProperties = {
    flex: 1,
    height: '100%',
    background: 'transparent',
    border: 'none',
    outline: 'none',
    fontSize: 15,
    color: '#1A1A2E',
    fontFamily: 'inherit',
    fontWeight: 500,
};
