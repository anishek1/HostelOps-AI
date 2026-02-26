/**
 * lib/rolePermissions.ts — HostelOps AI
 * Centralised role → allowed routes mapping.
 * All role checks must reference this file — never hardcode role strings in components.
 */

import type { UserRole } from '../types/user';

/** Maps each role to the default dashboard path after login. */
export const ROLE_DEFAULT_ROUTE: Record<UserRole, string> = {
    student: '/student',
    laundry_man: '/laundry-staff',
    mess_secretary: '/mess-staff',
    mess_manager: '/mess-manager',
    assistant_warden: '/warden',
    warden: '/warden',
    chief_warden: '/warden',
};

/** Roles that have access to the Warden Dashboard. */
export const WARDEN_ROLES: UserRole[] = [
    'assistant_warden',
    'warden',
    'chief_warden',
];

/** Roles that have access to student-facing pages. */
export const STUDENT_ROLES: UserRole[] = ['student'];

/** Check if a role has warden-level access. */
export function isWardenRole(role: UserRole): boolean {
    return WARDEN_ROLES.includes(role);
}

/** Get the redirect path after login based on role. */
export function getDefaultRoute(role: UserRole): string {
    return ROLE_DEFAULT_ROUTE[role] ?? '/';
}
