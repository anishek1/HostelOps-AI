/**
 * pages/student/StudentProfile.tsx — Sprint F
 * Avatar, bento stats, account details, password change, logout.
 */

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import AppShell from '../../components/AppShell';
import { useAuth } from '../../hooks/useAuth';
import client from '../../api/client';

const C = {
    bg: '#0A0A0F',
    primary: '#7C5CFC',
    primaryLight: 'rgba(70,71,211,0.10)',
    primaryContainer: 'rgba(70,71,211,0.12)',
    textPrimary: '#F0F0F5',
    textSecondary: '#6B6B80',
    textMuted: '#6B6B80',
    card: '#13121A',
    danger: '#E83B2A',
    dangerLight: 'rgba(232,59,42,0.10)',
    success: '#1A9B6C',
    successLight: 'rgba(26,155,108,0.10)',
    inputBg: '#F6ECE5',
    border: 'rgba(255,255,255,0.06)',
};

function initials(name: string | undefined) {
    if (!name) return '?'; return name.split(' ').map((w) => w[0]).filter(Boolean).join('').slice(0, 2).toUpperCase();
}

function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
}

interface PasswordForm {
    current_password: string;
    new_password: string;
    confirm_password: string;
}

export default function StudentProfile() {
    const { user, logout } = useAuth();
    const [pwForm, setPwForm] = useState<PasswordForm>({ current_password: '', new_password: '', confirm_password: '' });
    const [pwError, setPwError] = useState<string | null>(null);
    const [pwSuccess, setPwSuccess] = useState(false);
    const [showPw, setShowPw] = useState({ current: false, new: false, confirm: false });

    const passwordMutation = useMutation({
        mutationFn: async (data: { current_password: string; new_password: string }) => {
            await client.patch('/users/me/password', data);
        },
        onSuccess: () => {
            setPwSuccess(true);
            setPwForm({ current_password: '', new_password: '', confirm_password: '' });
            setPwError(null);
            setTimeout(() => setPwSuccess(false), 3000);
        },
        onError: (err) => {
            if (isAxiosError(err)) {
                const detail = err.response?.data?.detail;
                setPwError(typeof detail === 'string' ? detail : 'Incorrect current password.');
            } else {
                setPwError('Could not update password. Try again.');
            }
        },
    });

    function handlePasswordSubmit(e: React.FormEvent) {
        e.preventDefault();
        setPwError(null);
        if (pwForm.new_password !== pwForm.confirm_password) {
            setPwError('New passwords do not match.');
            return;
        }
        if (pwForm.new_password.length < 8) {
            setPwError('Password must be at least 8 characters.');
            return;
        }
        passwordMutation.mutate({
            current_password: pwForm.current_password,
            new_password: pwForm.new_password,
        });
    }

    function handleLogout() {
        logout();
        window.location.replace('/auth/login');
    }

    if (!user) return null;

    const name = user.name;
    const streak = user.feedback_streak ?? 0;

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
                    <h1 style={{ fontSize: 20, fontWeight: 700, color: C.primary, margin: 0 }}>Student Profile</h1>
                    <button
                        style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 22, color: C.primary }}>settings</span>
                    </button>
                </header>

                <div style={{ padding: '0 20px 100px' }}>
                    {/* Avatar + identity */}
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            textAlign: 'center',
                            marginBottom: 28,
                        }}
                    >
                        <div
                            style={{
                                width: 112,
                                height: 112,
                                borderRadius: 32,
                                background: C.primary,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: 34,
                                fontWeight: 800,
                                color: '#fff',
                                marginBottom: 18,
                                boxShadow: '0 4px 20px rgba(70,71,211,0.20)',
                            }}
                        >
                            {initials(name)}
                        </div>
                        <h2 style={{ fontSize: 22, fontWeight: 800, color: C.textPrimary, margin: '0 0 4px' }}>{name}</h2>
                        <p style={{ fontSize: 13, color: C.textSecondary, margin: '0 0 10px' }}>
                            Student · Room {user.room_number}
                        </p>
                        <div
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 5,
                                background: '#1C1B24',
                                padding: '4px 12px',
                                borderRadius: 999,
                            }}
                        >
                            <span className="material-symbols-outlined" style={{ fontSize: 13, color: C.textSecondary }}>calendar_today</span>
                            <span style={{ fontSize: 11, fontWeight: 600, color: C.textSecondary }}>
                                Member since {formatDate(user.created_at)}
                            </span>
                        </div>
                    </div>

                    {/* Bento stats */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 20 }}>
                        {[
                            { label: 'Day Streak', value: streak, primary: false },
                            { label: 'Complaints', value: '—', primary: false },
                            { label: 'Room No', value: user.room_number, primary: true },
                        ].map((s) => (
                            <div
                                key={s.label}
                                style={{
                                    background: s.primary ? C.primary : C.card,
                                    borderRadius: 20,
                                    padding: '14px 10px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: 5,
                                }}
                            >
                                <span style={{ fontSize: 22, fontWeight: 800, color: s.primary ? '#fff' : C.primary }}>{s.value}</span>
                                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: s.primary ? 'rgba(255,255,255,0.75)' : C.textMuted, textAlign: 'center' }}>{s.label}</span>
                            </div>
                        ))}
                    </div>

                    {/* Account details */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 20,
                            padding: '18px 20px',
                            boxShadow: '0 1px 6px rgba(255,255,255,0.03)',
                            marginBottom: 14,
                        }}
                    >
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 14px' }}>
                            Account Details
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                            {[
                                { label: 'Full Name', value: name },
                                { label: 'Room Allocation', value: user.room_number },
                            ].map((row) => (
                                <div key={row.label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                    <span style={{ fontSize: 14, color: C.textSecondary, fontWeight: 500 }}>{row.label}</span>
                                    <span style={{ fontSize: 14, fontWeight: 600, color: C.textPrimary }}>{row.value}</span>
                                </div>
                            ))}
                            {/* Mode */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: 14, color: C.textSecondary, fontWeight: 500 }}>Study Mode</span>
                                <span style={{ fontSize: 11, fontWeight: 700, color: C.primary, background: C.primaryLight, padding: '3px 10px', borderRadius: 999, textTransform: 'capitalize' }}>
                                    {user.hostel_mode}
                                </span>
                            </div>
                            {/* Verification */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: 14, color: C.textSecondary, fontWeight: 500 }}>Verification</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <span className="material-symbols-outlined" style={{ fontSize: 16, color: C.success, fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                                    <span style={{ fontSize: 13, fontWeight: 700, color: C.success }}>Verified</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Security settings */}
                    <div
                        style={{
                            background: C.card,
                            borderRadius: 20,
                            padding: '18px 20px',
                            boxShadow: '0 1px 6px rgba(255,255,255,0.03)',
                            marginBottom: 20,
                        }}
                    >
                        <p style={{ fontSize: 11, fontWeight: 700, color: C.textMuted, letterSpacing: '0.10em', textTransform: 'uppercase', margin: '0 0 16px' }}>
                            Security Settings
                        </p>
                        <form onSubmit={handlePasswordSubmit}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                                {(
                                    [
                                        { field: 'current_password' as const, label: 'Current Password', showKey: 'current' as const },
                                        { field: 'new_password' as const, label: 'New Password', showKey: 'new' as const },
                                        { field: 'confirm_password' as const, label: 'Confirm New Password', showKey: 'confirm' as const },
                                    ]
                                ).map((row) => (
                                    <div key={row.field}>
                                        <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.07em', textTransform: 'uppercase', color: C.textMuted, display: 'block', marginBottom: 6 }}>
                                            {row.label}
                                        </label>
                                        <div
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                background: C.inputBg,
                                                borderRadius: 12,
                                                height: 50,
                                                paddingLeft: 14,
                                            }}
                                        >
                                            <input
                                                type={showPw[row.showKey] ? 'text' : 'password'}
                                                value={pwForm[row.field]}
                                                onChange={(e) => setPwForm((f) => ({ ...f, [row.field]: e.target.value }))}
                                                placeholder="••••••••"
                                                style={{
                                                    flex: 1,
                                                    background: 'transparent',
                                                    border: 'none',
                                                    outline: 'none',
                                                    fontSize: 14,
                                                    color: C.textPrimary,
                                                    fontFamily: 'inherit',
                                                }}
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPw((s) => ({ ...s, [row.showKey]: !s[row.showKey] }))}
                                                style={{ background: 'none', border: 'none', padding: '0 14px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                                            >
                                                <span className="material-symbols-outlined" style={{ fontSize: 18, color: C.textMuted }}>
                                                    {showPw[row.showKey] ? 'visibility_off' : 'visibility'}
                                                </span>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {pwError && <p style={{ fontSize: 12, color: C.danger, margin: '10px 0 0', fontWeight: 500 }}>{pwError}</p>}
                            {pwSuccess && <p style={{ fontSize: 12, color: C.success, margin: '10px 0 0', fontWeight: 500 }}>Password updated successfully!</p>}

                            <button
                                type="submit"
                                disabled={!pwForm.current_password || !pwForm.new_password || !pwForm.confirm_password || passwordMutation.isPending}
                                style={{
                                    width: '100%',
                                    height: 48,
                                    background: C.primary,
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 12,
                                    fontSize: 14,
                                    fontWeight: 700,
                                    cursor: 'pointer',
                                    fontFamily: 'inherit',
                                    marginTop: 14,
                                    opacity: (!pwForm.current_password || !pwForm.new_password || passwordMutation.isPending) ? 0.55 : 1,
                                }}
                            >
                                {passwordMutation.isPending ? 'Updating…' : 'Update Security Credentials'}
                            </button>
                        </form>
                    </div>

                    {/* Logout */}
                    <button
                        onClick={handleLogout}
                        style={{
                            width: '100%',
                            height: 52,
                            background: C.dangerLight,
                            color: C.danger,
                            border: 'none',
                            borderRadius: 14,
                            fontSize: 15,
                            fontWeight: 700,
                            cursor: 'pointer',
                            fontFamily: 'inherit',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: 8,
                        }}
                    >
                        <span className="material-symbols-outlined" style={{ fontSize: 20 }}>logout</span>
                        Sign out
                    </button>
                </div>
            </div>
        </AppShell>
    );
}
