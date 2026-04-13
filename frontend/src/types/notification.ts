/**
 * types/notification.ts — HostelOps AI
 * TypeScript types mirroring backend notification schemas.
 */

export type NotificationType =
    | 'complaint_assigned'
    | 'approval_needed'
    | 'mess_alert'
    | 'laundry_reminder'
    | 'machine_down'
    | 'complaint_resolved'
    | 'registration_pending'
    | 'complaint_escalated'
    | 'complaint_reopened'
    | 'registration_approved'
    | 'registration_rejected'
    | 'password_reset'
    | 'account_deactivated';

export interface NotificationRead {
    id: string;
    recipient_id: string;
    title: string;
    body: string;
    type: NotificationType;
    is_read: boolean;
    created_at: string;
}
