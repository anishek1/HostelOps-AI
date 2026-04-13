/**
 * pages/student/ComplaintDetail.tsx — Sprint F
 * Shows complaint metadata, AI category, status timeline, and student actions.
 */

import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getComplaint, getComplaintTimeline, confirmResolved, reopenComplaint } from '../../api/complaintsApi';
import type { ComplaintStatus } from '../../types/complaint';

const C = {
    bg: '#0A0A0F',
    primary: '#7C5CFC',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#F0F0F5',
    textSecondary: '#6B6B80',
    textMuted: '#6B6B80',
    card: '#13121A',
    danger: '#E83B2A',
    dangerLight: 'rgba(232,59,42,0.08)',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.10)',
    amber: '#D48C00',
    amberLight: 'rgba(255,184,0,0.10)',
    border: 'rgba(255,255,255,0.06)',
};

const STATUS_META: Record<ComplaintStatus, { label: string; bg: string; text: string; dot: string }> = {
    INTAKE:            { label: 'Intake',     bg: C.primaryLight, text: C.primary, dot: C.primary },
    CLASSIFIED:        { label: 'Classified', bg: C.primaryLight, text: C.primary, dot: C.primary },
    AWAITING_APPROVAL: { label: 'Pending Approval', bg: C.amberLight, text: C.amber, dot: C.amber },
    ASSIGNED:          { label: 'Assigned',   bg: C.primaryLight, text: C.primary, dot: C.primary },
    IN_PROGRESS:       { label: 'In Progress',bg: C.primaryLight, text: C.primary, dot: C.primary },
    RESOLVED:          { label: 'Resolved',   bg: C.successLight, text: C.success, dot: C.success },
    REOPENED:          { label: 'Reopened',   bg: C.amberLight,   text: C.amber,   dot: C.amber },
    ESCALATED:         { label: 'Escalated',  bg: C.dangerLight,  text: C.danger,  dot: C.danger },
};

const STATUS_ORDER: ComplaintStatus[] = [
    'INTAKE', 'CLASSIFIED', 'AWAITING_APPROVAL', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED',
];

