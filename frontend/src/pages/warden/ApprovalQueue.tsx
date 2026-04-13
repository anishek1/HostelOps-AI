/**
 * pages/warden/ApprovalQueue.tsx — Sprint F
 * Complaints awaiting AWAITING_APPROVAL status — warden review.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { C, SEVERITY_COLORS, chipStyle } from '../../lib/theme';
import { getWardenComplaints, updateComplaintStatus, escalateComplaint } from '../../api/wardenApi';

export default function ApprovalQueue() {
    const navigate = useNavigate();
    const qc = useQueryClient();
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [escalateId, setEscalateId] = useState<string | null>(null);
    const [escalateReason, setEscalateReason] = useState('');
    const [loading, setLoading] = useState<string | null>(null);

    const { data: complaints = [], isLoading } = useQuery({
        queryKey: ['warden-complaints-approval'],
        queryFn: () => getWardenComplaints({ status: 'AWAITING_APPROVAL' }),
    });

    async function handleApprove(id: string) {
        setLoading(id + '-approve');
        try {
            await updateComplaintStatus(id, 'ASSIGNED');
            qc.invalidateQueries({ queryKey: ['warden-complaints-approval'] });
            qc.invalidateQueries({ queryKey: ['warden-analytics'] });
        } finally { setLoading(null); }
    }

    async function handleEscalate(id: string) {
        if (!escalateReason.trim()) return;
        setLoading(id + '-escalate');
        try {
            await escalateComplaint(id, escalateReason);
            qc.invalidateQueries({ queryKey: ['warden-complaints-approval'] });
            setEscalateId(null);
            setEscalateReason('');
        } finally { setLoading(null); }
    }

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button onClick={() => navigate('/warden')} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                    </button>
                    <div>
                        <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Approval Queue</h1>
                        {!isLoading && <p style={{ fontSize: 12, color: C.textMuted, margin: 0 }}>{complaints.length} awaiting review</p>}
                    </div>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {isLoading && <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{[1, 2, 3].map((i) => <div key={i} style={{ background: C.card, borderRadius: 20, height: 140, border: `1px solid ${C.border}` }} />)}</div>}

                    {!isLoading && complaints.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 48, color: C.textMuted, display: 'block', marginBottom: 12 }}>check_circle</span>
                            <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: '0 0 6px' }}>All caught up</p>
                            <p style={{ fontSize: 14, color: C.textMuted, margin: 0 }}>No complaints awaiting approval.</p>
                        </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {complaints.map((c) => {
                            const sev = (c.severity ?? 'low').toLowerCase();
                            const sevMeta = SEVERITY_COLORS[sev] ?? SEVERITY_COLORS.low;
                            const isExpanded = expandedId === c.id;
                            const isEscalating = escalateId === c.id;

                            return (
                                <div key={c.id} style={{ background: C.card, borderRadius: 20, padding: 18, border: `1px solid ${C.border}` }}>
                                    <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
                                        {c.category && <span style={chipStyle(C.bgElevated, C.textMuted)}>{c.category}</span>}
                                        <span style={chipStyle(sevMeta.bg, sevMeta.text)}>{sev} severity</span>
                                    </div>

                                    <p style={{ fontSize: 14, color: C.textPrimary, lineHeight: 1.55, margin: '0 0 8px' }}>
                                        {isExpanded ? c.text : (c.text.length > 120 ? c.text.slice(0, 120) + '…' : c.text)}
                                    </p>
                                    {c.text.length > 120 && (
                                        <button onClick={() => setExpandedId(isExpanded ? null : c.id)} style={{ background: 'none', border: 'none', color: C.primary, fontSize: 12, fontWeight: 600, cursor: 'pointer', padding: 0, fontFamily: 'inherit', marginBottom: 10 }}>
                                            {isExpanded ? 'Show less' : 'Read more'}
                                        </button>
                                    )}

                                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>person</span>
                                            <span style={{ fontSize: 12, color: C.textMuted }}>{c.is_anonymous ? 'Anonymous' : (c.student_id ?? 'Unknown')}</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>calendar_today</span>
                                            <span style={{ fontSize: 12, color: C.textMuted }}>{new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                                        </div>
                                    </div>

                                    {isEscalating && (
                                        <div style={{ background: C.bgElevated, borderRadius: 12, padding: 12, marginBottom: 12 }}>
                                            <p style={{ fontSize: 12, fontWeight: 700, color: C.textPrimary, margin: '0 0 8px' }}>Escalation Reason</p>
                                            <textarea value={escalateReason} onChange={(e) => setEscalateReason(e.target.value)} placeholder="Describe why this needs escalation…" rows={3} style={{ width: '100%', background: C.bgSurface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 10px', fontSize: 13, fontFamily: 'inherit', resize: 'none', outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary }} />
                                            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                                <button onClick={() => { setEscalateId(null); setEscalateReason(''); }} style={{ flex: 1, height: 36, background: C.bgHover, border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', color: C.textSecondary }}>Cancel</button>
                                                <button onClick={() => handleEscalate(c.id)} disabled={!escalateReason.trim() || !!loading} style={{ flex: 1, height: 36, background: C.danger, color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: !escalateReason.trim() ? 0.5 : 1 }}>
                                                    {loading === c.id + '-escalate' ? '…' : 'Escalate'}
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                                        <button onClick={() => setEscalateId(isEscalating ? null : c.id)} disabled={!!loading} style={{ height: 40, background: C.dangerLight, color: C.danger, border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 15 }}>warning</span>
                                            Escalate
                                        </button>
                                        <button onClick={() => handleApprove(c.id)} disabled={!!loading} style={{ height: 40, background: C.success, color: '#fff', border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, opacity: loading === c.id + '-approve' ? 0.6 : 1 }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 15 }}>check_circle</span>
                                            {loading === c.id + '-approve' ? '…' : 'Approve'}
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
