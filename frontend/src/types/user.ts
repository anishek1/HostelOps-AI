/**
 * types/user.ts — HostelOps AI
 * TypeScript types mirroring backend Pydantic schemas exactly.
 * When backend schemas change, update this file immediately.
 */

// Must match backend schemas/enums.py UserRole exactly
export type UserRole =
    | 'student'
    | 'laundry_man'
    | 'mess_staff'
    | 'warden';

export type HostelMode = 'college' | 'autonomous';

// ── Hostel schemas (mirrors backend/schemas/hostel.py) ────────────────────────

export interface HostelPublicInfo {
    name: string;
    mode: HostelMode;
    code: string;
}

export interface HostelRead {
    id: string;
    name: string;
    code: string;
    mode: HostelMode;
    total_floors: number;
    total_students_capacity: number;
    created_at: string;
}

export interface HostelSetupRequest {
    hostel_name: string;
    hostel_mode: HostelMode;
    total_floors: number;
    total_students_capacity: number;
    warden_name: string;
    warden_room_number: string;
    warden_password: string;
}

export interface HostelSetupResponse {
    hostel: HostelRead;
    access_token: string;
    refresh_token: string;
    token_type: string;
}

// ── User schemas (mirrors backend/schemas/user.py) ────────────────────────────

export interface UserRead {
    id: string;
    name: string;
    room_number: string;
    role: UserRole;
    hostel_mode: HostelMode;
    is_verified: boolean;
    is_active: boolean;
    is_rejected: boolean;
    rejection_reason: string | null;
    has_seen_onboarding: boolean;
    feedback_streak: number;
    created_at: string;
}

export interface LoginResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
    user: UserRead;
}

export interface UserCreate {
    name: string;
    room_number: string;
    hostel_code: string;
    role: UserRole;
    hostel_mode: HostelMode;
    password: string;
    roll_number?: string;
    erp_document_url?: string;
}

export interface UserUpdate {
    name?: string;
    room_number?: string;
}

export interface Token {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface LoginRequest {
    room_number: string;
    password: string;
    hostel_code: string;
}
