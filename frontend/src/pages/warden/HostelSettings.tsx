/**
 * pages/warden/HostelSettings.tsx — Sprint F
 * Hostel configuration: General, Complaints, Mess, Laundry sections with per-section save.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { useAuth } from '../../hooks/useAuth';
import { getHostelConfig, updateHostelConfig, type HostelConfig } from '../../api/hostelSettingsApi';

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
    amber: '#D48C00',
};


function FieldRow({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: C.textPrimary, flex: 1 }}>{label}</span>
            {children}
        </div>
    );
}

function NumberInput({ value, onChange, min, max }: { value: number; onChange: (v: number) => void; min?: number; max?: number }) {
    return (
        <input
            type="number"
            value={value}
            min={min}
            max={max}
            onChange={(e) => onChange(Number(e.target.value))}
            style={{ width: 80, background: '#1C1B24', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '8px 12px', fontSize: 14, fontFamily: 'inherit', outline: 'none', textAlign: 'center', color: C.textPrimary }}
        />
    );
}

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

export default function HostelSettings() {
    const navigate = useNavigate();
    const { user } = useAuth();
    const qc = useQueryClient();

    const { data: config, isLoading } = useQuery({ queryKey: ['hostel-config'], queryFn: getHostelConfig });

    // Local draft state per section
    const [general, setGeneral] = useState<Partial<HostelConfig>>({});
    const [complaints, setComplaints] = useState<Partial<HostelConfig>>({});
    const [mess, setMess] = useState<Partial<HostelConfig>>({});
    const [laundry, setLaundry] = useState<Partial<HostelConfig>>({});
    const [savedSection, setSavedSection] = useState<string | null>(null);

    useEffect(() => {
        if (!config) return;
        setGeneral({
            hostel_name: config.hostel_name,
            hostel_mode: config.hostel_mode,
            total_floors: config.total_floors,
            total_students_capacity: config.total_students_capacity,
        });
        setComplaints({
            complaint_rate_limit: config.complaint_rate_limit,
            approval_queue_timeout_minutes: config.approval_queue_timeout_minutes,
            complaint_confidence_threshold: config.complaint_confidence_threshold,
        });
        setMess({
            mess_alert_threshold: config.mess_alert_threshold,
            mess_critical_threshold: config.mess_critical_threshold,
            mess_min_participation: config.mess_min_participation,
            mess_min_responses: config.mess_min_responses,
        });
        setLaundry({
            laundry_slots_start_hour: config.laundry_slots_start_hour,
            laundry_slots_end_hour: config.laundry_slots_end_hour,
            laundry_slot_duration_hours: config.laundry_slot_duration_hours,
            laundry_noshow_penalty_hours: config.laundry_noshow_penalty_hours,
            laundry_cancellation_deadline_minutes: config.laundry_cancellation_deadline_minutes,
        });
    }, [config]);

    const saveMut = useMutation({
        mutationFn: (patch: Partial<HostelConfig>) => updateHostelConfig(patch),
        onSuccess: (_, patch) => {
            qc.invalidateQueries({ queryKey: ['hostel-config'] });
            const section = Object.keys(patch)[0];
            setSavedSection(section);
            setTimeout(() => setSavedSection(null), 2000);
        },
    });

    const userName = user?.name ?? 'Warden';

    if (isLoading || !config) {
        return (
            <AppShell>
                <div style={{ background: C.bg, minHeight: '100dvh', padding: '80px 20px 20px' }}>
                    {[1, 2, 3, 4].map((i) => <div key={i} style={{ background: C.card, borderRadius: 20, height: 180, marginBottom: 12 }} />)}
                </div>
            </AppShell>
        );
    }

    function SaveButton({ section, patch }: { section: string; patch: Partial<HostelConfig> }) {
        const saved = savedSection === section;
        return (
            <button
                onClick={() => saveMut.mutate(patch)}
                disabled={saveMut.isPending}
                style={{ width: '100%', height: 42, background: saved ? C.success : C.primary, color: '#fff', border: 'none', borderRadius: 12, fontSize: 14, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', transition: 'background 0.3s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
            >
                {saved ? (<><span className="material-symbols-outlined" style={{ fontSize: 16 }}>check</span>Saved!</>) : 'Save Changes'}
            </button>
        );
    }

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <button onClick={() => navigate('/warden')} style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                        </button>
                        <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Settings</h1>
                    </div>
                    <div style={{ width: 38, height: 38, borderRadius: '50%', background: C.primary, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700 }}>
                        {initials(userName)}
                    </div>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* General */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: 0 }}>General</p>
                            {config.hostel_code && (
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: C.primaryLight, borderRadius: 999, padding: '4px 12px' }}>
                                    <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.primary }}>tag</span>
                                    <span style={{ fontSize: 12, fontWeight: 700, color: C.primary, letterSpacing: '0.08em' }}>{config.hostel_code}</span>
                                </div>
                            )}
                        </div>

                        <div style={{ marginBottom: 14 }}>
                            <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: 'block', marginBottom: 6 }}>Hostel Name</label>
                            <input
                                value={general.hostel_name ?? ''}
                                onChange={(e) => setGeneral((p) => ({ ...p, hostel_name: e.target.value }))}
                                style={{ width: '100%', background: '#1C1B24', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: '10px 14px', fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary }}
                            />
                        </div>

                        <FieldRow label="Hostel Mode">
                            <select
                                value={general.hostel_mode ?? 'college'}
                                onChange={(e) => setGeneral((p) => ({ ...p, hostel_mode: e.target.value }))}
                                style={{ background: '#1C1B24', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '8px 12px', fontSize: 14, fontFamily: 'inherit', outline: 'none', color: C.textPrimary, cursor: 'pointer' }}
                            >
                                <option value="college">College</option>
                                <option value="autonomous">Autonomous</option>
                            </select>
                        </FieldRow>
                        <FieldRow label="Number of Floors">
                            <NumberInput value={general.total_floors ?? 0} onChange={(v) => setGeneral((p) => ({ ...p, total_floors: v }))} min={1} max={20} />
                        </FieldRow>
                        <FieldRow label="Capacity (students)">
                            <NumberInput value={general.total_students_capacity ?? 0} onChange={(v) => setGeneral((p) => ({ ...p, total_students_capacity: v }))} min={1} />
                        </FieldRow>

                        <SaveButton section="hostel_name" patch={general} />
                    </div>

                    {/* Complaints */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>Complaints</p>

                        <FieldRow label="Rate limit (per day)">
                            <NumberInput value={complaints.complaint_rate_limit ?? 5} onChange={(v) => setComplaints((p) => ({ ...p, complaint_rate_limit: v }))} min={1} max={20} />
                        </FieldRow>
                        <FieldRow label="Approval timeout (min)">
                            <NumberInput value={complaints.approval_queue_timeout_minutes ?? 2880} onChange={(v) => setComplaints((p) => ({ ...p, approval_queue_timeout_minutes: v }))} min={60} />
                        </FieldRow>
                        <FieldRow label="AI confidence threshold (%)">
                            <NumberInput value={complaints.complaint_confidence_threshold ?? 80} onChange={(v) => setComplaints((p) => ({ ...p, complaint_confidence_threshold: v }))} min={50} max={99} />
                        </FieldRow>

                        {/* AI info chip */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: C.primaryLight, borderRadius: 10, padding: '8px 12px', marginBottom: 14 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16, color: C.primary }}>auto_awesome</span>
                            <span style={{ fontSize: 12, color: C.primary, fontWeight: 500 }}>
                                Higher threshold = fewer AI overrides; lower = more manual reviews.
                            </span>
                        </div>

                        <SaveButton section="complaint_rate_limit" patch={complaints} />
                    </div>

                    {/* Mess */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>Mess</p>

                        <FieldRow label="Alert threshold (avg score)">
                            <NumberInput value={mess.mess_alert_threshold ?? 3} onChange={(v) => setMess((p) => ({ ...p, mess_alert_threshold: v }))} min={1} max={5} />
                        </FieldRow>
                        <FieldRow label="Critical threshold (avg score)">
                            <NumberInput value={mess.mess_critical_threshold ?? 2} onChange={(v) => setMess((p) => ({ ...p, mess_critical_threshold: v }))} min={1} max={5} />
                        </FieldRow>
                        <FieldRow label="Min participation (%)">
                            <NumberInput value={mess.mess_min_participation ?? 20} onChange={(v) => setMess((p) => ({ ...p, mess_min_participation: v }))} min={1} max={100} />
                        </FieldRow>
                        <FieldRow label="Min responses">
                            <NumberInput value={mess.mess_min_responses ?? 5} onChange={(v) => setMess((p) => ({ ...p, mess_min_responses: v }))} min={1} />
                        </FieldRow>

                        <SaveButton section="mess_alert_threshold" patch={mess} />
                    </div>

                    {/* Laundry */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>Laundry</p>

                        <FieldRow label="Start hour (24h)">
                            <NumberInput value={laundry.laundry_slots_start_hour ?? 7} onChange={(v) => setLaundry((p) => ({ ...p, laundry_slots_start_hour: v }))} min={0} max={23} />
                        </FieldRow>
                        <FieldRow label="End hour (24h)">
                            <NumberInput value={laundry.laundry_slots_end_hour ?? 21} onChange={(v) => setLaundry((p) => ({ ...p, laundry_slots_end_hour: v }))} min={1} max={24} />
                        </FieldRow>
                        <FieldRow label="Slot duration (hrs)">
                            <NumberInput value={laundry.laundry_slot_duration_hours ?? 1} onChange={(v) => setLaundry((p) => ({ ...p, laundry_slot_duration_hours: v }))} min={1} max={4} />
                        </FieldRow>
                        <FieldRow label="No-show penalty (hrs)">
                            <NumberInput value={laundry.laundry_noshow_penalty_hours ?? 24} onChange={(v) => setLaundry((p) => ({ ...p, laundry_noshow_penalty_hours: v }))} min={1} max={72} />
                        </FieldRow>
                        <FieldRow label="Cancel deadline (min)">
                            <NumberInput value={laundry.laundry_cancellation_deadline_minutes ?? 30} onChange={(v) => setLaundry((p) => ({ ...p, laundry_cancellation_deadline_minutes: v }))} min={5} />
                        </FieldRow>

                        <SaveButton section="laundry_slots_start_hour" patch={laundry} />
                    </div>
                </div>
            </div>
        </AppShell>
    );
}
