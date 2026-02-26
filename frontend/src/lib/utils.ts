/**
 * lib/utils.ts — HostelOps AI
 * General utility functions. Includes shadcn/ui's cn() helper.
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/** Merge Tailwind CSS classes safely (shadcn/ui pattern). */
export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/** Format an ISO date string to a readable format. */
export function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
    });
}

/** Format an ISO datetime string to a readable format. */
export function formatDateTime(iso: string): string {
    return new Date(iso).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}
