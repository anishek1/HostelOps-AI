/**
 * pages/warden/CreateStaffAccount.tsx — Sprint F
 * Create staff accounts: 4-role selector grid, temp password, existing staff list.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import AppShell from '../../components/AppShell';
import { getStaffMembers, createStaffAccount, deleteStaffAccount } from '../../api/wardenApi';
import { useAuth } from '../../hooks/useAuth';

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
};

const ROLES = [
    { value: 'laundry_man', label: 'Laundry Man',  icon: 'local_laundry_service' },
    { value: 'mess_staff',  label: 'Mess Staff',   icon: 'restaurant' },
    { value: 'warden',      label: 'Warden',       icon: 'shield_person' },
];

const ROLE_LABELS: Record<string, string> = {
    laundry_man: 'Laundry Man',
    mess_staff:  'Mess Staff',
    warden:      'Warden',
    student:     'Student',
};

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

export default function CreateStaffAccount() {
    const navigate = useNavigate();
    const qc = useQueryClient();
    const { user } = useAuth();

    const [fullName, setFullName] = useState('');
    const [roomNumber, setRoomNumber] = useState('');
    const [role, setRole] = useState('');
    const [tempPassword, setTempPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { data: staff = [] } = useQuery({ queryKey: ['staff-members'], queryFn: getStaffMembers });

    const createMut = useMutation({
        mutationFn: () => createStaffAccount({ name: fullName, room_number: roomNumber, role, password: tempPassword, hostel_mode: user?.hostel_mode ?? 'college' }),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ['staff-members'] });
            setFullName(''); setRoomNumber(''); setRole(''); setTempPassword(''); setError(null);
        },
        onError: () => setError('Failed to create account. Please try again.'),
    });

    const deleteMut = useMutation({
        mutationFn: deleteStaffAccount,
        onSuccess: () => qc.invalidateQueries({ queryKey: ['staff-members'] }),
    });

    const canSubmit = fullName.trim() && roomNumber.trim() && role && tempPassword.length >= 6 && !createMut.isPending;

    return (
        <AppShell hasStickyCta>
            <div style={{ background: C.bg, minHeight: '100dvh' }}>
                <header style={{ position: 'sticky', top: 0, zIndex: 20, background: C.bg, padding: '52px 20px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                    <button onClick={() => navigate('/warden')} style={{ background: C.card, border: 'none', borderRadius: '50%', width: 40, height: 40, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 20, color: C.textPrimary }}>arrow_back</span>
                    </button>
                    <h1 style={{ fontSize: 18, fontWeight: 700, color: C.textPrimary, margin: 0 }}>Create Staff Account</h1>
                </header>

                <div style={{ padding: '0 20px 20px' }}>
                    <p style={{ fontSize: 13, color: C.textMuted, margin: '0 0 20px', lineHeight: 1.5 }}>
                        Add a staff member to the hostel system. They will use their room number and the temporary password to log in.
                    </p>

                    {/* Form card */}
                    <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)', marginBottom: 14 }}>
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>Staff Details</p>

                        <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: 'block', marginBottom: 6 }}>Full Name</label>
                        <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="e.g. Mohammed Raza" style={{ width: '100%', background: '#F6ECE5', border: 'none', borderRadius: 12, padding: '12px 14px', fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary, marginBottom: 12 }} />

                        <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: 'block', marginBottom: 6 }}>Room / Office Number</label>
                        <input value={roomNumber} onChange={(e) => setRoomNumber(e.target.value)} placeholder="e.g. Staff-02 or Office-101" style={{ width: '100%', background: '#F6ECE5', border: 'none', borderRadius: 12, padding: '12px 14px', fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary, marginBottom: 16 }} />

                        <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: 'block', marginBottom: 10 }}>Role</label>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                            {ROLES.map((r) => {
                                const selected = role === r.value;
                                return (
                                    <button key={r.value} type="button" onClick={() => setRole(r.value)} style={{ background: selected ? C.primaryLight : '#F6ECE5', border: `2px solid ${selected ? C.primary : 'transparent'}`, borderRadius: 14, padding: '14px 12px', cursor: 'pointer', fontFamily: 'inherit', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                                        <span className="material-symbols-outlined" style={{ fontSize: 22, color: selected ? C.primary : C.textMuted }}>{r.icon}</span>
                                        <span style={{ fontSize: 12, fontWeight: 600, color: selected ? C.primary : C.textSecondary }}>{r.label}</span>
                                    </button>
                                );
                            })}
                        </div>

                        <label style={{ fontSize: 12, fontWeight: 600, color: C.textSecondary, display: 'block', marginBottom: 6 }}>Temporary Password</label>
                        <div style={{ position: 'relative' }}>
                            <input type={showPassword ? 'text' : 'password'} value={tempPassword} onChange={(e) => setTempPassword(e.target.value)} placeholder="Min. 6 characters" style={{ width: '100%', background: '#F6ECE5', border: 'none', borderRadius: 12, padding: '12px 48px 12px 14px', fontSize: 14, fontFamily: 'inherit', outline: 'none', boxSizing: 'border-box' as const, color: C.textPrimary }} />
                            <button type="button" onClick={() => setShowPassword((v) => !v)} style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: C.textMuted }}>
                                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{showPassword ? 'visibility_off' : 'visibility'}</span>
                            </button>
                        </div>
                        <p style={{ fontSize: 11, color: C.textMuted, margin: '6px 0 0' }}>The staff member should change this on first login.</p>
                    </div>

                    {error && <p style={{ fontSize: 13, color: C.danger, fontWeight: 500, margin: '0 0 12px' }}>{error}</p>}

                    {/* Existing staff */}
                    {staff.length > 0 && (
                        <div style={{ background: C.card, borderRadius: 20, padding: 20, boxShadow: '0 2px 12px rgba(255,255,255,0.06)' }}>
                            <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>Existing Staff</p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                {staff.map((s) => (
                                    <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <div style={{ width: 38, height: 38, borderRadius: '50%', background: '#F6ECE5', color: C.textSecondary, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                                            {initials(s.name)}
                                        </div>
                                        <div style={{ flex: 1 }}>
                                            <p style={{ fontSize: 14, fontWeight: 600, color: C.textPrimary, margin: 0 }}>{s.name}</p>
                                            <p style={{ fontSize: 12, color: C.textMuted, margin: 0 }}>{ROLE_LABELS[s.role] ?? s.role}{s.room_number ? ` · ${s.room_number}` : ''}</p>
                                        </div>
                                        <button onClick={() => deleteMut.mutate(s.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: C.textMuted }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 18 }}>delete</span>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Sticky CTA */}
            <div style={{ position: 'fixed', bottom: 64, left: '50%', transform: 'translateX(-50%)', width: '100%', maxWidth: 430, padding: '12px 20px', background: 'linear-gradient(to top, #0A0A0F 70%, transparent)', zIndex: 30 }}>
                <button onClick={() => createMut.mutate()} disabled={!canSubmit} style={{ width: '100%', height: 52, background: C.primary, color: '#fff', border: 'none', borderRadius: 14, fontSize: 15, fontWeight: 700, cursor: canSubmit ? 'pointer' : 'not-allowed', opacity: canSubmit ? 1 : 0.55, fontFamily: 'inherit', boxShadow: canSubmit ? '0 4px 16px rgba(70,71,211,0.25)' : 'none' }}>
                    {createMut.isPending ? 'Creating…' : 'Create Staff Account'}
                </button>
            </div>
        </AppShell>
    );
}
