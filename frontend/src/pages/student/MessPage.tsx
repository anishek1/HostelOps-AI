/**
 * pages/student/MessPage.tsx — Sprint F
 * Three tabs: Menu viewer, Rate (5-category feedback), History.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getMessMenu, submitFeedback, getMyFeedback } from '../../api/messApi';
import type { MealPeriod, MessRatings, MessFeedbackCreate } from '../../types/mess';
import { useAuth } from '../../hooks/useAuth';

const C = {
    bg: '#0A0A0F',
    primary: '#7C5CFC',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#F0F0F5',
    textSecondary: '#6B6B80',
    textMuted: '#6B6B80',
    card: '#13121A',
    danger: '#E83B2A',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.10)',
    amber: '#D48C00',
    amberLight: 'rgba(212,140,0,0.12)',
    border: 'rgba(255,255,255,0.06)',
};

type Tab = 'menu' | 'rate' | 'history';

const MEALS: { key: MealPeriod; label: string; icon: string; time: string }[] = [
    { key: 'breakfast', label: 'Breakfast', icon: 'light_mode', time: '7:30 – 9:00 AM' },
    { key: 'lunch',     label: 'Lunch',     icon: 'wb_twilight', time: '12:30 – 2:00 PM' },
    { key: 'dinner',    label: 'Dinner',    icon: 'dark_mode', time: '7:30 – 9:00 PM' },
];

const RATING_DIMS: { key: keyof MessRatings; label: string }[] = [
    { key: 'food_quality',  label: 'Food Quality' },
    { key: 'food_quantity', label: 'Food Quantity' },
    { key: 'hygiene',       label: 'Hygiene' },
    { key: 'menu_variety',  label: 'Menu Variety' },
    { key: 'timing',        label: 'Timing' },
];

function todayISO() {
    return new Date().toISOString().slice(0, 10);
}

function StarRow({ value, onChange }: { value: number; onChange: (v: number) => void }) {
    return (
        <div style={{ display: 'flex', gap: 4 }}>
            {[1, 2, 3, 4, 5].map((star) => (
                <button
                    key={star}
                    type="button"
                    onClick={() => onChange(star)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2 }}
                >
                    <span
                        className="material-symbols-outlined"
                        style={{
                            fontSize: 26,
                            color: star <= value ? '#D48C00' : '#E0E0E0',
                            fontVariationSettings: star <= value ? "'FILL' 1" : "'FILL' 0",
                        }}
                    >
                        star
                    </span>
                </button>
            ))}
        </div>
    );
}

function MenuTab({ selectedMeal, onMealChange }: { selectedMeal: MealPeriod; onMealChange: (m: MealPeriod) => void }) {
    const today = todayISO();
    const { data: menus = [], isLoading } = useQuery({
        queryKey: ['mess-menu', today],
        queryFn: () => getMessMenu(today),
    });

    const menu = menus.find((m) => m.meal === selectedMeal);

    return (
        <div>
            {/* Meal selector */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 20 }}>
                {MEALS.map((m) => {
                    const active = m.key === selectedMeal;
                    return (
                        <button
                            key={m.key}
                            onClick={() => onMealChange(m.key)}
                            style={{
                                background: active ? C.primaryLight : C.card,
                                border: `1.5px solid ${active ? C.primary + '40' : C.border}`,
                                borderRadius: 14,
                                padding: '12px 8px',
                                cursor: 'pointer',
                                fontFamily: 'inherit',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: 5,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 22, color: active ? C.primary : C.textMuted }}>
                                {m.icon}
                            </span>
                            <span style={{ fontSize: 12, fontWeight: 600, color: active ? C.primary : C.textPrimary }}>{m.label}</span>
                            <span style={{ fontSize: 10, color: C.textMuted }}>{m.time}</span>
                        </button>
                    );
                })}
            </div>

            {/* Menu card */}
            {isLoading ? (
                <div style={{ background: C.card, borderRadius: 16, height: 160 }} />
            ) : menu ? (
                <div style={{ background: C.card, borderRadius: 16, padding: 20, boxShadow: '0 1px 6px rgba(255,255,255,0.03)' }}>
                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>
                        Today's {MEALS.find((m) => m.key === selectedMeal)?.label} Menu
                    </p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {menu.items.map((item, i) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.primary, flexShrink: 0 }} />
                                <span style={{ fontSize: 14, color: C.textPrimary }}>{item}</span>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div style={{ background: C.card, borderRadius: 16, padding: '32px 20px', textAlign: 'center', boxShadow: '0 1px 6px rgba(255,255,255,0.03)' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 36, color: C.textMuted, display: 'block', marginBottom: 10 }}>restaurant_menu</span>
                    <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>Menu not posted yet for this meal.</p>
                </div>
            )}
        </div>
    );
}

