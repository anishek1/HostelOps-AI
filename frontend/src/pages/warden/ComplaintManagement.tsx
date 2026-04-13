/**
 * pages/warden/ComplaintManagement.tsx — Sprint F
 * Warden complaint list with search/filters, status update actions, analytics tab.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getWardenComplaints, updateComplaintStatus, escalateComplaint, type WardenComplaint } from '../../api/wardenApi';


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
    amberLight: 'rgba(255,184,0,0.12)',
};

const STATUS_META: Record<string, { label: string; bg: string; text: string }> = {
    INTAKE:            { label: 'Intake',          bg: C.primaryLight, text: C.primary },
    CLASSIFIED:        { label: 'Classified',      bg: C.primaryLight, text: C.primary },
    AWAITING_APPROVAL: { label: 'Awaiting',        bg: C.amberLight,   text: C.amber },
    ASSIGNED:          { label: 'Assigned',        bg: C.primaryLight, text: C.primary },
    IN_PROGRESS:       { label: 'In Progress',     bg: C.primaryLight, text: C.primary },
    RESOLVED:          { label: 'Resolved',        bg: C.successLight, text: C.success },
    REOPENED:          { label: 'Reopened',        bg: C.amberLight,   text: C.amber },
    ESCALATED:         { label: 'Escalated',       bg: C.dangerLight,  text: C.danger },
};

const SEV_META: Record<string, { bg: string; text: string }> = {
    high:   { bg: C.dangerLight,   text: C.danger },
    medium: { bg: C.amberLight,    text: C.amber },
    low:    { bg: C.successLight,  text: C.success },
};

const NEXT_STATUSES: Partial<Record<string, string[]>> = {
    INTAKE:            ['IN_PROGRESS', 'RESOLVED'],
    CLASSIFIED:        ['IN_PROGRESS', 'RESOLVED'],
    AWAITING_APPROVAL: ['ASSIGNED', 'IN_PROGRESS', 'RESOLVED'],
    ASSIGNED:          ['IN_PROGRESS', 'RESOLVED'],
    IN_PROGRESS:       ['RESOLVED'],
    RESOLVED:          ['REOPENED'],
    REOPENED:          ['IN_PROGRESS', 'RESOLVED'],
    ESCALATED:         ['IN_PROGRESS', 'RESOLVED'],
};

function ComplaintCard({ c, onStatusChange, onEscalate, loading }: {
    c: WardenComplaint;
    onStatusChange: (id: string, status: string) => void;
    onEscalate: (id: string, reason: string) => void;
    loading: string | null;
}) {
    const [expanded, setExpanded] = useState(false);
    const [showActions, setShowActions] = useState(false);
    const [escalating, setEscalating] = useState(false);
    const [escalateReason, setEscalateReason] = useState('');

    const statusMeta = STATUS_META[c.status] ?? STATUS_META.INTAKE;
    const sevMeta = c.severity ? (SEV_META[(c.severity).toLowerCase()] ?? SEV_META.low) : null;
    const nextStatuses = NEXT_STATUSES[c.status] ?? [];

    return (
        <div style={{ background: C.card, borderRadius: 20, padding: 18, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
            {/* Top badges row */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                {c.category && (
                    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: C.textMuted, background: '#1C1B24', padding: '3px 10px', borderRadius: 999 }}>{c.category}</span>
                )}
                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: statusMeta.text, background: statusMeta.bg, padding: '3px 10px', borderRadius: 999 }}>{statusMeta.label}</span>
                {sevMeta && c.severity && (
                    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: sevMeta.text, background: sevMeta.bg, padding: '3px 10px', borderRadius: 999 }}>{c.severity.toUpperCase()}</span>
                )}
            </div>

            {/* Text */}
            <p style={{ fontSize: 14, color: C.textPrimary, lineHeight: 1.55, margin: '0 0 8px' }}>
                {expanded ? c.text : (c.text.length > 100 ? c.text.slice(0, 100) + '…' : c.text)}
            </p>
            {c.text.length > 100 && (
                <button onClick={() => setExpanded((v) => !v)} style={{ background: 'none', border: 'none', color: C.primary, fontSize: 12, fontWeight: 600, cursor: 'pointer', padding: 0, fontFamily: 'inherit', marginBottom: 8 }}>
                    {expanded ? 'Show less' : 'Read more'}
                </button>
            )}

            {/* Meta footer */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>{c.is_anonymous ? 'person_off' : 'person'}</span>
                    <span style={{ fontSize: 12, color: C.textMuted }}>{c.is_anonymous ? 'Anonymous' : (c.student_id ?? 'Unknown')}</span>
                </div>
                {c.assigned_to && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>assignment_ind</span>
                        <span style={{ fontSize: 12, color: C.textMuted }}>{c.assigned_to}</span>
                    </div>
                )}
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textMuted }}>schedule</span>
                    <span style={{ fontSize: 12, color: C.textMuted }}>
                        {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                    </span>
                </div>
            </div>

            {/* Escalation form */}
            {escalating && (
                <div style={{ background: '#F6ECE5', borderRadius: 12, padding: 12, marginBottom: 12 }}>
                    <p style={{ fontSize: 12, fontWeight: 700, color: C.textPrimary, margin: '0 0 8px' }}>Escalation Reason</p>
                    <textarea value={escalateReason} onChange={(e) => setEscalateReason(e.target.value)} placeholder="Describe why this needs escalation…" rows={3} style={{ width: '100%', background: '#fff', border: 'none', borderRadius: 8, padding: '8px 10px', fontSize: 13, fontFamily: 'inherit', resize: 'none', outline: 'none', boxSizing: 'border-box' as const }} />
                    <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                        <button onClick={() => { setEscalating(false); setEscalateReason(''); }} style={{ flex: 1, height: 36, background: '#E0D7CF', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', color: C.textSecondary }}>Cancel</button>
                        <button onClick={() => { onEscalate(c.id, escalateReason); setEscalating(false); setEscalateReason(''); }} disabled={!escalateReason.trim() || !!loading} style={{ flex: 1, height: 36, background: C.danger, color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: !escalateReason.trim() ? 0.5 : 1 }}>
                            Escalate
                        </button>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => setEscalating((v) => !v)} style={{ height: 36, paddingInline: 14, background: C.dangerLight, color: C.danger, border: 'none', borderRadius: 10, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>warning</span>
                    Escalate
                </button>
                <button onClick={() => setShowActions((v) => !v)} style={{ flex: 1, height: 36, background: showActions ? C.primaryLight : '#F6ECE5', color: C.primary, border: 'none', borderRadius: 10, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>edit</span>
                    Update Status
                </button>
            </div>

            {showActions && nextStatuses.length > 0 && (
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
                    {nextStatuses.map((ns) => {
                        const meta = STATUS_META[ns] ?? STATUS_META.INTAKE;
                        return (
                            <button key={ns} onClick={() => { onStatusChange(c.id, ns); setShowActions(false); }} disabled={!!loading} style={{ height: 34, paddingInline: 14, background: meta.bg, color: meta.text, border: 'none', borderRadius: 10, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', opacity: loading === c.id ? 0.6 : 1 }}>
                                {loading === c.id ? '…' : meta.label}
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export default function ComplaintManagement() {
    const navigate = useNavigate();
    const qc = useQueryClient();
    const [tab, setTab] = useState<'complaints' | 'analytics'>('complaints');
    const [search, setSearch] = useState('');
    const [filterStatus, setFilterStatus] = useState('');
    const [filterCategory] = useState('');
    const [filterSeverity, setFilterSeverity] = useState('');
    const [loading, setLoading] = useState<string | null>(null);

    const { data: complaints = [], isLoading } = useQuery({
        queryKey: ['warden-complaints', filterStatus, filterCategory, filterSeverity],
        queryFn: () => getWardenComplaints({
            ...(filterStatus ? { status: filterStatus } : {}),
            ...(filterCategory ? { category: filterCategory } : {}),
            ...(filterSeverity ? { severity: filterSeverity } : {}),
        }),
    });

    const filtered = complaints.filter((c) => {
        if (!search) return true;
        return c.text.toLowerCase().includes(search.toLowerCase()) ||
            (c.category ?? '').toLowerCase().includes(search.toLowerCase()) ||
            (c.student_id ?? '').toLowerCase().includes(search.toLowerCase());
    });

    const activeCount = complaints.filter((c) => !['RESOLVED'].includes(c.status)).length;

    async function handleStatusChange(id: string, status: string) {
        setLoading(id);
        try {
            await updateComplaintStatus(id, status);
            qc.invalidateQueries({ queryKey: ['warden-complaints'] });
        } finally { setLoading(null); }
    }

    async function handleEscalate(id: string, reason: string) {
        setLoading(id);
        try {
            await escalateComplaint(id, reason);
            qc.invalidateQueries({ queryKey: ['warden-complaints'] });
        } finally { setLoading(null); }
    }

    const categories = [...new Set(complaints.map((c) => c.category).filter(Boolean) as string[])];

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                        <button onClick={() => navigate('/warden')} style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                        </button>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Complaints</h1>
                            {activeCount > 0 && <span style={{ fontSize: 11, fontWeight: 700, color: '#fff', background: C.danger, padding: '2px 8px', borderRadius: 999 }}>{activeCount} active</span>}
                        </div>
                    </div>

                    {/* Tab bar */}
                    <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid rgba(255,255,255,0.06)`, marginBottom: 0 }}>
                        {(['complaints', 'analytics'] as const).map((t) => (
                            <button key={t} onClick={() => setTab(t)} style={{ flex: 1, height: 40, background: 'transparent', border: 'none', borderBottom: tab === t ? `2px solid ${C.primary}` : '2px solid transparent', fontSize: 13, fontWeight: 600, color: tab === t ? C.primary : C.textMuted, cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize' }}>
                                {t}
                            </button>
                        ))}
                    </div>

                    {/* Search + filters (complaints tab only) */}
                    {tab === 'complaints' && (
                        <div style={{ padding: '12px 0 0' }}>
                            <div style={{ background: C.card, borderRadius: 12, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, boxShadow: '0 1px 4px rgba(255,255,255,0.03)' }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 18, color: C.textMuted }}>search</span>
                                <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search complaints…" style={{ flex: 1, background: 'none', border: 'none', outline: 'none', fontSize: 14, fontFamily: 'inherit', color: C.textPrimary }} />
                            </div>
                            <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 12, scrollbarWidth: 'none' }}>
                                {[
                                    { label: 'All Status', value: '', setter: setFilterStatus, current: filterStatus },
                                    { label: 'Escalated', value: 'ESCALATED', setter: setFilterStatus, current: filterStatus },
                                    { label: 'In Progress', value: 'IN_PROGRESS', setter: setFilterStatus, current: filterStatus },
                                    { label: 'Resolved', value: 'RESOLVED', setter: setFilterStatus, current: filterStatus },
                                ].map((chip) => (
                                    <button key={chip.label} onClick={() => chip.setter(chip.current === chip.value ? '' : chip.value)} style={{ flexShrink: 0, height: 30, paddingInline: 12, background: chip.current === chip.value ? C.primary : C.card, color: chip.current === chip.value ? '#fff' : C.textSecondary, border: 'none', borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
                                        {chip.label}
                                    </button>
                                ))}
                                {['HIGH', 'MEDIUM', 'LOW'].map((sev) => (
                                    <button key={sev} onClick={() => setFilterSeverity(filterSeverity === sev ? '' : sev)} style={{ flexShrink: 0, height: 30, paddingInline: 12, background: filterSeverity === sev ? C.primary : C.card, color: filterSeverity === sev ? '#fff' : C.textSecondary, border: 'none', borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
                                        {sev}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </header>

                <div style={{ padding: '12px 20px 100px' }}>
                    {/* Complaints tab */}
                    {tab === 'complaints' && (
                        <>
                            {isLoading && <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{[1, 2, 3].map((i) => <div key={i} style={{ background: C.card, borderRadius: 20, height: 140 }} />)}</div>}

                            {!isLoading && filtered.length === 0 && (
                                <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                    <span className="material-symbols-outlined" style={{ fontSize: 48, color: C.textMuted, display: 'block', marginBottom: 12 }}>chat_bubble</span>
                                    <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: '0 0 6px' }}>No complaints found</p>
                                    <p style={{ fontSize: 14, color: C.textMuted, margin: 0 }}>Try clearing your filters.</p>
                                </div>
                            )}

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                {filtered.map((c) => (
                                    <ComplaintCard key={c.id} c={c} onStatusChange={handleStatusChange} onEscalate={handleEscalate} loading={loading} />
                                ))}
                            </div>
                        </>
                    )}

                    {/* Analytics tab */}
                    {tab === 'analytics' && (
                        <div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 14 }}>
                                {[
                                    { label: 'Total', value: complaints.length, color: C.primary },
                                    { label: 'Active', value: activeCount, color: C.amber },
                                    { label: 'Escalated', value: complaints.filter((c) => c.status === 'ESCALATED').length, color: C.danger },
                                    { label: 'Resolved', value: complaints.filter((c) => c.status === 'RESOLVED').length, color: C.success },
                                ].map((stat) => (
                                    <div key={stat.label} style={{ background: C.card, borderRadius: 16, padding: '16px 14px', boxShadow: '0 2px 8px rgba(255,255,255,0.03)' }}>
                                        <p style={{ fontSize: 26, fontWeight: 800, color: stat.color, margin: '0 0 2px' }}>{stat.value}</p>
                                        <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>{stat.label}</p>
                                    </div>
                                ))}
                            </div>

                            {categories.length > 0 && (
                                <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                                    <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>By Category</p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {categories.map((cat) => {
                                            const count = complaints.filter((c) => c.category === cat).length;
                                            const pct = Math.round((count / complaints.length) * 100);
                                            return (
                                                <div key={cat}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                        <span style={{ fontSize: 13, fontWeight: 600, color: C.textSecondary }}>{cat}</span>
                                                        <span style={{ fontSize: 12, fontWeight: 700, color: C.primary }}>{count} ({pct}%)</span>
                                                    </div>
                                                    <div style={{ height: 6, background: C.primaryLight, borderRadius: 3, overflow: 'hidden' }}>
                                                        <div style={{ height: '100%', width: `${pct}%`, background: C.primary, borderRadius: 3 }} />
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
