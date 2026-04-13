/**
 * types/complaint.ts — HostelOps AI
 * TypeScript types mirroring backend complaint schemas and enums.
 */

export type ComplaintCategory =
    | 'mess'
    | 'laundry'
    | 'maintenance'
    | 'interpersonal'
    | 'critical'
    | 'uncategorised';

export type ComplaintSeverity = 'low' | 'medium' | 'high';

export type ComplaintStatus =
    | 'INTAKE'
    | 'CLASSIFIED'
    | 'AWAITING_APPROVAL'
    | 'ASSIGNED'
    | 'IN_PROGRESS'
    | 'RESOLVED'
    | 'REOPENED'
    | 'ESCALATED';

export type ClassifiedBy = 'llm' | 'fallback' | 'manual' | 'warden_override';

export type OverrideReason =
    | 'wrong_category'
    | 'wrong_assignee'
    | 'wrong_severity'
    | 'other';

export type ApprovalStatus = 'pending' | 'approved' | 'corrected';

export interface ComplaintCreate {
    text: string;
    is_anonymous?: boolean;
}

export interface ComplaintRead {
    id: string;
    hostel_id: string;
    student_id: string;
    text: string;
    is_anonymous: boolean;
    category: ComplaintCategory | null;
    severity: ComplaintSeverity | null;
    status: ComplaintStatus;
    assigned_to: string | null;
    confidence_score: number | null;
    ai_suggested_category: ComplaintCategory | null;
    ai_suggested_severity: ComplaintSeverity | null;
    ai_suggested_assignee: string | null;
    requires_approval: boolean;
    classified_by: ClassifiedBy | null;
    classification_note: string | null;
    override_reason: OverrideReason | null;
    override_note: string | null;
    flagged_input: string | null;
    resolved_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface ApprovalQueueItemRead {
    id: string;
    complaint_id: string;
    ai_suggested_category: ComplaintCategory;
    ai_suggested_severity: ComplaintSeverity;
    ai_suggested_assignee: string;
    confidence_score: number;
    status: ApprovalStatus;
    reviewed_by: string | null;
    override_reason: string | null;
    created_at: string;
    reviewed_at: string | null;
}
