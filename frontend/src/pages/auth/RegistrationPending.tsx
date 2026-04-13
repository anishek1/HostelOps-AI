/**
 * pages/auth/RegistrationPending.tsx — S-05
 * Shown after successful registration. Student waits for warden approval.
 * Rebuilt to match Stitch design: "Registration Pending"
 */

import { Link } from 'react-router-dom';
import { C } from '../../lib/theme';

const steps = [
    'Warden reviews your details',
    'You get notified once approved',
    'Log in and get started',
];

export default function RegistrationPending() {
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
            {/* Decorative arc */}
            <div
                style={{
                    position: 'absolute',
                    top: -40,
                    right: -40,
                    width: 256,
                    height: 256,
                    borderRadius: '50%',
                    border: '40px solid rgba(70,71,211,0.04)',
                    pointerEvents: 'none',
                }}
            />

            <main
                style={{
                    position: 'relative',
                    width: 390,
                    maxWidth: '100vw',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    padding: '0 24px',
                }}
            >
                {/* Hourglass with glow halo */}
                <div
                    style={{
                        position: 'relative',
                        width: 96,
                        height: 96,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: 20,
                    }}
                >
                    <div
                        style={{
                            position: 'absolute',
                            width: 80,
                            height: 80,
                            borderRadius: '50%',
                            background: 'rgba(70,71,211,0.15)',
                        }}
                    />
                    <span
                        className="material-symbols-outlined"
                        style={{
                            fontSize: 40,
                            color: C.primary,
                            position: 'relative',
                        }}
                    >
                        hourglass_empty
                    </span>
                </div>

                {/* Heading */}
                <h1
                    style={{
                        fontSize: 28,
                        fontWeight: 800,
                        color: C.textPrimary,
                        lineHeight: 1.2,
                        margin: '0 0 8px',
                    }}
                >
                    You're on the list.
                </h1>

                {/* Description */}
                <p
                    style={{
                        fontSize: 14,
                        color: C.textSecondary,
                        lineHeight: 1.6,
                        margin: '0 0 28px',
                        padding: '0 8px',
                    }}
                >
                    Your registration is under review. An assistant warden will verify your details and approve your account.
                </p>

                {/* What happens next card */}
                <div
                    style={{
                        width: '100%',
                        background: C.card,
                        borderRadius: 16,
                        padding: 20,
                        textAlign: 'left',
                    }}
                >
                    <h2
                        style={{
                            fontSize: 13,
                            fontWeight: 700,
                            color: C.textPrimary,
                            textTransform: 'uppercase',
                            letterSpacing: '0.08em',
                            margin: '0 0 20px',
                        }}
                    >
                        What happens next
                    </h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        {steps.map((step, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                <div
                                    style={{
                                        flexShrink: 0,
                                        width: 22,
                                        height: 22,
                                        borderRadius: '50%',
                                        background: C.primary,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#fff',
                                        fontSize: 11,
                                        fontWeight: 700,
                                    }}
                                >
                                    {i + 1}
                                </div>
                                <p style={{ fontSize: 14, color: C.textSecondary, margin: 0 }}>
                                    {step}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Bottom link */}
                <div style={{ marginTop: 24 }}>
                    <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>
                        Wrong hostel?{' '}
                        <Link
                            to="/auth/register"
                            style={{ color: C.primary, fontWeight: 600, marginLeft: 4, textDecoration: 'none' }}
                        >
                            Go back and re-register
                        </Link>
                    </p>
                </div>
            </main>
        </div>
    );
}
