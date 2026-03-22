/**
 * pages/student/LaundryBooking.tsx — Sprint F
 * Date strip → machine tabs → slot grid → upcoming bookings.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getMachines, getDaySlots, getMyBookings, bookSlot, cancelBooking } from '../../api/laundryApi';

const C = {
    bg: '#FFF5EE',
    primary: '#4647D3',
    primaryLight: 'rgba(70,71,211,0.10)',
    primaryContainer: 'rgba(70,71,211,0.12)',
    textPrimary: '#1A1A2E',
    textSecondary: '#6B6B80',
    textMuted: '#9B9BAF',
    card: '#FFFFFF',
    danger: '#E83B2A',
    dangerLight: 'rgba(232,59,42,0.10)',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.12)',
    border: 'rgba(0,0,0,0.06)',
};

function toISO(date: Date) {
    return date.toISOString().slice(0, 10);
}

function buildWeek(): Date[] {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return Array.from({ length: 7 }, (_, i) => {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        return d;
    });
}

const WEEK_DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const TODAY = toISO(new Date());

// Pre-generate time slots 7:00 – 21:00 every hour
const TIME_SLOTS = Array.from({ length: 15 }, (_, i) => {
    const h = 7 + i;
    return `${String(h).padStart(2, '0')}:00`;
});

function formatTime(t: string) {
    const [h, m] = t.split(':').map(Number);
    const suffix = h < 12 ? 'AM' : 'PM';
    const displayH = h % 12 || 12;
    return `${displayH}:${String(m).padStart(2, '0')} ${suffix}`;
}

export default function LaundryBooking() {
    const qc = useQueryClient();
    const week = buildWeek();

    const [selectedDate, setSelectedDate] = useState(TODAY);
    const [selectedMachineIdx, setSelectedMachineIdx] = useState(0);
    const [pendingSlot, setPendingSlot] = useState<{ time: string; machineId: string } | null>(null);
    const [cancelling, setCancelling] = useState<string | null>(null);

    const { data: machines = [] } = useQuery({ queryKey: ['machines'], queryFn: getMachines });
    const { data: daySlots = [] } = useQuery({
        queryKey: ['day-slots', selectedDate],
        queryFn: () => getDaySlots(selectedDate),
    });
    const { data: myBookings = [] } = useQuery({ queryKey: ['my-bookings'], queryFn: getMyBookings });

    const bookMutation = useMutation({
        mutationFn: bookSlot,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['day-slots', selectedDate] });
            qc.invalidateQueries({ queryKey: ['my-bookings'] });
            setPendingSlot(null);
        },
    });

    const selectedMachine = machines[selectedMachineIdx];

    function getSlotState(time: string, machineId: string) {
        const slot = daySlots.find((s) => s.slot_time === time && s.machine_id === machineId);
        if (!slot) return 'available';
        if (slot.is_yours) return 'yours';
        if (slot.machine_status === 'repair') return 'repair';
        if (!slot.is_available) return 'booked';
        return 'available';
    }

    async function handleCancelBooking(id: string) {
        setCancelling(id);
        try {
            await cancelBooking(id);
            qc.invalidateQueries({ queryKey: ['my-bookings'] });
            qc.invalidateQueries({ queryKey: ['day-slots'] });
        } finally {
            setCancelling(null);
        }
    }

    const upcomingBookings = myBookings.filter((b) => b.status === 'booked');

    return (
        <AppShell>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                {/* Header */}
                <header style={{ padding: '52px 20px 16px' }}>
                    <h1 style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: '0 0 4px' }}>
                        Laundry Booking
                    </h1>
                    <p style={{ fontSize: 13, color: C.textSecondary, margin: 0 }}>
                        Reserve a machine slot in advance.
                    </p>
                </header>

                {/* Date strip */}
                <div
                    style={{
                        display: 'flex',
                        gap: 10,
                        overflowX: 'auto',
                        padding: '0 20px 16px',
                        scrollbarWidth: 'none',
                    } as React.CSSProperties}
                >
                    {week.map((d) => {
                        const iso = toISO(d);
                        const isToday = iso === TODAY;
                        const isSelected = iso === selectedDate;
                        return (
                            <button
                                key={iso}
                                onClick={() => setSelectedDate(iso)}
                                style={{
                                    flexShrink: 0,
                                    width: 52,
                                    height: 66,
                                    borderRadius: 14,
                                    background: isSelected ? C.primary : C.card,
                                    border: 'none',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: 3,
                                    cursor: 'pointer',
                                    boxShadow: isSelected ? '0 4px 14px rgba(70,71,211,0.25)' : '0 1px 4px rgba(0,0,0,0.05)',
                                }}
                            >
                                <span style={{ fontSize: 10, fontWeight: 600, color: isSelected ? 'rgba(255,255,255,0.75)' : C.textMuted }}>
                                    {WEEK_DAYS[d.getDay()]}
                                </span>
                                <span style={{ fontSize: 18, fontWeight: 700, color: isSelected ? '#fff' : C.textPrimary }}>
                                    {d.getDate()}
                                </span>
                                {isToday && (
                                    <span
                                        style={{
                                            width: 5,
                                            height: 5,
                                            borderRadius: '50%',
                                            background: isSelected ? '#fff' : C.primary,
                                        }}
                                    />
                                )}
                            </button>
                        );
                    })}
                </div>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* Machine tabs */}
                    {machines.length > 0 && (
                        <div style={{ display: 'flex', gap: 8, marginBottom: 18, overflowX: 'auto', scrollbarWidth: 'none' } as React.CSSProperties}>
                            {machines.map((m, i) => {
                                const active = i === selectedMachineIdx;
                                return (
                                    <button
                                        key={m.id}
                                        onClick={() => setSelectedMachineIdx(i)}
                                        style={{
                                            flexShrink: 0,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 7,
                                            background: active ? C.primaryContainer : C.card,
                                            border: 'none',
                                            borderRadius: 999,
                                            padding: '8px 16px',
                                            cursor: 'pointer',
                                            fontFamily: 'inherit',
                                        }}
                                    >
                                        <span
                                            style={{
                                                width: 8,
                                                height: 8,
                                                borderRadius: '50%',
                                                background: m.is_active ? C.success : C.danger,
                                                flexShrink: 0,
                                            }}
                                        />
                                        <span style={{ fontSize: 13, fontWeight: active ? 700 : 500, color: active ? C.primary : C.textPrimary }}>
                                            {m.name}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    )}

                    {/* Slot grid */}
                    {selectedMachine && (
                        <>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 12px' }}>
                                Available Slots
                            </p>
                            <div
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: '1fr 1fr',
                                    gap: 10,
                                    marginBottom: 24,
                                }}
                            >
                                {TIME_SLOTS.map((time) => {
                                    const state = getSlotState(time, selectedMachine.id);
                                    const colors = {
                                        available: { bg: C.card, border: C.border, label: C.textPrimary, sub: C.success, subLabel: 'Available' },
                                        booked:    { bg: '#F6F6F6', border: 'transparent', label: '#BDBDBD', sub: '#BDBDBD', subLabel: 'Booked' },
                                        yours:     { bg: C.primaryContainer, border: C.primary, label: C.primary, sub: C.primary, subLabel: 'Your Slot' },
                                        repair:    { bg: C.dangerLight, border: C.danger, label: C.danger, sub: C.danger, subLabel: 'Repair' },
                                    }[state];

                                    return (
                                        <button
                                            key={time}
                                            onClick={() => {
                                                if (state === 'available' && selectedMachine.is_active) {
                                                    setPendingSlot({ time, machineId: selectedMachine.id });
                                                }
                                            }}
                                            disabled={state !== 'available' || !selectedMachine.is_active}
                                            style={{
                                                background: colors.bg,
                                                border: `1.5px solid ${colors.border}`,
                                                borderRadius: 14,
                                                padding: '12px 14px',
                                                textAlign: 'left',
                                                cursor: state === 'available' ? 'pointer' : 'default',
                                                fontFamily: 'inherit',
                                            }}
                                        >
                                            <p style={{ fontSize: 15, fontWeight: 700, color: colors.label, margin: '0 0 3px' }}>
                                                {formatTime(time)}
                                            </p>
                                            <p style={{ fontSize: 11, fontWeight: 600, color: colors.sub, margin: 0 }}>
                                                {colors.subLabel}
                                            </p>
                                        </button>
                                    );
                                })}
                            </div>
                        </>
                    )}

                    {/* Upcoming bookings */}
                    {upcomingBookings.length > 0 && (
                        <section>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 12px' }}>
                                Your Bookings
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {upcomingBookings.map((b) => (
                                    <div
                                        key={b.id}
                                        style={{
                                            background: C.card,
                                            borderRadius: 14,
                                            padding: '14px 16px',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: 14,
                                            boxShadow: '0 1px 6px rgba(0,0,0,0.04)',
                                        }}
                                    >
                                        <div
                                            style={{
                                                width: 40,
                                                height: 40,
                                                borderRadius: 12,
                                                background: C.primaryContainer,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flexShrink: 0,
                                            }}
                                        >
                                            <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.primary }}>
                                                local_laundry_service
                                            </span>
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <p style={{ fontSize: 13, fontWeight: 600, color: C.textPrimary, margin: '0 0 2px' }}>
                                                {b.date} · {b.start_time}
                                            </p>
                                            <p style={{ fontSize: 11, color: C.textMuted, margin: 0 }}>
                                                {b.is_priority ? '⭐ Priority booking' : 'Standard booking'}
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => handleCancelBooking(b.id)}
                                            disabled={cancelling === b.id}
                                            style={{
                                                background: C.dangerLight,
                                                border: 'none',
                                                borderRadius: 8,
                                                padding: '6px 12px',
                                                fontSize: 12,
                                                fontWeight: 600,
                                                color: C.danger,
                                                cursor: 'pointer',
                                                fontFamily: 'inherit',
                                                opacity: cancelling === b.id ? 0.5 : 1,
                                            }}
                                        >
                                            {cancelling === b.id ? '…' : 'Cancel'}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            </div>

            {/* Booking confirmation bottom sheet */}
            {pendingSlot && (
                <div
                    style={{
                        position: 'fixed',
                        inset: 0,
                        zIndex: 100,
                        background: 'rgba(0,0,0,0.40)',
                        display: 'flex',
                        alignItems: 'flex-end',
                    }}
                    onClick={() => setPendingSlot(null)}
                >
                    <div
                        style={{
                            width: '100%',
                            background: C.card,
                            borderRadius: '20px 20px 0 0',
                            padding: '24px 24px 48px',
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div style={{ width: 36, height: 4, borderRadius: 999, background: '#E0E0E0', margin: '0 auto 20px' }} />
                        <h2 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: '0 0 8px' }}>
                            Confirm booking
                        </h2>
                        <p style={{ fontSize: 14, color: C.textSecondary, margin: '0 0 24px' }}>
                            {formatTime(pendingSlot.time)} · {selectedDate} ·{' '}
                            {machines.find((m) => m.id === pendingSlot.machineId)?.name ?? 'Machine'}
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <button
                                onClick={() => setPendingSlot(null)}
                                style={{
                                    height: 48,
                                    background: '#F0EDE8',
                                    border: 'none',
                                    borderRadius: 12,
                                    fontSize: 14,
                                    fontWeight: 600,
                                    color: C.textPrimary,
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                }}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => bookMutation.mutate({ machine_id: pendingSlot.machineId, slot_date: selectedDate, slot_time: pendingSlot.time })}
                                disabled={bookMutation.isPending}
                                style={{
                                    height: 48,
                                    background: C.primary,
                                    border: 'none',
                                    borderRadius: 12,
                                    fontSize: 14,
                                    fontWeight: 700,
                                    color: '#fff',
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                    boxShadow: '0 4px 14px rgba(70,71,211,0.25)',
                                    opacity: bookMutation.isPending ? 0.7 : 1,
                                }}
                            >
                                {bookMutation.isPending ? 'Booking…' : 'Confirm'}
                            </button>
                        </div>
                        {bookMutation.isError && (
                            <p style={{ fontSize: 12, color: C.danger, textAlign: 'center', marginTop: 10 }}>
                                Slot unavailable. Try another time.
                            </p>
                        )}
                    </div>
                </div>
            )}
        </AppShell>
    );
}
