/**
 * api/hostelSettingsApi.ts — HostelOps AI
 * Hostel configuration get/update endpoints.
 * Field names match the backend HostelConfigRead schema exactly.
 */

import api from './client';

export interface HostelConfig {
    id: string;
    hostel_code: string | null;
    hostel_name: string;
    hostel_mode: string;
    total_floors: number;
    total_students_capacity: number;
    complaint_rate_limit: number;
    approval_queue_timeout_minutes: number;
    complaint_confidence_threshold: number;
    mess_alert_threshold: number;
    mess_critical_threshold: number;
    mess_min_participation: number;
    mess_min_responses: number;
    laundry_slots_start_hour: number;
    laundry_slots_end_hour: number;
    laundry_slot_duration_hours: number;
    laundry_noshow_penalty_hours: number;
    laundry_cancellation_deadline_minutes: number;
    created_at: string;
    updated_at: string | null;
}

export type HostelConfigUpdate = Partial<Omit<HostelConfig, 'id' | 'created_at' | 'updated_at'>>;

export async function getHostelConfig(): Promise<HostelConfig> {
    const { data } = await api.get('/config');
    return data;
}

export async function updateHostelConfig(patch: HostelConfigUpdate): Promise<HostelConfig> {
    const { data } = await api.patch('/config', patch);
    return data;
}
