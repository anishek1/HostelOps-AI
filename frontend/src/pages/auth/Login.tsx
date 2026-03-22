/**
 * pages/auth/Login.tsx — S-03
 * Login with hostel code + room number + password.
 * Rebuilt to match Stitch design: "Login - HostelOPS AI"
 */

import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { isAxiosError } from 'axios';
import { useAuth } from '../../hooks/useAuth';
import { useHostelLookup } from '../../hooks/useHostelLookup';
import SkeletonCard from '../../components/SkeletonCard';
import { getDefaultRoute } from '../../lib/rolePermissions';
import type { HostelPublicInfo } from '../../types/user';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    inputBg: '#F6ECE5',
    danger: '#E83B2A',
    warning: '#FFB800',
};

interface LocationState {
    hostelCode?: string;
    hostelInfo?: HostelPublicInfo;
}

type ErrorType = 'general' | 'deactivated' | 'hostel_not_found';

interface ParsedError {
    type: ErrorType | 'not_verified' | 'rejected';
    message: string;
    rejectionReason?: string | null;
}

function parseError(err: unknown): ParsedError {
    if (!isAxiosError(err)) {
        return { type: 'general', message: 'Something went wrong. Please try again.' };
    }
    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (status === 401) {
        if (typeof detail === 'string' && detail.includes('not yet verified')) {
            return { type: 'not_verified', message: detail };
        }
        return { type: 'general', message: 'Wrong room number or password. Please try again.' };
    }
    if (status === 403) {
        if (detail && typeof detail === 'object' && 'detail' in detail) {
            const d = detail as { detail: string; reason?: string | null };
            return { type: 'rejected', message: d.detail, rejectionReason: d.reason ?? null };
        }
        if (typeof detail === 'string' && detail.includes('deactivated')) {
            return { type: 'deactivated', message: detail };
        }
        return { type: 'general', message: typeof detail === 'string' ? detail : 'Access denied.' };
    }
    if (status === 404) {
        return { type: 'hostel_not_found', message: 'Hostel not found. Check your hostel code.' };
    }
    return {
        type: 'general',
        message: typeof detail === 'string' ? detail : 'Login failed. Please try again.',
    };
}

