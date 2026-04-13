/**
 * api/complaintsApi.ts — HostelOps AI
 * Student complaint CRUD and state-machine actions.
 */

import type { ComplaintCreate, ComplaintRead } from '../types/complaint';
import client from './client';

export interface ComplaintTemplate {
    title: string;
    description: string;
    category: string;
}

export interface TimelineEntry {
    status: string;
    changed_at: string;
    changed_by: string | null;
    note: string | null;
}

export async function getMyComplaints(): Promise<ComplaintRead[]> {
    const res = await client.get<ComplaintRead[]>('/complaints/my');
    return res.data;
}

export async function getComplaint(id: string): Promise<ComplaintRead> {
    const res = await client.get<ComplaintRead>(`/complaints/${id}`);
    return res.data;
}

export async function getComplaintTimeline(id: string): Promise<TimelineEntry[]> {
    const res = await client.get<TimelineEntry[]>(`/complaints/${id}/timeline`);
    return res.data;
}

export async function getComplaintTemplates(): Promise<ComplaintTemplate[]> {
    const res = await client.get<ComplaintTemplate[]>('/complaints/templates');
    return res.data;
}

export interface ComplaintCreatedResponse {
    complaint_id: string;
    status: string;
    message: string;
}

export async function fileComplaint(data: ComplaintCreate): Promise<ComplaintCreatedResponse> {
    const res = await client.post<ComplaintCreatedResponse>('/complaints/', data);
    return res.data;
}

export async function confirmResolved(id: string): Promise<ComplaintCreatedResponse> {
    const res = await client.post<ComplaintCreatedResponse>(`/complaints/${id}/confirm`);
    return res.data;
}

export async function reopenComplaint(id: string): Promise<ComplaintCreatedResponse> {
    const res = await client.post<ComplaintCreatedResponse>(`/complaints/${id}/reopen`, { reason: '' });
    return res.data;
}
