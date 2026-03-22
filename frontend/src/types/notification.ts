/**
 * types/notification.ts — HostelOps AI
 * TypeScript types mirroring backend notification schemas.
 */

export type NotificationType =
    | 'complaint_update'
    | 'laundry_reminder'
    | 'mess_alert'
    | 'approval'
    | 'system';

export interface NotificationRead {
    id: string;
    user_id: string;
    title: string;
    body: string;
    notification_type: NotificationType;
    is_read: boolean;
    created_at: string;
}
