/**
 * pages/student/NotificationInbox.tsx — Sprint F
 * Unread (colored borders) + Earlier sections, mark all read.
 */

import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getNotifications, markRead, markAllRead } from '../../api/notificationsApi';
import type { NotificationRead, NotificationType } from '../../types/notification';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    danger: '#E83B2A',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.10)',
    amber: '#D48C00',
    amberLight: 'rgba(212,140,0,0.10)',
    dimCard: '#FAFAF8',
    border: 'rgba(0,0,0,0.06)',
};

const TYPE_CONFIG: Record<NotificationType, { icon: string; dot: string; border: string; iconBg: string; iconColor: string }> = {
    complaint_update: { icon: 'chat_bubble', dot: C.primary, border: C.primary, iconBg: C.primaryLight, iconColor: C.primary },
    laundry_reminder: { icon: 'local_laundry_service', dot: C.success, border: C.success, iconBg: C.successLight, iconColor: C.success },
    mess_alert:       { icon: 'restaurant', dot: C.amber, border: C.amber, iconBg: C.amberLight, iconColor: C.amber },
    approval:         { icon: 'how_to_reg', dot: C.primary, border: C.primary, iconBg: C.primaryLight, iconColor: C.primary },
    system:           { icon: 'notifications', dot: C.textMuted, border: C.textMuted, iconBg: '#F0EDE8', iconColor: C.textMuted },
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
    const cfg = TYPE_CONFIG[n.notification_type] ?? TYPE_CONFIG.system;

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
                boxShadow: unread ? '0 1px 6px rgba(0,0,0,0.05)' : 'none',
            }}
        >
            {/* Icon circle */}
            <div
                style={{
                    width: 38,
                    height: 38,
                    borderRadius: '50%',
                    background: cfg.iconBg,
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
    const navigate = useNavigate();
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <button
                            onClick={() => navigate(-1)}
                            style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                        </button>
                        <h1 style={{ fontSize: 20, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Notifications</h1>
                    </div>
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
                        <div style={{ background: C.card, borderRadius: 16, padding: '48px 20px', textAlign: 'center', boxShadow: '0 1px 6px rgba(0,0,0,0.04)' }}>
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
