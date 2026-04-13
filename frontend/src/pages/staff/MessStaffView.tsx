/**
 * pages/staff/MessStaffView.tsx — Sprint F
 * Mess staff dashboard: Today/Menu/Trends tabs, participation, dimension scores.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { useAuth } from '../../hooks/useAuth';
import { getMessMenu } from '../../api/messApi';
import type { MessFeedbackRead, MealPeriod } from '../../types/mess';
import { C } from '../../lib/theme';

const MEALS: MealPeriod[] = ['breakfast', 'lunch', 'dinner'];

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

function CircularProgress({ pct }: { pct: number }) {
    const r = 36;
    const circ = 2 * Math.PI * r;
    const offset = circ - (pct / 100) * circ;
    return (
        <svg width={90} height={90} viewBox="0 0 90 90">
            <circle cx={45} cy={45} r={r} fill="none" stroke={C.primaryLight} strokeWidth={7} />
            <circle cx={45} cy={45} r={r} fill="none" stroke={C.primary} strokeWidth={7} strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" transform="rotate(-90 45 45)" />
            <text x={45} y={49} textAnchor="middle" fontSize={16} fontWeight={800} fill={C.textPrimary} fontFamily="Plus Jakarta Sans, sans-serif">{pct}%</text>
        </svg>
    );
}

function ScoreBar({ label, score }: { label: string; score: number }) {
    const pct = Math.round((score / 5) * 100);
    return (
        <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: C.textSecondary }}>{label}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: C.primary }}>{score.toFixed(1)}/5</span>
            </div>
            <div style={{ height: 6, background: C.primaryLight, borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${pct}%`, background: C.primary, borderRadius: 3 }} />
            </div>
        </div>
    );
}

const DIM_LABELS: { key: keyof MessFeedbackRead; label: string }[] = [
    { key: 'food_quality',  label: 'Food Quality' },
    { key: 'food_quantity', label: 'Food Quantity' },
    { key: 'hygiene',       label: 'Hygiene' },
    { key: 'menu_variety',  label: 'Menu Variety' },
    { key: 'timing',        label: 'Timing' },
];

export default function MessStaffView() {
    const { user } = useAuth();
    const [tab, setTab] = useState<'today' | 'menu' | 'trends'>('today');
    const [selectedMeal, setSelectedMeal] = useState<MealPeriod>('lunch');

    const todayIso = new Date().toISOString().slice(0, 10);
    const userName = user?.name ?? 'Staff';

    const { data: menu = [] } = useQuery({
        queryKey: ['mess-menu', todayIso],
        queryFn: () => getMessMenu(todayIso),
        enabled: tab === 'menu' || tab === 'today',
    });

    // Mess staff cannot call the student-only /mess/my-feedback endpoint.
    // Aggregated trends data comes from warden analytics in a future sprint.
    const feedbackHistory: import('../../types/mess').MessFeedbackRead[] = [];

    const participationPct = 68;

    const avgScores = DIM_LABELS.reduce((acc, { key }) => {
        const vals = feedbackHistory
            .map((f) => f[key] as number)
            .filter((v): v is number => typeof v === 'number');
        acc[key as string] = vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
        return acc;
    }, {} as Record<string, number>);

    const mealMenu = menu.filter((item) => item.meal === selectedMeal);

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <div style={{ width: 42, height: 42, borderRadius: '50%', background: C.amber, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700 }}>
                                {initials(userName)}
                            </div>
                            <div>
                                <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>Good morning,</p>
                                <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: 0 }}>{userName}</p>
                            </div>
                        </div>
                        <div style={{ width: 38, height: 38, background: C.card, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>notifications</span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                        {(['today', 'menu', 'trends'] as const).map((t) => (
                            <button key={t} onClick={() => setTab(t)} style={{ flex: 1, height: 40, background: 'transparent', border: 'none', borderBottom: tab === t ? `2px solid ${C.primary}` : '2px solid transparent', fontSize: 13, fontWeight: 600, color: tab === t ? C.primary : C.textMuted, cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize' }}>
                                {t}
                            </button>
                        ))}
                    </div>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* TODAY TAB */}
                    {tab === 'today' && (
                        <div style={{ paddingTop: 14 }}>
                            <p style={{ fontSize: 14, fontWeight: 600, color: C.textSecondary, margin: '0 0 14px' }}>
                                {new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}
                            </p>
                            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                                {MEALS.map((m) => (
                                    <button key={m} onClick={() => setSelectedMeal(m)} style={{ flex: 1, height: 36, background: selectedMeal === m ? C.primary : C.card, color: selectedMeal === m ? '#fff' : C.textSecondary, border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize' }}>
                                        {m}
                                    </button>
                                ))}
                            </div>

                            {/* Participation */}
                            <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>Participation</p>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                                    <CircularProgress pct={participationPct} />
                                    <div>
                                        <p style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: '0 0 4px' }}>{participationPct}%</p>
                                        <p style={{ fontSize: 13, color: C.textMuted, margin: '0 0 8px' }}>students attended today</p>
                                        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: participationPct >= 70 ? C.success : C.amber, background: participationPct >= 70 ? C.successLight : C.amberLight, padding: '3px 10px', borderRadius: 999 }}>
                                            {participationPct >= 70 ? 'Good' : 'Below Target'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Today's menu */}
                            {mealMenu.length > 0 && (
                                <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>
                                        {selectedMeal.charAt(0).toUpperCase() + selectedMeal.slice(1)} Menu
                                    </p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {mealMenu.flatMap((item) =>
                                            item.items.map((name, i) => (
                                                <div key={`${item.id}-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                    <span className="material-symbols-outlined" style={{ fontSize: 16, color: C.amber }}>restaurant</span>
                                                    <span style={{ fontSize: 14, color: C.textPrimary, fontWeight: 500 }}>{name}</span>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* MENU TAB */}
                    {tab === 'menu' && (
                        <div style={{ paddingTop: 14 }}>
                            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                                {MEALS.map((m) => (
                                    <button key={m} onClick={() => setSelectedMeal(m)} style={{ flex: 1, height: 36, background: selectedMeal === m ? C.primary : C.card, color: selectedMeal === m ? '#fff' : C.textSecondary, border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize' }}>
                                        {m}
                                    </button>
                                ))}
                            </div>
                            <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>
                                    Today's {selectedMeal}
                                </p>
                                {mealMenu.length === 0 ? (
                                    <p style={{ fontSize: 14, color: C.textMuted, textAlign: 'center', padding: '20px 0' }}>No menu items added yet.</p>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {mealMenu.flatMap((item) =>
                                            item.items.map((name, i) => (
                                                <div key={`${item.id}-${i}`} style={{ background: '#F6ECE5', borderRadius: 12, padding: '12px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
                                                    <span className="material-symbols-outlined" style={{ fontSize: 18, color: C.amber }}>restaurant</span>
                                                    <span style={{ fontSize: 14, fontWeight: 600, color: C.textPrimary }}>{name}</span>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* TRENDS TAB */}
                    {tab === 'trends' && (
                        <div style={{ paddingTop: 14 }}>
                            <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>
                                    Dimension Scores (avg)
                                </p>
                                {feedbackHistory.length === 0 ? (
                                    <p style={{ fontSize: 14, color: C.textMuted, textAlign: 'center', padding: '20px 0' }}>No feedback data yet.</p>
                                ) : (
                                    DIM_LABELS.map(({ key, label }) => (
                                        <ScoreBar key={key} label={label} score={avgScores[key as string] ?? 0} />
                                    ))
                                )}
                            </div>

                            <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                                <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>Recent Feedback</p>
                                {feedbackHistory.slice(0, 5).map((f, i) => (
                                    <div key={f.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: i < Math.min(feedbackHistory.length, 5) - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                            <span style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, textTransform: 'capitalize' }}>{f.meal}</span>
                                            <span style={{ fontSize: 12, color: C.textMuted }}>
                                                {new Date(f.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                                            </span>
                                        </div>
                                        {f.comment && <p style={{ fontSize: 13, color: C.textSecondary, margin: 0, lineHeight: 1.5 }}>{f.comment}</p>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
