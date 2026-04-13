/**
 * pages/warden/StudentRegistrations.tsx — Sprint F
 * Pending and reviewed student registrations with approve/reject actions.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import {
    getPendingRegistrations,
    getAllRegistrations,
    approveRegistration,
    rejectRegistration,
    type PendingRegistration,
} from '../../api/wardenApi';

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
};

function initials(name: string | undefined) {
    if (!name) return '?';
    return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

function timeAgo(iso: string) {
    const h = Math.floor((Date.now() - new Date(iso).getTime()) / 3600000);
    if (h < 1) return 'Just now';
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
}

function RegCard({ reg, onApprove, onReject, loading }: {
    reg: PendingRegistration;
    onApprove: (id: string) => void;
    onReject: (id: string, reason: string) => void;
    loading: string | null;
}) {
    const [rejectMode, setRejectMode] = useState(false);
    const [reason, setReason] = useState('');

    return (
        <div style={{ background: C.card, borderRadius: 20, padding: 18, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 14 }}>
                <div style={{ width: 46, height: 46, borderRadius: '50%', background: C.primaryLight, color: C.primary, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 15, fontWeight: 700, flexShrink: 0 }}>
                    {initials(reg.name)}
                </div>
                <div style={{ flex: 1 }}>
                    <p style={{ fontSize: 15, fontWeight: 700, color: C.textPrimary, margin: '0 0 2px' }}>{reg.name}</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: 12, color: C.textMuted }}>Room {reg.room_number}</span>
                        <span style={{ fontSize: 11, color: C.textMuted }}>·</span>
                        <span style={{ fontSize: 12, color: C.textMuted }}>{timeAgo(reg.created_at)}</span>
                    </div>
                </div>
                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: reg.hostel_mode === 'college' ? C.primary : C.success, background: reg.hostel_mode === 'college' ? C.primaryLight : C.successLight, padding: '3px 10px', borderRadius: 999, flexShrink: 0 }}>
                    {reg.hostel_mode}
                </span>
            </div>

            {reg.roll_number && (
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#F6ECE5', borderRadius: 999, padding: '4px 12px', marginBottom: 12 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>badge</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary }}>{reg.roll_number}</span>
                </div>
            )}

            {reg.erp_document_url && (
                <a href={reg.erp_document_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12, color: C.primary, fontWeight: 600, textDecoration: 'none', marginLeft: 8, marginBottom: 12 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 13 }}>open_in_new</span>
                    View Document
                </a>
            )}

            {rejectMode && (
                <div style={{ background: '#F6ECE5', borderRadius: 12, padding: 12, marginBottom: 12 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: C.textPrimary, margin: '0 0 8px' }}>Rejection Reason</p>
                    <textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Explain why this registration is being rejected…" rows={3} style={{ width: '100%', background: '#fff', border: 'none', borderRadius: 8, padding: '8px 10px', fontSize: 13, fontFamily: 'inherit', resize: 'none', outline: 'none', boxSizing: 'border-box' as const }} />
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button onClick={() => { setRejectMode(false); setReason(''); }} style={{ flex: 1, height: 36, background: '#E0D7CF', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', color: C.textSecondary }}>Cancel</button>
                        <button onClick={() => onReject(reg.id, reason)} disabled={!reason.trim() || !!loading} style={{ flex: 1, height: 36, background: C.danger, color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: !reason.trim() ? 0.5 : 1 }}>
                            {loading === reg.id + '-reject' ? '…' : 'Reject'}
                        </button>
                    </div>
                </div>
            )}

            {reg.status === 'approved' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: C.success }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>check_circle</span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>Approved</span>
                </div>
            )}

            {reg.status === 'rejected' && (
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: C.danger }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>cancel</span>
                        <span style={{ fontSize: 13, fontWeight: 600 }}>Rejected</span>
                    </div>
                    {reg.rejection_reason && <p style={{ fontSize: 12, color: C.textMuted, margin: '4px 0 0', paddingLeft: 22 }}>{reg.rejection_reason}</p>}
                </div>
            )}

            {reg.status === 'pending' && !rejectMode && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                    <button onClick={() => setRejectMode(true)} disabled={!!loading} style={{ height: 42, background: C.dangerLight, color: C.danger, border: 'none', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>Reject</button>
                    <button onClick={() => onApprove(reg.id)} disabled={!!loading} style={{ height: 42, background: C.success, color: '#fff', border: 'none', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: loading === reg.id + '-approve' ? 0.6 : 1, boxShadow: '0 3px 10px rgba(26,155,108,0.25)' }}>
                        {loading === reg.id + '-approve' ? '…' : 'Approve'}
                    </button>
                </div>
            )}
        </div>
    );
}

export default function StudentRegistrations() {
    const navigate = useNavigate();
    const qc = useQueryClient();
    const [tab, setTab] = useState<'pending' | 'reviewed'>('pending');
    const [loading, setLoading] = useState<string | null>(null);

    const { data: pending = [], isLoading: pendingLoading } = useQuery({ queryKey: ['pending-registrations'], queryFn: getPendingRegistrations });
    const { data: all = [], isLoading: allLoading } = useQuery({ queryKey: ['all-registrations'], queryFn: getAllRegistrations, enabled: tab === 'reviewed' });

    const displayed = tab === 'pending'
        ? pending.filter((r) => r.status === 'pending')
        : all.filter((r) => r.status !== 'pending');
    const isLoading = tab === 'pending' ? pendingLoading : allLoading;

    async function handleApprove(id: string) {
        setLoading(id + '-approve');
        try {
            await approveRegistration(id);
            qc.invalidateQueries({ queryKey: ['pending-registrations'] });
            qc.invalidateQueries({ queryKey: ['all-registrations'] });
        } finally { setLoading(null); }
    }

    async function handleReject(id: string, reason: string) {
        setLoading(id + '-reject');
        try {
            await rejectRegistration(id, reason);
            qc.invalidateQueries({ queryKey: ['pending-registrations'] });
            qc.invalidateQueries({ queryKey: ['all-registrations'] });
        } finally { setLoading(null); }
    }

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                        <button onClick={() => navigate('/warden')} style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                        </button>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Registrations</h1>
                            {pending.length > 0 && <span style={{ fontSize: 11, fontWeight: 700, color: '#fff', background: C.amber, padding: '2px 8px', borderRadius: 999 }}>{pending.length}</span>}
                        </div>
                    </div>
                    <div style={{ display: 'flex', background: '#1C1B24', borderRadius: 12, padding: 4 }}>
                        {(['pending', 'reviewed'] as const).map((t) => (
                            <button key={t} onClick={() => setTab(t)} style={{ flex: 1, height: 36, background: tab === t ? C.card : 'transparent', border: 'none', borderRadius: 9, fontSize: 13, fontWeight: 600, color: tab === t ? C.textPrimary : C.textMuted, cursor: 'pointer', fontFamily: 'inherit', boxShadow: tab === t ? '0 1px 4px rgba(255,255,255,0.06)' : 'none' }}>
                                {t === 'pending' ? 'Pending' : 'Reviewed'}
                            </button>
                        ))}
                    </div>
                    <p style={{ fontSize: 12, color: C.textMuted, margin: '10px 0 0', paddingBottom: 12 }}>
                        {tab === 'pending' ? 'Students awaiting approval.' : 'Previously reviewed registrations.'}
                    </p>
                </header>

                <div style={{ padding: '12px 20px 100px' }}>
                    {isLoading && <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{[1, 2].map((i) => <div key={i} style={{ background: C.card, borderRadius: 20, height: 160 }} />)}</div>}

                    {!isLoading && displayed.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 48, color: C.textMuted, display: 'block', marginBottom: 12 }}>people</span>
                            <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: 0 }}>
                                {tab === 'pending' ? 'No pending registrations' : 'No reviewed registrations'}
                            </p>
                        </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {displayed.map((reg) => (
                            <RegCard key={reg.id} reg={reg} onApprove={handleApprove} onReject={handleReject} loading={loading} />
                        ))}
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
