/**
 * types/laundry.ts — HostelOps AI
 * TypeScript types mirroring backend laundry slot and machine schemas.
 */

export type SlotStatus = 'available' | 'booked' | 'cancelled' | 'completed' | 'no_show';

export interface LaundrySlotCreate {
    machine_id: string;
    slot_date: string; // YYYY-MM-DD
    slot_time: string; // HH:MM
}

export interface LaundrySlotRead {
    id: string;
    machine_id: string;
    student_id: string | null;
    slot_date: string;
    slot_time: string;
    booking_status: SlotStatus;
    priority_score: number | null;
    booked_at: string | null;
    completed_at: string | null;
    created_at: string;
}

export interface MachineRead {
    id: string;
    name: string;
    floor: number | null;
    status: string;
    is_active: boolean;
    last_reported_issue: string | null;
    created_at: string;
}
