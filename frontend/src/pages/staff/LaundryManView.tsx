/**
 * pages/staff/LaundryManView.tsx — Sprint F
 * Laundry man dashboard: date strip, Slots/Machines/Stats tabs, slot management.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { useAuth } from '../../hooks/useAuth';
import { getMachines, getDaySlots } from '../../api/laundryApi';
import { C } from '../../lib/theme';

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

function getDateStrip() {
    const days: { label: string; iso: string }[] = [];
    const now = new Date();
    for (let i = 0; i < 7; i++) {
        const d = new Date(now);
        d.setDate(now.getDate() + i);
        const iso = d.toISOString().slice(0, 10);
        const label = i === 0 ? 'Today' : d.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric' });
        days.push({ label, iso });
    }
    return days;
}

function formatHour(h: number) {
    if (h === 0) return '12 AM';
    if (h < 12) return `${h} AM`;
    if (h === 12) return '12 PM';
    return `${h - 12} PM`;
}

export default function LaundryManView() {
    const { user } = useAuth();
    const [tab, setTab] = useState<'slots' | 'machines' | 'stats'>('slots');
    const [selectedDayIso, setSelectedDayIso] = useState(new Date().toISOString().slice(0, 10));
    const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null);

    const days = getDateStrip();
    const userName = user?.name ?? 'Staff';

    const { data: machines = [] } = useQuery({ queryKey: ['machines'], queryFn: getMachines });
    const { data: slots = [] } = useQuery({
        queryKey: ['day-slots', selectedDayIso],
        queryFn: () => getDaySlots(selectedDayIso),
        enabled: tab === 'slots',
    });

    const activeMachineId = selectedMachineId ?? machines[0]?.id ?? null;
    const machineSlots = slots.filter((s) => s.machine_id === activeMachineId);

    // Summary counts using DaySlot fields
    const booked = slots.filter((s) => s.booking_status === 'booked').length;
    const yours = slots.filter((s) => s.booking_status === 'booked' && s.student_id === user?.id).length;
    const available = slots.filter((s) => s.booking_status === 'available').length;

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Header */}
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 0' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <div style={{ width: 42, height: 42, borderRadius: '50%', background: C.success, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700 }}>
                                {initials(userName)}
                            </div>
                            <div>
                                <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>Good morning,</p>
                                <p style={{ fontSize: 16, fontWeight: 700, color: C.textPrimary, margin: 0 }}>{userName}</p>
                            </div>
                        </div>
                        <div style={{ width: 38, height: 38, background: C.card, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>notifications</span>
                        </div>
                    </div>

                    {/* Tab nav */}
                    <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                        {(['slots', 'machines', 'stats'] as const).map((t) => (
                            <button key={t} onClick={() => setTab(t)} style={{ flex: 1, height: 40, background: 'transparent', border: 'none', borderBottom: tab === t ? `2px solid ${C.primary}` : '2px solid transparent', fontSize: 13, fontWeight: 600, color: tab === t ? C.primary : C.textMuted, cursor: 'pointer', fontFamily: 'inherit', textTransform: 'capitalize' }}>
                                {t}
                            </button>
                        ))}
                    </div>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* SLOTS TAB */}
                    {tab === 'slots' && (
                        <>
                            {/* Date strip */}
                            <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBlock: 14, scrollbarWidth: 'none' }}>
                                {days.map((d) => (
                                    <button key={d.iso} onClick={() => setSelectedDayIso(d.iso)} style={{ flexShrink: 0, background: selectedDayIso === d.iso ? C.primary : C.card, color: selectedDayIso === d.iso ? '#fff' : C.textSecondary, border: 'none', borderRadius: 12, padding: '8px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', boxShadow: '0 1px 4px rgba(255,255,255,0.06)' }}>
                                        {d.label}
                                    </button>
                                ))}
                            </div>

                            {/* Summary strip */}
                            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
                                {[
                                    { label: 'Booked', value: booked, color: C.primary, bg: C.primaryLight },
                                    { label: 'Available', value: available, color: C.success, bg: C.successLight },
                                    { label: 'Your Slots', value: yours, color: C.amber, bg: 'rgba(255,184,0,0.12)' },
                                ].map((stat) => (
                                    <div key={stat.label} style={{ flex: 1, background: C.card, borderRadius: 14, padding: '12px 10px', textAlign: 'center', boxShadow: '0 1px 4px rgba(255,255,255,0.06)' }}>
                                        <p style={{ fontSize: 18, fontWeight: 800, color: stat.color, margin: '0 0 2px' }}>{stat.value}</p>
                                        <p style={{ fontSize: 11, color: C.textMuted, margin: 0, fontWeight: 500 }}>{stat.label}</p>
                                    </div>
                                ))}
                            </div>

                            {/* Machine tabs */}
                            <div style={{ display: 'flex', gap: 8, overflowX: 'auto', marginBottom: 14, scrollbarWidth: 'none' }}>
                                {machines.map((m) => {
                                    const isActive = m.id === activeMachineId;
                                    const statusColor = m.is_active ? C.success : C.danger;
                                    return (
                                        <button key={m.id} onClick={() => setSelectedMachineId(m.id)} style={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 6, background: isActive ? C.primaryLight : C.card, border: `1.5px solid ${isActive ? C.primary : 'transparent'}`, borderRadius: 10, padding: '8px 14px', cursor: 'pointer', fontFamily: 'inherit' }}>
                                            <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor }} />
                                            <span style={{ fontSize: 13, fontWeight: 600, color: isActive ? C.primary : C.textSecondary }}>{m.name}</span>
                                        </button>
                                    );
                                })}
                            </div>

                            {/* Slot cards */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {machineSlots.length === 0 && (
                                    <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                                        <span className="material-symbols-outlined" style={{ fontSize: 40, color: C.textMuted, display: 'block', marginBottom: 10 }}>local_laundry_service</span>
                                        <p style={{ fontSize: 14, color: C.textMuted, margin: 0 }}>No slots for this day.</p>
                                    </div>
                                )}
                                {machineSlots.map((slot, idx) => {
                                    const hour = parseInt(slot.slot_time.split(':')[0]);
                                    const isBooked = slot.booking_status === 'booked';
                                    const isAvailable = slot.booking_status === 'available';
                                    const borderColor = isBooked ? C.amber : isAvailable ? 'transparent' : C.primary;
                                    const statusLabel = isAvailable ? 'Available' : slot.booking_status === 'completed' ? 'Completed' : 'Booked';

                                    return (
                                        <div key={slot.id ?? `${slot.machine_id}-${idx}`} style={{ background: C.card, borderRadius: 16, padding: '14px 16px', borderLeft: `4px solid ${borderColor}`, boxShadow: '0 1px 6px rgba(255,255,255,0.03)', display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <div style={{ flex: 1 }}>
                                                <p style={{ fontSize: 14, fontWeight: 700, color: C.textPrimary, margin: '0 0 2px' }}>
                                                    {formatHour(hour)} — {formatHour(hour + 1)}
                                                </p>
                                                <p style={{ fontSize: 12, color: C.textMuted, margin: 0 }}>{statusLabel}</p>
                                            </div>
                                            {isBooked && slot.id && (
                                                <div style={{ display: 'flex', gap: 6 }}>
                                                    <button style={{ height: 34, paddingInline: 12, background: C.successLight, color: C.success, border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
                                                        Mark Done
                                                    </button>
                                                    <button style={{ height: 34, paddingInline: 12, background: C.dangerLight, color: C.danger, border: 'none', borderRadius: 8, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}>
                                                        Cancel
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </>
                    )}

                    {/* MACHINES TAB */}
                    {tab === 'machines' && (
                        <div style={{ paddingTop: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {machines.map((m) => {
                                const statusColor = m.is_active ? C.success : C.danger;
                                const statusLabel = m.is_active ? 'Operational' : 'Under Repair';
                                return (
                                    <div key={m.id} style={{ background: C.card, borderRadius: 18, padding: 18, boxShadow: '0 2px 8px rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 14 }}>
                                        <div style={{ width: 44, height: 44, borderRadius: 14, background: m.is_active ? C.successLight : C.dangerLight, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 22, color: statusColor }}>local_laundry_service</span>
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <p style={{ fontSize: 15, fontWeight: 700, color: C.textPrimary, margin: '0 0 2px' }}>{m.name}</p>
                                            {m.last_reported_issue && <p style={{ fontSize: 12, color: C.textMuted, margin: 0 }}>Issue: {m.last_reported_issue}</p>}
                                        </div>
                                        <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: statusColor, background: m.is_active ? C.successLight : C.dangerLight, padding: '4px 10px', borderRadius: 999 }}>
                                            {statusLabel}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* STATS TAB */}
                    {tab === 'stats' && (
                        <div style={{ paddingTop: 14 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                                {[
                                    { label: 'Total Machines', value: machines.length, color: C.primary },
                                    { label: 'Operational', value: machines.filter((m) => m.is_active).length, color: C.success },
                                    { label: 'Under Repair', value: machines.filter((m) => !m.is_active).length, color: C.danger },
                                    { label: "Today's Bookings", value: booked, color: C.amber },
                                ].map((stat) => (
                                    <div key={stat.label} style={{ background: C.card, borderRadius: 16, padding: 16, boxShadow: '0 2px 8px rgba(255,255,255,0.03)' }}>
                                        <p style={{ fontSize: 26, fontWeight: 800, color: stat.color, margin: '0 0 4px' }}>{stat.value}</p>
                                        <p style={{ fontSize: 12, color: C.textMuted, margin: 0, fontWeight: 500 }}>{stat.label}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </AppShell>
    );
}
