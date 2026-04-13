/**
 * api/wardenApi.ts — HostelOps AI
 * Warden-specific endpoints: registrations, notices, analytics, complaint management.
 */

import api from './client';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface PendingRegistration {
    id: string;
    name: string;
    room_number: string;
    hostel_mode: 'college' | 'autonomous';
    roll_number?: string | null;
    erp_document_url?: string | null;
    created_at: string;
    is_verified: boolean;
    is_rejected: boolean;
    rejection_reason?: string | null;
    // derived — not from backend
    status: 'pending' | 'approved' | 'rejected';
}

function deriveStatus(u: { is_verified: boolean; is_rejected: boolean }): 'pending' | 'approved' | 'rejected' {
    if (u.is_rejected) return 'rejected';
    if (u.is_verified) return 'approved';
    return 'pending';
}

export interface Notice {
    id: string;
    hostel_id: string;
    title: string;
    body: string;
    priority: 'low' | 'medium' | 'high';
    created_by: string;
    created_at: string;
}

export interface WardenComplaint {
    id: string;
    text: string;
    category?: string;
    severity?: string;
    status: string;
    is_anonymous: boolean;
    assigned_to?: string;
    student_id?: string;
    created_at: string;
    updated_at: string;
}

export interface WardenAnalytics {
    total_complaints: number;
    resolved_count: number;
    pending_count: number;
    escalated_count: number;
    resolution_rate: number;
    avg_resolution_hours: number;
    misclassification_rate: number;
    false_severity_rate: number;
    queue_latency_minutes: number;
    override_rate_by_category: Record<string, number>;
    mess_participation_rate: number;
    laundry_noshow_rate: number;
}

export interface StaffMember {
    id: string;
    name: string;
    room_number?: string;
    role: string;
    created_at: string;
}

// ── Registrations ─────────────────────────────────────────────────────────────

export async function getPendingRegistrations(): Promise<PendingRegistration[]> {
    const { data } = await api.get('/users', { params: { is_verified: false } });
    return data.map((u: PendingRegistration) => ({ ...u, status: deriveStatus(u) }));
}

export async function getAllRegistrations(): Promise<PendingRegistration[]> {
    const { data } = await api.get('/users');
    return data.map((u: PendingRegistration) => ({ ...u, status: deriveStatus(u) }));
}

export async function approveRegistration(userId: string): Promise<void> {
    await api.post(`/users/${userId}/verify`);
}

export async function rejectRegistration(userId: string, reason: string): Promise<void> {
    await api.post(`/users/${userId}/reject`, { reason });
}

// ── Notices ───────────────────────────────────────────────────────────────────

export async function getNotices(): Promise<Notice[]> {
    const { data } = await api.get('/notices/');
    return data;
}

export async function postNotice(title: string, body: string): Promise<Notice> {
    const { data } = await api.post('/notices/', { title, body });
    return data;
}

export async function deleteNotice(id: string): Promise<void> {
    await api.delete(`/notices/${id}`);
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function getWardenAnalytics(): Promise<WardenAnalytics> {
    const { data } = await api.get('/analytics/dashboard');
    return data;
}

// ── Complaint management (warden) ─────────────────────────────────────────────

export async function getWardenComplaints(params?: {
    status?: string;
    category?: string;
    severity?: string;
}): Promise<WardenComplaint[]> {
    const { data } = await api.get('/complaints', { params });
    return data;
}

export async function updateComplaintStatus(
    id: string,
    status: string,
    note?: string,
): Promise<void> {
    await api.patch(`/complaints/${id}/status`, { status, note });
}

export async function escalateComplaint(id: string, reason: string): Promise<void> {
    await api.post(`/complaints/${id}/escalate`, { reason });
}

// ── Staff ─────────────────────────────────────────────────────────────────────

export async function getStaffMembers(): Promise<StaffMember[]> {
    const { data } = await api.get('/users/staff');
    return data;
}

export async function createStaffAccount(payload: {
    name: string;
    room_number: string;
    role: string;
    password: string;
    hostel_mode?: string;
}): Promise<StaffMember> {
    const { data } = await api.post('/users/staff', payload);
    return data;
}

export async function deleteStaffAccount(userId: string): Promise<void> {
    await api.delete(`/users/${userId}/deactivate`);
}
