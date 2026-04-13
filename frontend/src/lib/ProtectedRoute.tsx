/**
 * lib/ProtectedRoute.tsx — HostelOps AI
 * Route guard: redirects to /auth/login if unauthenticated,
 * redirects to role default home if wrong role.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { UserRole } from '../types/user';
import { getDefaultRoute } from './rolePermissions';

interface Props {
    children: React.ReactNode;
    allowedRoles?: UserRole[];
}

export default function ProtectedRoute({ children, allowedRoles }: Props) {
    const { isAuthenticated, isLoading, user } = useAuth();

    if (isLoading) {
        // Minimal loading state — SkeletonCard not used here to avoid circular deps
        return (
            <div
                style={{ minHeight: '100dvh', background: '#0A0A0F' }}
                aria-busy="true"
            />
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/auth/login" replace />;
    }

    if (allowedRoles && user && !allowedRoles.includes(user.role)) {
        return <Navigate to={getDefaultRoute(user.role)} replace />;
    }

    return <>{children}</>;
}
