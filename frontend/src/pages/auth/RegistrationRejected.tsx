/**
 * pages/auth/RegistrationRejected.tsx — S-06
 * Shown when login detects is_rejected=true.
 * Rebuilt to match Stitch design: "Registration Rejected"
 */

import { Link, useLocation } from 'react-router-dom';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    card: '#FFFFFF',
    danger: '#E83B2A',
};

interface LocationState {
    reason?: string | null;
}

export default function RegistrationRejected() {
    const location = useLocation();
    const state = location.state as LocationState | null;
    const reason = state?.reason ?? null;

    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Decorative arcs (concentric circles, top-right) */}
            <div
                style={{
                    position: 'absolute',
                    top: -40,
                    right: -40,
                    width: 192,
                    height: 192,
                    borderRadius: '50%',
                    border: '1px solid rgba(70,71,211,0.05)',
                    pointerEvents: 'none',
                }}
            />
            <div
                style={{
                    position: 'absolute',
                    top: -64,
                    right: -64,
                    width: 256,
                    height: 256,
                    borderRadius: '50%',
                    border: '1px solid rgba(70,71,211,0.05)',
                    pointerEvents: 'none',
                }}
            />

            <div
                style={{
                    width: 390,
                    maxWidth: '100vw',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: '0 24px',
                    gap: 24,
                    position: 'relative',
                }}
            >
                {/* Icon with red halo */}
                <div
                    style={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: 'rgba(232,59,42,0.10)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{ fontSize: 40, color: C.danger }}
                    >
                        unsubscribe
                    </span>
                </div>

                {/* Header */}
                <div style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <h1
                        style={{
                            fontSize: 28,
                            fontWeight: 800,
                            color: C.textPrimary,
                            lineHeight: 1.2,
                            margin: 0,
                        }}
                    >
                        Registration rejected.
                    </h1>
                </div>

                {/* Rejection reason card */}
                <div
                    style={{
                        width: '100%',
                        background: C.card,
                        borderRadius: 16,
                        padding: 20,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                    }}
                >
                    <span
                        style={{
                            fontSize: 11,
                            fontWeight: 600,
                            color: C.textSecondary,
                            letterSpacing: '0.08em',
                            textTransform: 'uppercase',
                        }}
                    >
                        REASON FROM WARDEN
                    </span>
                    <div
                        style={{
                            borderLeft: `3px solid ${C.danger}`,
                            paddingLeft: 12,
                        }}
                    >
                        <p
                            style={{
                                fontSize: 14,
                                color: C.textPrimary,
                                lineHeight: 1.6,
                                margin: 0,
                            }}
                        >
                            {reason ?? 'No reason was provided. Please contact your warden directly.'}
                        </p>
                    </div>
                </div>

                {/* Description */}
                <p
                    style={{
                        fontSize: 13,
                        color: C.textSecondary,
                        textAlign: 'center',
                        margin: 0,
                    }}
                >
                    You can fix the issue and submit a new registration request.
                </p>

                {/* Primary action */}
                <Link
                    to="/auth/register"
                    style={{
                        width: '100%',
                        height: 52,
                        background: C.primary,
                        color: '#fff',
                        borderRadius: 12,
                        fontSize: 14,
                        fontWeight: 600,
                        textDecoration: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 6,
                        boxSizing: 'border-box',
                    }}
                >
                    Re-register →
                </Link>

                {/* Secondary link */}
                <Link
                    to="/auth/login"
                    style={{
                        fontSize: 13,
                        fontWeight: 500,
                        color: C.textSecondary,
                        textDecoration: 'none',
                    }}
                >
                    Contact your warden for help
                </Link>
            </div>
        </div>
    );
}
