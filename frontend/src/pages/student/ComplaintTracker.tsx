/**
 * pages/student/ComplaintTracker.tsx — Sprint F
 * Lists student's complaints with summary pills, filter, and FAB to file new.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getMyComplaints } from '../../api/complaintsApi';
import type { ComplaintStatus, ComplaintRead } from '../../types/complaint';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    primaryLight: 'rgba(70,71,211,0.10)',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    danger: '#E83B2A',
    dangerLight: 'rgba(232,59,42,0.08)',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.10)',
    amber: '#D48C00',
    amberLight: 'rgba(255,184,0,0.10)',
    border: 'rgba(0,0,0,0.06)',
};

const STATUS_META: Record<ComplaintStatus, { label: string; bg: string; text: string }> = {
    INTAKE:            { label: 'Intake',     bg: C.primaryLight, text: C.primary },
    CLASSIFIED:        { label: 'Classified', bg: C.primaryLight, text: C.primary },
    AWAITING_APPROVAL: { label: 'Pending',    bg: C.amberLight,   text: C.amber },
    ASSIGNED:          { label: 'Assigned',   bg: C.primaryLight, text: C.primary },
    IN_PROGRESS:       { label: 'In Progress',bg: C.primaryLight, text: C.primary },
    RESOLVED:          { label: 'Resolved',   bg: C.successLight, text: C.success },
    REOPENED:          { label: 'Reopened',   bg: C.amberLight,   text: C.amber },
    ESCALATED:         { label: 'Escalated',  bg: C.dangerLight,  text: C.danger },
};

const ACTIVE_STATUSES: ComplaintStatus[] = ['INTAKE', 'CLASSIFIED', 'AWAITING_APPROVAL', 'ASSIGNED', 'IN_PROGRESS', 'REOPENED', 'ESCALATED'];

type Filter = 'all' | 'active' | 'resolved';

function relativeTime(iso: string) {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

function filterComplaints(list: ComplaintRead[], filter: Filter) {
    if (filter === 'active') return list.filter((c) => ACTIVE_STATUSES.includes(c.status));
    if (filter === 'resolved') return list.filter((c) => c.status === 'RESOLVED');
    return list;
}

export default function ComplaintTracker() {
    const navigate = useNavigate();
    const [filter, setFilter] = useState<Filter>('all');

    const { data: complaints = [], isLoading } = useQuery({
        queryKey: ['my-complaints'],
        queryFn: getMyComplaints,
    });

    const active = complaints.filter((c) => ACTIVE_STATUSES.includes(c.status)).length;
    const resolved = complaints.filter((c) => c.status === 'RESOLVED').length;
    const visible = filterComplaints(complaints, filter);

    const pills: { key: Filter; label: string; count: number; bg: string; text: string }[] = [
        { key: 'all',      label: 'Total',   count: complaints.length, bg: '#F0EDE8', text: C.textPrimary },
        { key: 'active',   label: 'Active',  count: active,   bg: C.primaryLight, text: C.primary },
        { key: 'resolved', label: 'Resolved',count: resolved, bg: C.successLight, text: C.success },
    ];

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh', position: 'relative' }}>
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
                    <h1 style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: 0 }}>
                        My Complaints
                    </h1>
                    <button
                        style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textSecondary }}>filter_list</span>
                    </button>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* Summary pills */}
                    <div style={{ display: 'flex', gap: 8, marginBottom: 24, overflowX: 'auto', scrollbarWidth: 'none' } as React.CSSProperties}>
                        {pills.map((p) => (
                            <button
                                key={p.key}
                                onClick={() => setFilter(p.key)}
                                style={{
                                    flexShrink: 0,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6,
                                    background: filter === p.key ? p.bg : C.card,
                                    border: filter === p.key ? `1.5px solid ${p.text}20` : `1.5px solid ${C.border}`,
                                    borderRadius: 999,
                                    padding: '8px 16px',
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                    transition: 'all 0.15s',
                                }}
                            >
                                <span style={{ fontSize: 15, fontWeight: 700, color: p.text }}>{p.count}</span>
                                <span style={{ fontSize: 12, fontWeight: 600, color: filter === p.key ? p.text : C.textSecondary }}>{p.label}</span>
                            </button>
                        ))}
                    </div>

                    {/* Complaints list */}
                    {isLoading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {[1, 2, 3].map((i) => (
                                <div key={i} style={{ background: C.card, borderRadius: 16, height: 100, animation: 'pulse 1.5s ease infinite' }} />
                            ))}
                        </div>
                    ) : visible.length === 0 ? (
                        <div
                            style={{
                                background: C.card,
                                borderRadius: 16,
                                padding: '40px 20px',
                                textAlign: 'center',
                                boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 40, color: C.textMuted, display: 'block', marginBottom: 12 }}>
                                chat_bubble_outline
                            </span>
                            <p style={{ fontSize: 14, color: C.textSecondary, margin: 0 }}>
                                {filter === 'all' ? 'No complaints filed yet.' : `No ${filter} complaints.`}
                            </p>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                            {visible.map((c) => {
                                const s = STATUS_META[c.status] ?? STATUS_META.INTAKE;
                                return (
                                    <Link key={c.id} to={`/student/complaints/${c.id}`} style={{ textDecoration: 'none' }}>
                                        <div
                                            style={{
                                                background: C.card,
                                                borderRadius: 16,
                                                overflow: 'hidden',
                                                boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
                                            }}
                                        >
                                            <div style={{ padding: '14px 16px' }}>
                                                {/* Badges row */}
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                                                    {c.category && (
                                                        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: C.textMuted, background: '#F0EDE8', padding: '2px 8px', borderRadius: 999 }}>
                                                            {c.category}
                                                        </span>
                                                    )}
                                                    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: s.text, background: s.bg, padding: '2px 8px', borderRadius: 999 }}>
                                                        {s.label}
                                                    </span>
                                                    <span style={{ marginLeft: 'auto', fontSize: 11, color: C.textMuted }}>
                                                        {relativeTime(c.created_at)}
                                                    </span>
                                                </div>
                                                {/* Body */}
                                                <p
                                                    style={{
                                                        fontSize: 13,
                                                        color: C.textPrimary,
                                                        margin: 0,
                                                        lineHeight: 1.5,
                                                        overflow: 'hidden',
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: 2,
                                                        WebkitBoxOrient: 'vertical',
                                                    } as React.CSSProperties}
                                                >
                                                    {c.text}
                                                </p>
                                            </div>
                                            {/* Footer bar */}
                                            <div
                                                style={{
                                                    borderTop: `1px solid ${C.border}`,
                                                    padding: '9px 16px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: 6,
                                                }}
                                            >
                                                <span className="material-symbols-outlined" style={{ fontSize: 14, color: C.textMuted }}>
                                                    {c.assigned_to ? 'person' : 'pending'}
                                                </span>
                                                <span style={{ fontSize: 11, color: C.textMuted }}>
                                                    {c.assigned_to ? `Assigned to ${c.assigned_to}` : 'Awaiting assignment'}
                                                </span>
                                                <span className="material-symbols-outlined" style={{ fontSize: 16, color: C.textMuted, marginLeft: 'auto' }}>
                                                    chevron_right
                                                </span>
                                            </div>
                                        </div>
                                    </Link>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* FAB */}
                <button
                    onClick={() => navigate('/student/complaints/new')}
                    style={{
                        position: 'fixed',
                        bottom: 80,
                        right: 20,
                        width: 56,
                        height: 56,
                        borderRadius: 16,
                        background: C.primary,
                        border: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                        boxShadow: '0 4px 20px rgba(70,71,211,0.35)',
                        zIndex: 40,
                    }}
                >
                    <span className="material-symbols-outlined" style={{ fontSize: 24, color: '#fff' }}>edit_square</span>
                </button>
            </div>
        </AppShell>
    );
}
