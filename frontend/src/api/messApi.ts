/**
 * api/messApi.ts — HostelOps AI
 * Mess menu, feedback submission, and history.
 */

import type { MessFeedbackCreate, MessFeedbackRead, MealPeriod } from '../types/mess';
import client from './client';

export interface MessMenuItem {
    id: string;
    date: string;
    meal: MealPeriod;
    items: string[];
    posted_by: string;
    created_at: string;
}

export async function getMessMenu(date: string): Promise<MessMenuItem[]> {
    const res = await client.get<MessMenuItem[]>('/mess/menu', { params: { date } });
    return res.data;
}

export async function submitFeedback(data: MessFeedbackCreate): Promise<MessFeedbackRead> {
    const res = await client.post<MessFeedbackRead>('/mess/feedback', data);
    return res.data;
}

export async function getMyFeedback(): Promise<MessFeedbackRead[]> {
    const res = await client.get<MessFeedbackRead[]>('/mess/my-feedback');
    return res.data;
}