function RateTab({ selectedMeal, onMealChange }: { selectedMeal: MealPeriod; onMealChange: (m: MealPeriod) => void }) {
    const qc = useQueryClient();
    const [ratings, setRatings] = useState<MessRatings>({
        food_quality: 0,
        food_quantity: 0,
        hygiene: 0,
        menu_variety: 0,
        timing: 0,
    });
    const [comment, setComment] = useState('');
    const [success, setSuccess] = useState(false);

    const mutation = useMutation({
        mutationFn: submitFeedback,
        onSuccess: () => {
            setSuccess(true);
            setRatings({ food_quality: 0, food_quantity: 0, hygiene: 0, menu_variety: 0, timing: 0 });
            setComment('');
            qc.invalidateQueries({ queryKey: ['my-feedback'] });
            setTimeout(() => setSuccess(false), 3000);
        },
    });

    const canSubmit = Object.values(ratings).every((v) => v > 0);

    function handleSubmit() {
        const payload: MessFeedbackCreate = {
            meal: selectedMeal,
            feedback_date: todayISO(),
            food_quality: ratings.food_quality,
            food_quantity: ratings.food_quantity,
            hygiene: ratings.hygiene,
            menu_variety: ratings.menu_variety,
            timing: ratings.timing,
        };
        if (comment.trim()) payload.comment = comment.trim();
        mutation.mutate(payload);
    }

    if (success) {
        return (
            <div style={{ background: C.card, borderRadius: 20, padding: '32px 20px', textAlign: 'center', boxShadow: '0 1px 6px rgba(255,255,255,0.03)' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 44, color: C.success, display: 'block', marginBottom: 12, fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                <h3 style={{ fontSize: 17, fontWeight: 700, color: C.textPrimary, margin: '0 0 6px' }}>Feedback submitted!</h3>
                <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>Thank you for rating today's meal.</p>
            </div>
        );
    }

    return (
        <div>
            {/* Meal selector */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 20 }}>
                {MEALS.map((m) => {
                    const active = m.key === selectedMeal;
                    return (
                        <button
                            key={m.key}
                            onClick={() => onMealChange(m.key)}
                            style={{
                                background: active ? C.primaryLight : C.card,
                                border: `1.5px solid ${active ? C.primary + '40' : C.border}`,
                                borderRadius: 14,
                                padding: '10px 6px',
                                cursor: 'pointer',
                                fontFamily: 'inherit',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: 5,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: active ? C.primary : C.textMuted }}>{m.icon}</span>
                            <span style={{ fontSize: 11, fontWeight: 600, color: active ? C.primary : C.textPrimary }}>{m.label}</span>
                        </button>
                    );
                })}
            </div>

            {/* Rating card */}
            <div style={{ background: C.card, borderRadius: 20, padding: '18px 20px', boxShadow: '0 1px 6px rgba(255,255,255,0.03)', marginBottom: 14 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>
                    Rate Today's {MEALS.find((m) => m.key === selectedMeal)?.label}
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                    {RATING_DIMS.map((dim) => (
                        <div key={dim.key} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: 14, color: C.textPrimary, fontWeight: 500 }}>{dim.label}</span>
                            <StarRow
                                value={ratings[dim.key]}
                                onChange={(v) => setRatings((r) => ({ ...r, [dim.key]: v }))}
                            />
                        </div>
                    ))}
                </div>
            </div>

            {/* Comment */}
            <div style={{ background: C.card, borderRadius: 16, padding: '14px 16px', boxShadow: '0 1px 6px rgba(255,255,255,0.03)', marginBottom: 16 }}>
                <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value.slice(0, 300))}
                    placeholder="Optional comment… (e.g. 'Rice was cold today')"
                    rows={3}
                    style={{
                        width: '100%',
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        resize: 'none',
                        fontSize: 13,
                        color: C.textPrimary,
                        fontFamily: 'inherit',
                        lineHeight: 1.6,
                        boxSizing: 'border-box',
                    }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <span style={{ fontSize: 11, color: C.textMuted }}>{comment.length}/300</span>
                </div>
            </div>

            {mutation.isError && (
                <p style={{ fontSize: 13, color: C.danger, margin: '0 0 12px', fontWeight: 500 }}>
                    Could not submit. Try again.
                </p>
            )}

            <button
                onClick={handleSubmit}
                disabled={!canSubmit || mutation.isPending}
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
                    opacity: canSubmit && !mutation.isPending ? 1 : 0.55,
                    fontFamily: 'inherit',
                    boxShadow: canSubmit ? '0 4px 14px rgba(70,71,211,0.25)' : 'none',
                }}
            >
                {mutation.isPending ? 'Submitting…' : 'Submit Feedback'}
            </button>
        </div>
    );
}

