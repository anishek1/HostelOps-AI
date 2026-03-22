/**
 * api/notificationsApi.ts — HostelOps AI
 * Notification inbox for students.
 */

import type { NotificationRead } from '../types/notification';
import client from './client';

export async function getNotifications(): Promise<NotificationRead[]> {
    const res = await client.get<NotificationRead[]>('/notifications/');
    return res.data;
}

export async function markRead(id: string): Promise<void> {
    await client.patch(`/notifications/${id}/read`);
}

export async function markAllRead(): Promise<void> {
    await client.patch('/notifications/read-all');
}
