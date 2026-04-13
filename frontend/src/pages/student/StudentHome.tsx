/**
 * pages/student/StudentHome.tsx — Sprint F
 * Student dashboard: greeting, notices, quick actions, recent complaints, AI card.
 */

import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../hooks/useAuth';
import AppShell from '../../components/AppShell';
import { getMyComplaints } from '../../api/complaintsApi';
import { getNotifications } from '../../api/notificationsApi';
import { C, STATUS_COLORS, chipStyle } from '../../lib/theme';

function getGreeting() {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 17) return 'Good afternoon';
    return 'Good evening';
}

function initials(name: string) {
    return name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
}

function relativeTime(iso: string) {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
}

const QUICK_ACTIONS = [
    { label: 'Complaint', icon: 'chat_bubble', to: '/student/complaints/new', color: C.primary, bg: C.primaryContainer },
    { label: 'Laundry',   icon: 'local_laundry_service', to: '/student/laundry', color: C.accent, bg: C.accentLight },
    { label: 'Mess',      icon: 'restaurant', to: '/student/mess', color: C.warning, bg: C.warningLight },
];

export default function StudentHome() {
    const { user } = useAuth();
    const navigate = useNavigate();

    const { data: complaints = [] } = useQuery({
        queryKey: ['my-complaints'],
        queryFn: getMyComplaints,
    });

    const { data: notifications = [] } = useQuery({
        queryKey: ['notifications'],
        queryFn: getNotifications,
    });

    const recentComplaints = complaints.slice(0, 3);
    const notices = notifications.filter((n) => !n.is_read).slice(0, 2);
    const hasUnread = notifications.some((n) => !n.is_read);
    const name = user?.name ?? 'Student';

    const notifIconMap: Record<string, string> = {
        complaint_assigned:    'assignment_ind',
        complaint_resolved:    'check_circle',
        complaint_escalated:   'warning',
        complaint_reopened:    'refresh',
        approval_needed:       'how_to_reg',
        registration_pending:  'pending_actions',
        registration_approved: 'verified_user',
        registration_rejected: 'person_off',
        mess_alert:            'restaurant',
        laundry_reminder:      'local_laundry_service',
        machine_down:          'build',
        password_reset:        'lock_reset',
        account_deactivated:   'block',
    };

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Fixed Header */}
                <header
                    style={{
                        position: 'sticky',
                        top: 0,
                        zIndex: 20,
                        background: C.bg,
                        padding: '52px 20px 16px',
                        display: 'flex',
                        alignItems: 'flex-start',
                        justifyContent: 'space-between',
                    }}
                >
                    {/* Avatar + greeting */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div
                            style={{
                                width: 44,
                                height: 44,
                                borderRadius: '50%',
                                background: C.primaryContainer,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 15,
                                fontWeight: 700,
                                color: C.primary,
                                flexShrink: 0,
                            }}
                        >
                            {initials(name)}
                        </div>
                        <div>
                            <p style={{ fontSize: 12, color: C.textSecondary, margin: 0 }}>
                                {getGreeting()}
                            </p>
                            <p style={{ fontSize: 17, fontWeight: 700, color: C.textPrimary, margin: 0 }}>
                                {name.split(' ')[0]}
                            </p>
                        </div>
                    </div>

                    {/* Notification bell */}
                    <button
                        onClick={() => navigate('/student/notifications')}
                        style={{
                            position: 'relative',
                            background: C.card,
                            border: `1px solid ${C.border}`,
                            borderRadius: '50%',
                            width: 40,
                            height: 40,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                        }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 22, color: C.textSecondary }}>
                            notifications
                        </span>
                        {hasUnread && (
                            <span
                                style={{
                                    position: 'absolute',
                                    top: 7,
                                    right: 7,
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    background: C.danger,
                                    border: '2px solid ' + C.bg,
                                }}
                            />
                        )}
                    </button>
                </header>

                <div style={{ padding: '0 20px 20px' }}>

                    {/* Notices section */}
                    {notices.length > 0 && (
                        <section style={{ marginBottom: 24 }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 10px' }}>
                                Notices
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {notices.map((n) => (
                                    <div
                                        key={n.id}
                                        style={{
                                            background: C.card,
                                            borderRadius: 14,
                                            padding: '14px 16px',
                                            display: 'flex',
                                            gap: 12,
                                            alignItems: 'flex-start',
                                            border: `1px solid ${C.border}`,
                                        }}
                                    >
                                        <div
                                            style={{
                                                width: 44,
                                                height: 44,
                                                borderRadius: 14,
                                                background: C.primaryLight,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flexShrink: 0,
                                            }}
                                        >
                                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.primary }}>
                                                {notifIconMap[n.type] ?? 'notifications'}
                                            </span>
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: 0 }}>{n.title}</p>
                                                <span style={{ fontSize: 11, color: C.textMuted, whiteSpace: 'nowrap', marginLeft: 8 }}>
                                                    {relativeTime(n.created_at)}
                                                </span>
                                            </div>
                                            <p style={{ fontSize: 12, color: C.textSecondary, margin: '3px 0 0', lineHeight: 1.45 }}>
                                                {n.body}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Quick Actions */}
                    <section style={{ marginBottom: 28 }}>
                        <p style={{ fontSize: 18, fontWeight: 800, color: C.textPrimary, margin: '0 0 14px' }}>
                            What do you need?
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                            {QUICK_ACTIONS.map((a) => (
                                <Link
                                    key={a.to}
                                    to={a.to}
                                    style={{ textDecoration: 'none' }}
                                >
                                    <div
                                        style={{
                                            background: C.card,
                                            borderRadius: 24,
                                            aspectRatio: '1',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            gap: 10,
                                            border: `1px solid ${C.border}`,
                                        }}
                                    >
                                        <div
                                            style={{
                                                width: 48,
                                                height: 48,
                                                borderRadius: '50%',
                                                background: a.bg,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                            }}
                                        >
                                            <span
                                                className="material-symbols-outlined"
                                                style={{ fontSize: 24, color: a.color, fontVariationSettings: "'FILL' 1" }}
                                            >
                                                {a.icon}
                                            </span>
                                        </div>
                                        <span style={{ fontSize: 12, fontWeight: 600, color: C.textPrimary }}>
                                            {a.label}
                                        </span>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    </section>

                    {/* AI Suggestion Card */}
                    <div
                        style={{
                            background: C.primaryContainer,
                            borderRadius: 16,
                            padding: '16px 18px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 14,
                            marginBottom: 28,
                        }}
                    >
                        <div
                            style={{
                                width: 44,
                                height: 44,
                                borderRadius: '50%',
                                background: C.primaryLight,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 22, color: C.primary, fontVariationSettings: "'FILL' 1" }}>
                                auto_awesome
                            </span>
                        </div>
                        <div style={{ flex: 1 }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.primary, letterSpacing: '0.08em', textTransform: 'uppercase', margin: '0 0 3px' }}>
                                Sanctuary AI
                            </p>
                            <p style={{ fontSize: 13, color: C.textPrimary, margin: 0, lineHeight: 1.45 }}>
                                Describe any issue in plain words and our AI will classify it for you.
                            </p>
                        </div>
                        <Link to="/student/complaints/new" style={{ textDecoration: 'none' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.primary }}>
                                arrow_forward
                            </span>
                        </Link>
                    </div>

                    {/* Recent Complaints */}
                    <section>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: 0 }}>
                                Recent Complaints
                            </p>
                            <Link to="/student/complaints" style={{ fontSize: 12, fontWeight: 600, color: C.primary, textDecoration: 'none' }}>
                                View all
                            </Link>
                        </div>

                        {recentComplaints.length === 0 ? (
                            <div
                                style={{
                                    background: C.card,
                                    borderRadius: 16,
                                    padding: '32px 20px',
                                    textAlign: 'center',
                                    border: `1px solid ${C.border}`,
                                }}
                            >
                                <span className="material-symbols-outlined" style={{ fontSize: 36, color: C.textMuted, display: 'block', marginBottom: 10 }}>
                                    chat_bubble_outline
                                </span>
                                <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>
                                    No complaints yet. File one if something's off.
                                </p>
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {recentComplaints.map((c) => {
                                    const s = STATUS_COLORS[c.status] ?? STATUS_COLORS.INTAKE;
                                    return (
                                        <Link key={c.id} to={`/student/complaints/${c.id}`} style={{ textDecoration: 'none' }}>
                                            <div
                                                style={{
                                                    background: C.card,
                                                    borderRadius: 14,
                                                    padding: '14px 16px',
                                                    border: `1px solid ${C.border}`,
                                                }}
                                            >
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                                    {c.category && (
                                                        <span
                                                            style={{
                                                                ...chipStyle(C.bgElevated, C.textMuted),
                                                            }}
                                                        >
                                                            {c.category}
                                                        </span>
                                                    )}
                                                    <span
                                                        style={{
                                                            ...chipStyle(s.bg, s.text),
                                                        }}
                                                    >
                                                        {s.label}
                                                    </span>
                                                    <span style={{ marginLeft: 'auto', fontSize: 11, color: C.textMuted }}>
                                                        {relativeTime(c.created_at)}
                                                    </span>
                                                </div>
                                                <p
                                                    style={{
                                                        fontSize: 13,
                                                        color: C.textPrimary,
                                                        margin: 0,
                                                        lineHeight: 1.45,
                                                        overflow: 'hidden',
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: 2,
                                                        WebkitBoxOrient: 'vertical',
                                                    } as React.CSSProperties}
                                                >
                                                    {c.text}
                                                </p>
                                            </div>
                                        </Link>
                                    );
                                })}
                            </div>
                        )}
                    </section>
                </div>
            </div>
        </AppShell>
    );
}
