/**
 * pages/warden/WardenDashboard.tsx — Sprint F
 * Warden home: AI alert, stat tiles, performance grid, notices, quick access.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { useAuth } from '../../hooks/useAuth';
import { C } from '../../lib/theme';
import {
    getWardenAnalytics,
    getNotices,
    getPendingRegistrations,
    deleteNotice,
    postNotice,
} from '../../api/wardenApi';

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

export default function WardenDashboard() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const qc = useQueryClient();
    const [alertDismissed, setAlertDismissed] = useState(false);
    const [showNoticeForm, setShowNoticeForm] = useState(false);
    const [noticeTitle, setNoticeTitle] = useState('');
    const [noticeBody, setNoticeBody] = useState('');

    const { data: analytics } = useQuery({
        queryKey: ['warden-analytics'],
        queryFn: getWardenAnalytics,
    });

    const { data: notices = [] } = useQuery({
        queryKey: ['notices'],
        queryFn: getNotices,
    });

    const { data: pending = [] } = useQuery({
        queryKey: ['pending-registrations'],
        queryFn: getPendingRegistrations,
    });

    const deleteMut = useMutation({
        mutationFn: deleteNotice,
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notices'] }),
    });

    const postMut = useMutation({
        mutationFn: () => postNotice(noticeTitle, noticeBody),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['notices'] });
            setNoticeTitle('');
            setNoticeBody('');
            setShowNoticeForm(false);
        },
    });

    const userName = user?.name ?? 'Warden';
    const pendingApproval = analytics?.pending_count ?? 0;

    const performanceMetrics = [
        { label: 'Misclassification', value: analytics ? `${(analytics.misclassification_rate ?? 0).toFixed(0)}%` : '—', trend: '↓4%' },
        { label: 'False Severity',    value: analytics ? `${(analytics.false_severity_rate ?? 0).toFixed(0)}%` : '—',    trend: '↓2%' },
        { label: 'Resolution Rate',   value: analytics ? `${(analytics.resolution_rate ?? 0).toFixed(0)}%` : '—',        trend: '↑12%' },
        { label: 'Queue Latency',     value: analytics ? `${(analytics.queue_latency_minutes ?? 0).toFixed(0)}m` : '—',   trend: '↓5m' },
    ];

    const overrideCategories: [string, number][] = analytics?.override_rate_by_category
        ? Object.entries(analytics.override_rate_by_category).map(([k, v]) => [k, Number(v)])
        : [['Maintenance', 0.35], ['Mess', 0.20], ['Laundry', 0.15], ['Interpersonal', 0.08]];

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 42, height: 42, borderRadius: '50%', background: C.primary, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, flexShrink: 0 }}>
                            {initials(userName)}
                        </div>
                        <div>
                            <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>Hostel Warden</p>
                            <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: 0 }}>{userName}</p>
                        </div>
                    </div>
                    <button onClick={() => navigate('/student/notifications')} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', position: 'relative' }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>notifications</span>
                        <span style={{ position: 'absolute', top: 9, right: 9, width: 8, height: 8, borderRadius: '50%', background: C.danger, border: `1.5px solid ${C.bg}` }} />
                    </button>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* AI Alert */}
                    {!alertDismissed && (
                        <div style={{ background: C.dangerLight, borderRadius: 16, padding: '14px 16px', marginBottom: 14, display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.danger, marginTop: 2, flexShrink: 0 }}>warning</span>
                            <div style={{ flex: 1 }}>
                                <p style={{ fontSize: 13, fontWeight: 700, color: C.danger, margin: '0 0 2px' }}>AI Accuracy Alert</p>
                                <p style={{ fontSize: 12, color: C.textSecondary, margin: 0, lineHeight: 1.5 }}>
                                    Misclassification rate is 12% this week. Review recent complaints for override opportunities.
                                </p>
                            </div>
                            <button onClick={() => setAlertDismissed(true)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: C.textMuted, flexShrink: 0 }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>close</span>
                            </button>
                        </div>
                    )}

                    {/* Stat tiles */}
                    <div style={{ display: 'flex', gap: 12, marginBottom: 14 }}>
                        {[
                            { value: pending.length, label: 'Pending Registrations', icon: 'person_add', color: C.warning, bg: C.warningLight, to: '/warden/registrations' },
                            { value: pendingApproval, label: 'Awaiting Approval', icon: 'approval', color: C.primary, bg: C.primaryLight, to: '/warden/approval-queue' },
                        ].map((tile) => (
                            <div key={tile.label} style={{ flex: 1, background: C.card, borderRadius: 20, padding: '16px 18px', border: `1px solid ${C.border}`, cursor: 'pointer' }} onClick={() => navigate(tile.to)}>
                                <div style={{ width: 36, height: 36, borderRadius: 12, background: tile.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                                    <span className="material-symbols-outlined" style={{ fontSize: 18, color: tile.color }}>{tile.icon}</span>
                                </div>
                                <p style={{ fontSize: 28, fontWeight: 800, color: tile.color, margin: '0 0 2px', lineHeight: 1 }}>{tile.value}</p>
                                <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>{tile.label}</p>
                            </div>
                        ))}
                    </div>

                    {/* Performance */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, border: `1px solid ${C.border}`, marginBottom: 14 }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>Performance · 30 Days</p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                            {performanceMetrics.map((m) => (
                                <div key={m.label} style={{ background: C.bgElevated, borderRadius: 12, padding: '12px 14px' }}>
                                    <p style={{ fontSize: 10, fontWeight: 700, color: C.textMuted, margin: '0 0 6px', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{m.label}</p>
                                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                                        <p style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: 0 }}>{m.value}</p>
                                        <span style={{ fontSize: 11, fontWeight: 600, color: C.success }}>{m.trend}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
                            {[
                                { label: 'Mess Participation', value: analytics ? `${analytics.mess_participation_rate.toFixed(0)}%` : '62%', color: C.success },
                                { label: 'Laundry No-show', value: analytics ? `${analytics.laundry_noshow_rate.toFixed(0)}%` : '7%', color: C.warning },
                            ].map((row) => (
                                <div key={row.label} style={{ background: C.bgElevated, borderRadius: 12, padding: '10px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                    <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: 0 }}>{row.label}</p>
                                    <p style={{ fontSize: 16, fontWeight: 800, color: row.color, margin: 0 }}>{row.value}</p>
                                </div>
                            ))}
                        </div>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.08em', textTransform: 'uppercase', margin: '0 0 10px' }}>Override Rate by Category</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {overrideCategories.map(([cat, rate]) => {
                                const pct = Math.round(rate * 100);
                                return (
                                    <div key={cat}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                            <span style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary }}>{cat}</span>
                                            <span style={{ fontSize: 12, fontWeight: 700, color: C.primary }}>{pct}%</span>
                                        </div>
                                        <div style={{ height: 6, background: C.primaryLight, borderRadius: 3, overflow: 'hidden' }}>
                                            <div style={{ height: '100%', width: `${pct}%`, background: C.primary, borderRadius: 3 }} />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Notices */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, border: `1px solid ${C.border}`, marginBottom: 14 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: 0 }}>Notices</p>
                            <button onClick={() => setShowNoticeForm((v) => !v)} style={{ display: 'flex', alignItems: 'center', gap: 4, background: C.primary, color: '#fff', border: 'none', borderRadius: 999, padding: '6px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 14 }}>add</span>
                                Post Notice
                            </button>
                        </div>
                        {showNoticeForm && (
                            <div style={{ background: C.bgElevated, borderRadius: 12, padding: 14, marginBottom: 14 }}>
                                <input value={noticeTitle} onChange={(e) => setNoticeTitle(e.target.value)} placeholder="Notice title" style={{ width: '100%', background: C.bgSurface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 12px', fontSize: 14, fontFamily: 'inherit', marginBottom: 8, boxSizing: 'border-box' as const, outline: 'none', color: C.textPrimary }} />
                                <textarea value={noticeBody} onChange={(e) => setNoticeBody(e.target.value)} placeholder="Notice body" rows={3} style={{ width: '100%', background: C.bgSurface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 12px', fontSize: 14, fontFamily: 'inherit', resize: 'none' as const, outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary }} />
                                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                    <button onClick={() => setShowNoticeForm(false)} style={{ flex: 1, height: 38, background: C.bgHover, border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', color: C.textSecondary }}>Cancel</button>
                                    <button onClick={() => postMut.mutate()} disabled={!noticeTitle.trim() || !noticeBody.trim() || postMut.isPending} style={{ flex: 1, height: 38, background: C.primary, color: '#fff', border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: postMut.isPending ? 0.6 : 1 }}>
                                        {postMut.isPending ? '…' : 'Post'}
                                    </button>
                                </div>
                            </div>
                        )}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {notices.length === 0 && <p style={{ fontSize: 13, color: C.textMuted, textAlign: 'center', margin: '8px 0' }}>No notices posted yet.</p>}
                            {notices.map((n) => (
                                <div key={n.id} style={{ background: C.bgElevated, borderRadius: 12, padding: '12px 14px', display: 'flex', gap: 10 }}>
                                    <div style={{ flex: 1 }}>
                                        <p style={{ fontSize: 13, fontWeight: 700, color: C.textPrimary, margin: '0 0 4px' }}>{n.title}</p>
                                        <p style={{ fontSize: 12, color: C.textSecondary, margin: 0, lineHeight: 1.5 }}>{n.body}</p>
                                    </div>
                                    <button onClick={() => deleteMut.mutate(n.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: C.textMuted, flexShrink: 0, alignSelf: 'flex-start' }}>
                                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>delete</span>
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Quick Access */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, border: `1px solid ${C.border}` }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>Quick Access</p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                            {[
                                { label: 'Approval Queue', icon: 'approval',          to: '/warden/approval-queue', color: C.primary },
                                { label: 'Registrations',  icon: 'people',            to: '/warden/registrations',  color: C.success },
                                { label: 'Complaints',     icon: 'chat_bubble',       to: '/warden/complaints',     color: C.warning },
                                { label: 'Create Staff',   icon: 'person_add',        to: '/warden/staff/new',      color: C.info },
                                { label: 'Settings',       icon: 'settings',          to: '/warden/settings',       color: C.textSecondary },
                            ].map((item) => (
                                <button key={item.to} onClick={() => navigate(item.to)} style={{ background: C.bgElevated, borderRadius: 14, padding: '16px 14px', border: 'none', cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <span className="material-symbols-outlined" style={{ fontSize: 20, color: item.color }}>{item.icon}</span>
                                    <span style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary }}>{item.label}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
