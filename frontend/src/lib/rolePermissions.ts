/**
 * lib/rolePermissions.ts — HostelOps AI
 * Centralised role → routes mapping.
 * All role checks must reference this file — never hardcode role strings in components.
 */

import type { UserRole } from '../types/user';

// ── Role groups ───────────────────────────────────────────────────────────────

export const WARDEN_ROLES: UserRole[] = ['warden'];

export const STUDENT_ROLES: UserRole[] = ['student'];

export const LAUNDRY_STAFF_ROLES: UserRole[] = ['laundry_man'];

export const MESS_STAFF_ROLES: UserRole[] = ['mess_staff'];

export const STAFF_ROLES: UserRole[] = [...LAUNDRY_STAFF_ROLES, ...MESS_STAFF_ROLES];

// ── Route lists ───────────────────────────────────────────────────────────────

export const STUDENT_ROUTES = [
    '/student',
    '/student/onboarding',
    '/student/complaints',
    '/student/complaints/new',
    '/student/laundry',
    '/student/mess',
    '/student/notifications',
    '/student/profile',
];

export const WARDEN_ROUTES = [
    '/warden',
    '/warden/approval-queue',
    '/warden/registrations',
    '/warden/staff/new',
    '/warden/complaints',
    '/warden/settings',
];

export const STAFF_ROUTES = [
    '/staff/laundry',
    '/staff/mess',
];

// ── Default redirect after login ──────────────────────────────────────────────

export const ROLE_DEFAULT_ROUTE: Record<UserRole, string> = {
    student:     '/student',
    laundry_man: '/staff/laundry',
    mess_staff:  '/staff/mess',
    warden:      '/warden',
};

export function getDefaultRoute(role: UserRole): string {
    return ROLE_DEFAULT_ROUTE[role] ?? '/auth/login';
}

// ── Role predicates ───────────────────────────────────────────────────────────

export function isWardenRole(role: UserRole): boolean {
    return WARDEN_ROLES.includes(role);
}

export function isStaffRole(role: UserRole): boolean {
    return STAFF_ROLES.includes(role);
}