export default function Login() {
    const navigate = useNavigate();
    const location = useLocation();
    const { login, isAuthenticated, user } = useAuth();

    const state = location.state as LocationState | null;

    const [hostelCode, setHostelCode] = useState(state?.hostelCode ?? '');
    const [roomNumber, setRoomNumber] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);
    const [errorType, setErrorType] = useState<ErrorType | null>(null);

    const { hostelInfo, isLoading: codeLoading, error: codeError } = useHostelLookup(hostelCode);

    useEffect(() => {
        if (isAuthenticated && user) {
            navigate(getDefaultRoute(user.role), { replace: true });
        }
    }, [isAuthenticated, user, navigate]);

    function handleCodeChange(e: React.ChangeEvent<HTMLInputElement>) {
        setHostelCode(e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, ''));
        setErrorType(null);
        setErrorMsg(null);
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setErrorMsg(null);
        setErrorType(null);
        setIsLoading(true);

        try {
            await login({ room_number: roomNumber.trim(), password, hostel_code: hostelCode });
        } catch (err: unknown) {
            const parsed = parseError(err);

            if (parsed.type === 'not_verified') {
                navigate('/auth/pending', { replace: true });
                return;
            }
            if (parsed.type === 'rejected') {
                navigate('/auth/rejected', {
                    replace: true,
                    state: { reason: parsed.rejectionReason },
                });
                return;
            }
            setErrorType(parsed.type === 'hostel_not_found' ? 'hostel_not_found' : 'general');
            if (parsed.type === 'deactivated') setErrorType('deactivated');
            setErrorMsg(parsed.message);
        } finally {
            setIsLoading(false);
        }
    }

    const showCodePreview = hostelCode.trim().length >= 4;
    const canSubmit = hostelCode && roomNumber && password && !isLoading;

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
            {/* Decorative arc */}
            <div
                style={{
                    position: 'absolute',
                    top: -100,
                    right: -100,
                    width: 400,
                    height: 400,
                    borderRadius: '50%',
                    border: '60px solid rgba(70,71,211,0.04)',
                    pointerEvents: 'none',
                    zIndex: 0,
                }}
            />

            {/* Main content */}
            <main
                style={{
                    width: '100%',
                    padding: '80px 24px 32px',
                    display: 'flex',
                    flexDirection: 'column',
                    flex: 1,
                    position: 'relative',
                    zIndex: 1,
                    overflowY: 'auto',
                }}
            >
                {/* Header */}
                <header style={{ marginBottom: 32 }}>
                    <h1
                        style={{
                            fontSize: 32,
                            fontWeight: 800,
                            color: C.textPrimary,
                            letterSpacing: '-0.02em',
                            margin: 0,
                        }}
                    >
                        Welcome back.
                    </h1>
                    <p
                        style={{
                            fontSize: 15,
                            color: C.textSecondary,
                            marginTop: 6,
                            fontWeight: 400,
                        }}
                    >
                        Sign in to your hostel account.
                    </p>
                </header>

                <form onSubmit={handleSubmit}>
                    {/* White card with all inputs */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 16,
                            padding: 20,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 14,
                            boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                        }}
                    >
                        {/* Hostel code field */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            <div style={inputRowStyle}>
                                <span
                                    className="material-symbols-outlined"
                                    style={fieldIconStyle}
                                >
                                    numbers
                                </span>
                                <input
                                    type="text"
                                    value={hostelCode}
                                    onChange={handleCodeChange}
                                    placeholder="e.g. IGBH-4821"
                                    maxLength={12}
                                    style={{
                                        ...inputStyle,
                                        fontFamily: 'monospace',
                                        letterSpacing: '0.06em',
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

                            {/* Live preview chip */}
                            {showCodePreview && !codeError && !codeLoading && hostelInfo && (
                                <div
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: 6,
                                        background: 'rgba(70,71,211,0.08)',
                                        padding: '4px 12px',
                                        borderRadius: 999,
                                        width: 'fit-content',
                                    }}
                                >
                                    <span
                                        className="material-symbols-outlined"
                                        style={{
                                            fontSize: 14,
                                            color: C.primary,
                                            fontVariationSettings: "'FILL' 1",
                                        }}
                                    >
                                        domain
                                    </span>
                                    <span
                                        style={{
                                            fontSize: 11,
                                            fontWeight: 600,
                                            color: C.primary,
                                            whiteSpace: 'nowrap',
                                        }}
                                    >
                                        {hostelInfo.name} · {hostelInfo.mode}
                                    </span>
                                </div>
                            )}
                            {showCodePreview && codeLoading && (
                                <SkeletonCard lines={1} />
                            )}
                            {codeError && (
                                <p style={{ fontSize: 12, color: C.danger, margin: 0, fontWeight: 500 }}>
                                    {codeError}
                                </p>
                            )}
                        </div>

                        {/* Room number */}
                        <div style={inputRowStyle}>
                            <span className="material-symbols-outlined" style={fieldIconStyle}>
                                door_front
                            </span>
                            <input
                                type="text"
                                value={roomNumber}
                                onChange={(e) => setRoomNumber(e.target.value)}
                                placeholder="Your room number"
                                autoComplete="username"
                                style={inputStyle}
                            />
                        </div>

                        {/* Password */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            <div style={inputRowStyle}>
                                <span className="material-symbols-outlined" style={fieldIconStyle}>
                                    lock
                                </span>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Your password"
                                    autoComplete="current-password"
                                    style={inputStyle}
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

                            {/* Forgot password */}
                            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <span
                                    style={{
                                        fontSize: 12,
                                        fontWeight: 500,
                                        color: C.primary,
                                        cursor: 'default',
                                    }}
                                >
                                    Forgot password?
                                </span>
                            </div>
                        </div>

                        {/* Error banner */}
                        {errorMsg && (
                            <div
                                role="alert"
                                style={{
                                    background: errorType === 'deactivated'
                                        ? 'rgba(255,184,0,0.08)'
                                        : 'rgba(232,59,42,0.06)',
                                    borderRadius: 10,
                                    padding: '10px 14px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 10,
                                }}
                            >
                                <span
                                    className="material-symbols-outlined"
                                    style={{
                                        fontSize: 20,
                                        color: errorType === 'deactivated' ? '#9E7600' : C.danger,
                                        flexShrink: 0,
                                    }}
                                >
                                    warning
                                </span>
                                <p
                                    style={{
                                        fontSize: 12,
                                        color: errorType === 'deactivated' ? '#9E7600' : C.danger,
                                        margin: 0,
                                        lineHeight: 1.4,
                                        fontWeight: 500,
                                    }}
                                >
                                    {errorMsg}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Sign in button */}
                    <button
                        type="submit"
                        disabled={!canSubmit}
                        style={{
                            width: '100%',
                            height: 52,
                            background: C.primary,
                            color: '#fff',
                            border: 'none',
                            borderRadius: 14,
                            fontSize: 14,
                            fontWeight: 600,
                            cursor: !canSubmit ? 'not-allowed' : 'pointer',
                            opacity: !canSubmit ? 0.6 : 1,
                            fontFamily: 'inherit',
                            marginTop: 20,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                            boxShadow: canSubmit ? '0 4px 16px rgba(70,71,211,0.2)' : 'none',
                        }}
                    >
                        {isLoading ? 'Signing in…' : 'Sign in'}
                        {!isLoading && (
                            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>
                                arrow_forward
                            </span>
                        )}
                    </button>

                    {/* Register link */}
                    <p
                        style={{
                            textAlign: 'center',
                            fontSize: 14,
                            color: C.textSecondary,
                            marginTop: 16,
                            fontWeight: 400,
                        }}
                    >
                        Don't have an account?{' '}
                        <Link
                            to="/auth/register"
                            style={{ color: C.primary, fontWeight: 700, textDecoration: 'none', marginLeft: 4 }}
                        >
                            Register
                        </Link>
                    </p>
                </form>
            </main>

            {/* Footer branding */}
            <footer
                style={{
                    paddingBottom: 32,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                <div
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        opacity: 0.3,
                        userSelect: 'none',
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{
                            color: C.primary,
                            fontSize: 18,
                            fontVariationSettings: "'FILL' 1",
                        }}
                    >
                        school
                    </span>
                    <span
                        style={{
                            fontSize: 14,
                            fontWeight: 800,
                            letterSpacing: '-0.02em',
                            color: C.textPrimary,
                        }}
                    >
                        HostelOPS AI
                    </span>
                </div>
            </footer>
        </div>
    );
}

// ── Shared input styles ─────────────────────────────────────────────────────────

const inputRowStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    background: '#F6ECE5',
    borderRadius: 12,
    height: 52,
    paddingLeft: 4,
};

const fieldIconStyle: React.CSSProperties = {
    padding: '0 12px',
    color: '#767586',
    fontSize: 20,
    flexShrink: 0,
};

const inputStyle: React.CSSProperties = {
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
