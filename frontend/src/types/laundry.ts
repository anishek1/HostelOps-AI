/**
 * types/laundry.ts — HostelOps AI
 * TypeScript types mirroring backend laundry slot and machine schemas.
 */

export type SlotStatus = 'booked' | 'cancelled' | 'completed' | 'no_show';

export interface LaundrySlotCreate {
    machine_id: string;
    date: string; // ISO date: YYYY-MM-DD
    start_time: string; // HH:MM
    end_time: string; // HH:MM
}

export interface LaundrySlotRead {
    id: string;
    machine_id: string;
    student_id: string;
    date: string;
    start_time: string;
    end_time: string;
    status: SlotStatus;
    is_priority: boolean;
    priority_reason: string | null;
    priority_approved_by: string | null;
    created_at: string;
}

export interface MachineRead {
    id: string;
    name: string;
    is_active: boolean;
    last_reported_issue: string | null;
    repaired_at: string | null;
    created_at: string;
}