function HistoryTab() {
    const { data: history = [], isLoading } = useQuery({
        queryKey: ['my-feedback'],
        queryFn: getMyFeedback,
    });

    if (isLoading) {
        return <div style={{ background: C.card, borderRadius: 16, height: 120 }} />;
    }

    if (history.length === 0) {
        return (
            <div style={{ background: C.card, borderRadius: 16, padding: '40px 20px', textAlign: 'center', boxShadow: '0 1px 6px rgba(255,255,255,0.03)' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 36, color: C.textMuted, display: 'block', marginBottom: 10 }}>receipt_long</span>
                <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>No feedback submitted yet.</p>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {history.slice(0, 15).map((f) => {
                const avg = ((f.food_quality + f.food_quantity + f.hygiene + f.menu_variety + f.timing) / 5).toFixed(1);
                const meal = MEALS.find((m) => m.key === f.meal);
                return (
                    <div key={f.id} style={{ background: C.card, borderRadius: 14, padding: '14px 16px', boxShadow: '0 1px 4px rgba(255,255,255,0.03)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 16, color: C.textMuted }}>{meal?.icon ?? 'restaurant'}</span>
                                <span style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary }}>{meal?.label ?? f.meal}</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 14, color: '#D48C00', fontVariationSettings: "'FILL' 1" }}>star</span>
                                <span style={{ fontSize: 13, fontWeight: 700, color: C.textPrimary }}>{avg}</span>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 10, color: C.textMuted, background: '#1C1B24', padding: '2px 8px', borderRadius: 999 }}>
                                {new Date(f.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                            </span>
                            {f.comment && (
                                <span style={{ fontSize: 10, color: C.textMuted }}>· "{f.comment.slice(0, 40)}{f.comment.length > 40 ? '…' : ''}"</span>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default function MessPage() {
    const { user } = useAuth();
    const [tab, setTab] = useState<Tab>('menu');
    const [selectedMeal, setSelectedMeal] = useState<MealPeriod>('lunch');

    const streak = user?.feedback_streak ?? 0;

    const TABS: { key: Tab; label: string }[] = [
        { key: 'menu',    label: 'Menu' },
        { key: 'rate',    label: 'Rate' },
        { key: 'history', label: 'History' },
    ];

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Sticky Header */}
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '52px 20px 16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div
                                style={{
                                    width: 42,
                                    height: 42,
                                    borderRadius: 14,
                                    background: C.amberLight,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                }}
                            >
                                <span className="material-symbols-outlined" style={{ fontSize: 22, color: C.amber, fontVariationSettings: "'FILL' 1" }}>
                                    restaurant
                                </span>
                            </div>
                            <h1 style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: 0 }}>Mess</h1>
                        </div>
                        {streak > 0 && (
                            <div
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 5,
                                    background: C.amberLight,
                                    padding: '5px 12px',
                                    borderRadius: 999,
                                }}
                            >
                                <span style={{ fontSize: 14 }}>🔥</span>
                                <span style={{ fontSize: 12, fontWeight: 700, color: C.amber }}>{streak} day streak</span>
                            </div>
                        )}
                    </div>

                    {/* Sticky tab bar */}
                    <div style={{ display: 'flex', borderBottom: `1px solid ${C.border}`, paddingInline: 20 }}>
                        {TABS.map((t) => (
                            <button
                                key={t.key}
                                onClick={() => setTab(t.key)}
                                style={{
                                    flex: 1,
                                    height: 40,
                                    border: 'none',
                                    borderBottom: tab === t.key ? `2px solid ${C.primary}` : '2px solid transparent',
                                    background: 'transparent',
                                    color: tab === t.key ? C.primary : C.textSecondary,
                                    fontSize: 13,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                }}
                            >
                                {t.label}
                            </button>
                        ))}
                    </div>
                </header>

                {/* Tab content */}
                <div style={{ padding: '16px 20px 100px' }}>
                    {tab === 'menu'    && <MenuTab    selectedMeal={selectedMeal} onMealChange={setSelectedMeal} />}
                    {tab === 'rate'    && <RateTab    selectedMeal={selectedMeal} onMealChange={setSelectedMeal} />}
                    {tab === 'history' && <HistoryTab />}
                </div>
            </div>
        </AppShell>
    );
}
