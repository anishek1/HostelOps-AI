/**
 * pages/student/FileComplaint.tsx — Sprint F
 * File a complaint: quick fill chips, textarea, anonymous toggle, submit.
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fileComplaint } from '../../api/complaintsApi';
import AppShell from '../../components/AppShell';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    danger: '#E83B2A',
    border: 'rgba(0,0,0,0.06)',
};

const CHIPS = [
    { label: 'Fan not working', prefix: '🔧' },
    { label: 'Water supply issue', prefix: '💧' },
    { label: 'Light not working', prefix: '💡' },
    { label: 'Bad food in mess', prefix: '🍽️' },
    { label: 'Laundry machine issue', prefix: '👕' },
];

const MAX = 1000;

export default function FileComplaint() {
    const navigate = useNavigate();
    const [text, setText] = useState('');
    const [isAnonymous, setIsAnonymous] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    function applyChip(chip: typeof CHIPS[0]) {
        const snippet = `${chip.prefix} ${chip.label}: `;
        setText((prev) => (prev ? `${prev}\n${snippet}` : snippet));
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        if (!text.trim()) return;
        setError(null);
        setLoading(true);
        try {
            const c = await fileComplaint({ text: text.trim(), is_anonymous: isAnonymous });
            navigate(`/student/complaints/${c.id}`, { replace: true });
        } catch {
            setError('Could not submit. Please try again.');
        } finally {
            setLoading(false);
        }
    }

    const canSubmit = text.trim().length > 0 && !loading;

    return (
        <AppShell hasStickyCta>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Sticky header */}
                <header
                    style={{
                        position: 'sticky',
                        top: 0,
                        zIndex: 20,
                        background: C.bg,
                        padding: '52px 20px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 12,
                    }}
                >
                    <button
                        onClick={() => navigate(-1)}
                        style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                    </button>
                    <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>
                        File a Complaint
                    </h1>
                </header>

                <form onSubmit={handleSubmit} style={{ padding: '0 20px 20px' }}>
                    {/* Section label */}
                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>
                        What's the issue?
                    </p>

                    {/* Quick fill */}
                    <div style={{ marginBottom: 16 }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 8px' }}>
                            Quick Fill
                        </p>
                        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4, scrollbarWidth: 'none' } as React.CSSProperties}>
                            {CHIPS.map((chip) => (
                                <button
                                    key={chip.label}
                                    type="button"
                                    onClick={() => applyChip(chip)}
                                    style={{
                                        flexShrink: 0,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 5,
                                        background: C.card,
                                        border: `1.5px solid ${C.border}`,
                                        borderRadius: 999,
                                        padding: '7px 14px',
                                        fontSize: 13,
                                        color: C.textPrimary,
                                        cursor: 'pointer',
                                        fontFamily: 'inherit',
                                        whiteSpace: 'nowrap',
                                    }}
                                >
                                    {chip.prefix} {chip.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Textarea card */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 16,
                            padding: '14px 16px',
                            boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
                            marginBottom: 14,
                        }}
                    >
                        <textarea
                            value={text}
                            onChange={(e) => setText(e.target.value.slice(0, MAX))}
                            placeholder="Describe your issue in detail… Our AI will classify it automatically."
                            rows={8}
                            style={{
                                width: '100%',
                                background: 'transparent',
                                border: 'none',
                                outline: 'none',
                                resize: 'none',
                                fontSize: 14,
                                color: C.textPrimary,
                                fontFamily: 'inherit',
                                lineHeight: 1.65,
                                boxSizing: 'border-box',
                            }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <span style={{ fontSize: 11, color: text.length > MAX * 0.9 ? C.danger : C.textMuted }}>
                                {text.length}/{MAX}
                            </span>
                        </div>
                    </div>

                    {/* Anonymous toggle */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 14,
                            padding: '14px 16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
                            marginBottom: 14,
                        }}
                    >
                        <div>
                            <p style={{ fontSize: 14, fontWeight: 600, color: C.textPrimary, margin: '0 0 2px' }}>
                                Submit anonymously
                            </p>
                            <p style={{ fontSize: 12, color: C.textSecondary, margin: 0 }}>
                                Your name won't appear in the complaint.
                            </p>
                        </div>
                        <button
                            type="button"
                            role="switch"
                            aria-checked={isAnonymous}
                            onClick={() => setIsAnonymous((v) => !v)}
                            style={{
                                width: 48,
                                height: 28,
                                borderRadius: 999,
                                background: isAnonymous ? C.primary : '#D1D5DB',
                                border: 'none',
                                cursor: 'pointer',
                                position: 'relative',
                                transition: 'background 0.2s',
                                flexShrink: 0,
                            }}
                        >
                            <span
                                style={{
                                    position: 'absolute',
                                    top: 3,
                                    left: isAnonymous ? 23 : 3,
                                    width: 22,
                                    height: 22,
                                    borderRadius: '50%',
                                    background: '#fff',
                                    boxShadow: '0 1px 4px rgba(0,0,0,0.18)',
                                    transition: 'left 0.2s',
                                    display: 'block',
                                }}
                            />
                        </button>
                    </div>

                    {error && (
                        <p style={{ fontSize: 13, color: C.danger, margin: '0 0 12px', fontWeight: 500 }}>{error}</p>
                    )}
                </form>
            </div>

            {/* Sticky CTA */}
            <div
                style={{
                    position: 'fixed',
                    bottom: 64,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: '100%',
                    maxWidth: 430,
                    padding: '12px 20px',
                    background: 'linear-gradient(to top, #FFF5EE 70%, transparent)',
                    zIndex: 30,
                }}
            >
                <button
                    onClick={handleSubmit as unknown as React.MouseEventHandler}
                    disabled={!canSubmit}
                    style={{
                        width: '100%',
                        height: 52,
                        background: C.primary,
                        color: '#fff',
                        border: 'none',
                        borderRadius: 14,
                        fontSize: 15,
                        fontWeight: 700,
                        cursor: canSubmit ? 'pointer' : 'not-allowed',
                        opacity: canSubmit ? 1 : 0.55,
                        fontFamily: 'inherit',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        boxShadow: canSubmit ? '0 4px 16px rgba(70,71,211,0.25)' : 'none',
                    }}
                >
                    {loading ? 'Submitting…' : <>Submit Complaint <span className="material-symbols-outlined" style={{ fontSize: 18 }}>arrow_forward</span></>}
                </button>
            </div>
        </AppShell>
    );
}
