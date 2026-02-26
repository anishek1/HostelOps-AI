/**
 * types/user.ts — HostelOps AI
 * TypeScript types mirroring backend Pydantic schemas exactly.
 * When backend schemas change, update this file immediately.
 */

export type UserRole =
    | 'student'
    | 'laundry_man'
    | 'mess_secretary'
    | 'mess_manager'
    | 'assistant_warden'
    | 'warden'
    | 'chief_warden';

export type HostelMode = 'college' | 'autonomous';

export interface UserRead {
    id: string;
    name: string;
    room_number: string;
    role: UserRole;
    hostel_mode: HostelMode;
    is_verified: boolean;
    is_active: boolean;
    created_at: string;
}

export interface UserCreate {
    name: string;
    room_number: string;
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
}
