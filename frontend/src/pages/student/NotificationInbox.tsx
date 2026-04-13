/**
 * pages/student/NotificationInbox.tsx — Sprint F
 * Unread (colored borders) + Earlier sections, mark all read.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getNotifications, markRead, markAllRead } from '../../api/notificationsApi';
import type { NotificationRead, NotificationType } from '../../types/notification';

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
    amberLight: 'rgba(212,140,0,0.10)',
    dimCard: '#FAFAF8',
    border: 'rgba(255,255,255,0.06)',
};

const TYPE_CONFIG: Record<NotificationType, { icon: string; dot: string; border: string; iconBg: string; iconColor: string }> = {
    complaint_assigned:    { icon: 'assignment_ind',        dot: C.primary, border: C.primary, iconBg: C.primaryLight, iconColor: C.primary },
    complaint_resolved:    { icon: 'check_circle',          dot: C.success, border: C.success, iconBg: C.successLight, iconColor: C.success },
    complaint_escalated:   { icon: 'warning',               dot: C.danger,  border: C.danger,  iconBg: 'rgba(232,59,42,0.08)', iconColor: C.danger },
    complaint_reopened:    { icon: 'refresh',               dot: C.amber,   border: C.amber,   iconBg: C.amberLight, iconColor: C.amber },
    approval_needed:       { icon: 'how_to_reg',            dot: C.primary, border: C.primary, iconBg: C.primaryLight, iconColor: C.primary },
    registration_pending:  { icon: 'pending_actions',       dot: C.amber,   border: C.amber,   iconBg: C.amberLight, iconColor: C.amber },
    registration_approved: { icon: 'verified_user',         dot: C.success, border: C.success, iconBg: C.successLight, iconColor: C.success },
    registration_rejected: { icon: 'person_off',            dot: C.danger,  border: C.danger,  iconBg: 'rgba(232,59,42,0.08)', iconColor: C.danger },
    mess_alert:            { icon: 'restaurant',            dot: C.amber,   border: C.amber,   iconBg: C.amberLight, iconColor: C.amber },
    laundry_reminder:      { icon: 'local_laundry_service', dot: C.success, border: C.success, iconBg: C.successLight, iconColor: C.success },
    machine_down:          { icon: 'build',                 dot: C.danger,  border: C.danger,  iconBg: 'rgba(232,59,42,0.08)', iconColor: C.danger },
    password_reset:        { icon: 'lock_reset',            dot: C.textMuted, border: C.textMuted, iconBg: '#1C1B24', iconColor: C.textMuted },
    account_deactivated:   { icon: 'block',                 dot: C.danger,  border: C.danger,  iconBg: 'rgba(232,59,42,0.08)', iconColor: C.danger },
};

function relativeTime(iso: string) {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function NotifCard({
    n,
    unread,
    onRead,
}: {
    n: NotificationRead;
    unread: boolean;
    onRead: (id: string) => void;
}) {
    const cfg = TYPE_CONFIG[n.type] ?? TYPE_CONFIG.account_deactivated;

    return (
        <div
            onClick={() => unread && onRead(n.id)}
            style={{
                background: unread ? C.card : C.dimCard,
                borderRadius: 14,
                padding: '14px 16px',
                display: 'flex',
                gap: 14,
                alignItems: 'flex-start',
                borderLeft: unread ? `3px solid ${cfg.border}` : 'none',
                opacity: unread ? 1 : 0.80,
                cursor: unread ? 'pointer' : 'default',
                boxShadow: unread ? '0 1px 6px rgba(255,255,255,0.06)' : 'none',
            }}
        >
            {/* Icon */}
            <div
                style={{
                    width: 40,
                    height: 40,
                    borderRadius: 12,
                    background: '#1C1B24',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                }}
            >
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: cfg.iconColor, fontVariationSettings: "'FILL' 1" }}>
                    {cfg.icon}
                </span>
            </div>

            {/* Content */}
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 3 }}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: 0 }}>{n.title}</p>
                    <span style={{ fontSize: 11, color: C.textMuted, whiteSpace: 'nowrap', marginLeft: 8 }}>
                        {relativeTime(n.created_at)}
                    </span>
                </div>
                <p style={{ fontSize: 12, color: C.textSecondary, margin: 0, lineHeight: 1.5 }}>{n.body}</p>
            </div>

            {/* Unread dot */}
            {unread && (
                <div
                    style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: cfg.dot,
                        flexShrink: 0,
                        marginTop: 4,
                    }}
                />
            )}
        </div>
    );
}

export default function NotificationInbox() {
    const qc = useQueryClient();

    const { data: notifications = [], isLoading } = useQuery({
        queryKey: ['notifications'],
        queryFn: getNotifications,
    });

    const readMutation = useMutation({
        mutationFn: markRead,
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
    });

    const readAllMutation = useMutation({
        mutationFn: markAllRead,
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
    });

    const unread = notifications.filter((n) => !n.is_read);
    const earlier = notifications.filter((n) => n.is_read);
    const hasUnread = unread.length > 0;

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Header */}
                <header
                    style={{
                        position: 'sticky',
                        top: 0,
                        zIndex: 20,
                        background: C.bg,
                        padding: '52px 20px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                    }}
                >
                    <h1 style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: 0 }}>Notifications</h1>
                    {hasUnread && (
                        <button
                            onClick={() => readAllMutation.mutate()}
                            disabled={readAllMutation.isPending}
                            style={{
                                background: 'none',
                                border: 'none',
                                fontSize: 13,
                                fontWeight: 600,
                                color: C.primary,
                                cursor: 'pointer',
                                fontFamily: 'inherit',
                                opacity: readAllMutation.isPending ? 0.6 : 1,
                            }}
                        >
                            Mark all read
                        </button>
                    )}
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {isLoading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {[1, 2, 3].map((i) => (
                                <div key={i} style={{ background: C.card, borderRadius: 14, height: 80 }} />
                            ))}
                        </div>
                    ) : notifications.length === 0 ? (
                        <div style={{ background: C.card, borderRadius: 16, padding: '48px 20px', textAlign: 'center', boxShadow: '0 1px 6px rgba(255,255,255,0.03)' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 40, color: C.textMuted, display: 'block', marginBottom: 12 }}>notifications_none</span>
                            <p style={{ fontSize: 14, color: C.textSecondary, margin: 0 }}>All quiet — no notifications yet.</p>
                        </div>
                    ) : (
                        <>
                            {/* Unread section */}
                            {unread.length > 0 && (
                                <section style={{ marginBottom: 24 }}>
                                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 10px' }}>
                                        Unread · {unread.length}
                                    </p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {unread.map((n) => (
                                            <NotifCard
                                                key={n.id}
                                                n={n}
                                                unread
                                                onRead={(id) => readMutation.mutate(id)}
                                            />
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Earlier section */}
                            {earlier.length > 0 && (
                                <section>
                                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 10px' }}>
                                        Earlier
                                    </p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                        {earlier.map((n) => (
                                            <NotifCard key={n.id} n={n} unread={false} onRead={() => {}} />
                                        ))}
                                    </div>
                                </section>
                            )}
                        </>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