function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function ComplaintDetail() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const qc = useQueryClient();
    const [actionLoading, setActionLoading] = useState<'confirm' | 'reopen' | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);

    const { data: complaint, isLoading } = useQuery({
        queryKey: ['complaint', id],
        queryFn: () => getComplaint(id!),
        enabled: !!id,
    });

    const { data: timeline = [] } = useQuery({
        queryKey: ['complaint-timeline', id],
        queryFn: () => getComplaintTimeline(id!),
        enabled: !!id,
    });

    async function handleConfirm() {
        if (!id) return;
        setActionError(null);
        setActionLoading('confirm');
        try {
            await confirmResolved(id);
            await qc.invalidateQueries({ queryKey: ['complaint', id] });
            await qc.invalidateQueries({ queryKey: ['my-complaints'] });
            navigate(`/student/complaints/${id}/resolved`);
        } catch {
            setActionError('Could not confirm. Please try again.');
        } finally {
            setActionLoading(null);
        }
    }

    async function handleReopen() {
        if (!id) return;
        setActionError(null);
        setActionLoading('reopen');
        try {
            await reopenComplaint(id);
            await qc.invalidateQueries({ queryKey: ['complaint', id] });
            await qc.invalidateQueries({ queryKey: ['my-complaints'] });
        } catch {
            setActionError('Could not reopen. Please try again.');
        } finally {
            setActionLoading(null);
        }
    }

    if (isLoading || !complaint) {
        return (
            <AppShell>
                <div style={{ background: C.bg, minHeight: '100dvh', padding: '80px 20px 20px' }}>
                    <div style={{ background: C.card, borderRadius: 16, height: 180, marginBottom: 12 }} />
                    <div style={{ background: C.card, borderRadius: 16, height: 220 }} />
                </div>
            </AppShell>
        );
    }

    const s = STATUS_META[complaint.status] ?? STATUS_META.INTAKE;
    const currentIndex = STATUS_ORDER.indexOf(complaint.status);
    const showActionZone = complaint.status === 'RESOLVED' || complaint.status === 'IN_PROGRESS';

    return (
        <AppShell hasStickyCta={showActionZone}>
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
                        Complaint Details
                    </h1>
                </header>

                <div style={{ padding: '0 20px 20px' }}>
                    {/* Header card */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 20,
                            padding: 20,
                            boxShadow: '0 2px 12px rgba(255,255,255,0.06)',
                            marginBottom: 14,
                        }}
                    >
                        {/* Badges */}
                        <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
                            {complaint.category && (
                                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: C.textMuted, background: '#1C1B24', padding: '3px 10px', borderRadius: 999 }}>
                                    {complaint.category}
                                </span>
                            )}
                            <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: s.text, background: s.bg, padding: '3px 10px', borderRadius: 999 }}>
                                {s.label}
                            </span>
                        </div>

                        {/* Complaint text */}
                        <p style={{ fontSize: 14, color: C.textPrimary, lineHeight: 1.6, margin: '0 0 18px' }}>
                            {complaint.text}
                        </p>

                        {/* 2×2 metadata grid */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            {[
                                { label: 'Severity', value: complaint.severity ? complaint.severity.charAt(0).toUpperCase() + complaint.severity.slice(1) : 'Pending', icon: 'priority_high' },
                                { label: 'Filed On', value: formatDate(complaint.created_at), icon: 'calendar_today' },
                                { label: 'Assigned To', value: complaint.assigned_to ?? 'Unassigned', icon: 'person' },
                                { label: 'Anonymous', value: complaint.is_anonymous ? 'Yes' : 'No', icon: 'visibility_off' },
                            ].map((m) => (
                                <div key={m.label} style={{ background: '#F6ECE5', borderRadius: 12, padding: '10px 12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 4 }}>
                                        <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>{m.icon}</span>
                                        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: C.textMuted }}>{m.label}</span>
                                    </div>
                                    <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: 0 }}>{m.value}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Status timeline */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 20,
                            padding: 20,
                            boxShadow: '0 2px 12px rgba(255,255,255,0.06)',
                            marginBottom: 14,
                        }}
                    >
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 18px' }}>
                            Status Timeline
                        </p>

                        {timeline.length > 0 ? (
                            <div style={{ position: 'relative', paddingLeft: 24 }}>
                                {/* Vertical line */}
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 7,
                                        top: 8,
                                        bottom: 8,
                                        width: 2,
                                        background: 'linear-gradient(to bottom, ' + C.primary + ', ' + C.primaryLight + ')',
                                        borderRadius: 2,
                                    }}
                                />
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                    {timeline.map((entry, i) => {
                                        const isLast = i === timeline.length - 1;
                                        const statusMeta = STATUS_META[entry.status as ComplaintStatus] ?? STATUS_META.INTAKE;
                                        return (
                                            <div key={i} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                                                {/* Dot */}
                                                <div
                                                    style={{
                                                        position: 'absolute',
                                                        left: 0,
                                                        width: 16,
                                                        height: 16,
                                                        borderRadius: '50%',
                                                        background: isLast ? statusMeta.dot : C.primaryLight,
                                                        border: `2px solid ${statusMeta.dot}`,
                                                        marginTop: 2,
                                                        flexShrink: 0,
                                                    }}
                                                />
                                                <div>
                                                    <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: '0 0 2px' }}>
                                                        {statusMeta.label}
                                                    </p>
                                                    <p style={{ fontSize: 11, color: C.textMuted, margin: 0 }}>
                                                        {new Date(entry.changed_at).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                                                        {entry.note ? ` · ${entry.note}` : ''}
                                                    </p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            /* Fallback: show status pipeline */
                            <div style={{ position: 'relative', paddingLeft: 24 }}>
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: 7,
                                        top: 8,
                                        bottom: 8,
                                        width: 2,
                                        background: C.primaryLight,
                                        borderRadius: 2,
                                    }}
                                />
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                                    {STATUS_ORDER.map((st, i) => {
                                        const meta = STATUS_META[st];
                                        const done = i <= currentIndex;
                                        const isCurrent = i === currentIndex;
                                        return (
                                            <div key={st} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                                                <div
                                                    style={{
                                                        position: 'absolute',
                                                        left: 0,
                                                        width: 16,
                                                        height: 16,
                                                        borderRadius: '50%',
                                                        background: done ? meta.dot : 'transparent',
                                                        border: `2px solid ${done ? meta.dot : '#D1D5DB'}`,
                                                        marginTop: 2,
                                                    }}
                                                />
                                                <p
                                                    style={{
                                                        fontSize: 13,
                                                        fontWeight: isCurrent ? 700 : 500,
                                                        color: done ? C.textPrimary : C.textMuted,
                                                        margin: 0,
                                                    }}
                                                >
                                                    {meta.label}
                                                </p>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}
                    </div>

                    {actionError && (
                        <p style={{ fontSize: 13, color: C.danger, fontWeight: 500, margin: '0 0 12px' }}>{actionError}</p>
                    )}
                </div>
            </div>

            {/* Sticky action zone */}
            {showActionZone && (
                <div
                    style={{
                        position: 'fixed',
                        bottom: 64,
                        left: '50%',
                        transform: 'translateX(-50%)',
                        width: '100%',
                        maxWidth: 430,
                        padding: '12px 20px',
                        background: 'linear-gradient(to top, #0A0A0F 70%, transparent)',
                        zIndex: 30,
                    }}
                >
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 16,
                            padding: '14px 16px',
                            boxShadow: '0 4px 20px rgba(255,255,255,0.06)',
                        }}
                    >
                        <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: '0 0 12px', textAlign: 'center' }}>
                            Was your issue resolved?
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                            <button
                                onClick={handleReopen}
                                disabled={!!actionLoading}
                                style={{
                                    height: 44,
                                    background: C.dangerLight,
                                    color: C.danger,
                                    border: 'none',
                                    borderRadius: 12,
                                    fontSize: 14,
                                    fontWeight: 600,
                                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                                    opacity: actionLoading === 'reopen' ? 0.6 : 1,
                                    fontFamily: 'inherit',
                                }}
                            >
                                {actionLoading === 'reopen' ? '…' : 'No, reopen'}
                            </button>
                            <button
                                onClick={handleConfirm}
                                disabled={!!actionLoading}
                                style={{
                                    height: 44,
                                    background: C.success,
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 12,
                                    fontSize: 14,
                                    fontWeight: 600,
                                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                                    opacity: actionLoading === 'confirm' ? 0.6 : 1,
                                    fontFamily: 'inherit',
                                    boxShadow: '0 3px 10px rgba(26,155,108,0.25)',
                                }}
                            >
                                {actionLoading === 'confirm' ? '…' : 'Yes, resolved!'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </AppShell>
    );
}
