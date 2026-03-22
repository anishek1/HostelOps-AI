/**
 * components/AppShell.tsx — HostelOps AI
 * Wraps all authenticated screens. Renders the correct bottom nav for user.role.
 * Content area has padding-bottom to clear the 64px fixed nav.
 */

import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { isWardenRole, isStaffRole } from '../lib/rolePermissions';
import StudentBottomNav from './StudentBottomNav';
import WardenBottomNav from './WardenBottomNav';
import StaffBottomNav from './StaffBottomNav';

interface Props {
    children: React.ReactNode;
    /** Set true on pages that have their own sticky CTA button above the nav */
    hasStickyCta?: boolean;
}

export default function AppShell({ children, hasStickyCta = false }: Props) {
    const { user } = useAuth();

    function renderNav() {
        if (!user) return null;
        if (isWardenRole(user.role)) return <WardenBottomNav />;
        if (isStaffRole(user.role)) return <StaffBottomNav role={user.role} />;
        return <StudentBottomNav />;
    }

    return (
        <div
            style={{
                minHeight: '100dvh',
                background: '#FFF5EE',
                display: 'flex',
                flexDirection: 'column',
            }}
        >
            <main
                style={{
                    flex: 1,
                    paddingBottom: hasStickyCta ? 120 : 64,
                }}
            >
                {children}
            </main>
            {renderNav()}
        </div>
    );
}
