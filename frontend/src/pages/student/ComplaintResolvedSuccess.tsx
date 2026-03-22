/**
 * pages/student/ComplaintResolvedSuccess.tsx — Sprint F
 * Full-screen overlay shown after student confirms complaint resolved.
 * Route: /student/complaints/:id/resolved
 */

import { Link } from 'react-router-dom';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    card: '#FFFFFF',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.12)',
};

export default function ComplaintResolvedSuccess() {
    return (
        <div
            style={{
                minHeight: '100dvh',
                background: C.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '0 24px',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Radial confetti gradient background */}
            <div
                style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'radial-gradient(circle at 50% 40%, rgba(26,155,108,0.12) 0%, rgba(70,71,211,0.06) 40%, transparent 70%)',
                    pointerEvents: 'none',
                }}
            />

            {/* Decorative dots */}
            {[
                { top: '15%', left: '12%', size: 6, color: C.success },
                { top: '20%', right: '10%', size: 8, color: C.primary },
                { top: '72%', left: '8%', size: 5, color: C.primary },
                { top: '68%', right: '14%', size: 7, color: C.success },
                { top: '10%', left: '55%', size: 5, color: C.success },
                { top: '80%', left: '45%', size: 6, color: C.primary },
            ].map((dot, i) => (
                <div
                    key={i}
                    style={{
                        position: 'absolute',
                        top: dot.top,
                        left: 'left' in dot ? dot.left : undefined,
                        right: 'right' in dot ? (dot as { right: string }).right : undefined,
                        width: dot.size,
                        height: dot.size,
                        borderRadius: '50%',
                        background: dot.color,
                        opacity: 0.5,
                        pointerEvents: 'none',
                    }}
                />
            ))}

            {/* Card */}
            <div
                style={{
                    background: C.card,
                    borderRadius: 24,
                    padding: '36px 28px',
                    width: '100%',
                    maxWidth: 342,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    boxShadow: '0 8px 40px rgba(0,0,0,0.08)',
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {/* Success icon */}
                <div
                    style={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: C.successLight,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        marginBottom: 24,
                    }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{ fontSize: 42, color: C.success, fontVariationSettings: "'FILL' 1" }}
                    >
                        check_circle
                    </span>
                </div>

                <h1
                    style={{
                        fontSize: 22,
                        fontWeight: 800,
                        color: C.textPrimary,
                        lineHeight: 1.25,
                        margin: '0 0 10px',
                    }}
                >
                    Great, glad it's sorted!
                </h1>

                <p
                    style={{
                        fontSize: 14,
                        color: C.textSecondary,
                        lineHeight: 1.6,
                        margin: '0 0 32px',
                    }}
                >
                    Complaint closed. Thank you for confirming.
                    Your feedback helps us improve.
                </p>

                {/* Actions */}
                <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <Link
                        to="/student"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: 50,
                            background: C.success,
                            color: '#fff',
                            borderRadius: 14,
                            fontSize: 14,
                            fontWeight: 700,
                            textDecoration: 'none',
                            boxShadow: '0 4px 14px rgba(26,155,108,0.25)',
                        }}
                    >
                        Back to Home
                    </Link>
                    <Link
                        to="/student/complaints"
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            height: 50,
                            background: C.primaryLight,
                            color: C.primary,
                            borderRadius: 14,
                            fontSize: 14,
                            fontWeight: 700,
                            textDecoration: 'none',
                        }}
                    >
                        View History
                    </Link>
                </div>
            </div>
        </div>
    );
}
