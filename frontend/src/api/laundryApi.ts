/**
 * api/laundryApi.ts — HostelOps AI
 * Laundry slot booking and machine management for students.
 */

import type { LaundrySlotRead, MachineRead } from '../types/laundry';
import client from './client';

export interface SlotBookingRequest {
    machine_id: string;
    slot_date: string; // YYYY-MM-DD
    slot_time: string; // HH:MM
}

export interface DaySlot {
    slot_time: string;       // "08:00"
    machine_id: string;
    is_available: boolean;
    is_yours: boolean;
    booking_id?: string;
    machine_status?: 'active' | 'repair';
}

export async function getMachines(): Promise<MachineRead[]> {
    const res = await client.get<MachineRead[]>('/laundry/machines');
    return res.data;
}

export async function getDaySlots(slot_date: string): Promise<DaySlot[]> {
    const res = await client.get<DaySlot[]>('/laundry/slots', { params: { slot_date } });
    return res.data;
}

export async function getMyBookings(): Promise<LaundrySlotRead[]> {
    const res = await client.get<LaundrySlotRead[]>('/laundry/my-bookings');
    return res.data;
}

export async function bookSlot(data: SlotBookingRequest): Promise<LaundrySlotRead> {
    const res = await client.post<LaundrySlotRead>('/laundry/slots/book', data);
    return res.data;
}

export async function cancelBooking(id: string): Promise<void> {
    await client.delete(`/laundry/slots/${id}`);
}
