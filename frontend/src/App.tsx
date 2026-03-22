/**
 * App.tsx — HostelOps AI
 * Root component: AuthProvider + QueryClientProvider + all 23 routes.
 * Every protected route uses ProtectedRoute with explicit allowedRoles.
 * All page components are lazy-loaded for code splitting.
 */

import { Suspense, lazy } from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './lib/ProtectedRoute';
import {
    STUDENT_ROLES,
    WARDEN_ROLES,
    LAUNDRY_STAFF_ROLES,
    MESS_STAFF_ROLES,
} from './lib/rolePermissions';

// ── Lazy page imports ─────────────────────────────────────────────────────────

// Auth (public)
const Landing             = lazy(() => import('./pages/auth/Landing'));
const Login               = lazy(() => import('./pages/auth/Login'));
const Register            = lazy(() => import('./pages/auth/Register'));
const HostelSetup         = lazy(() => import('./pages/auth/HostelSetup'));
const RegistrationPending = lazy(() => import('./pages/auth/RegistrationPending'));
const RegistrationRejected = lazy(() => import('./pages/auth/RegistrationRejected'));

// Student
const StudentHome         = lazy(() => import('./pages/student/StudentHome'));
const Onboarding          = lazy(() => import('./pages/student/Onboarding'));
const ComplaintTracker    = lazy(() => import('./pages/student/ComplaintTracker'));
const FileComplaint       = lazy(() => import('./pages/student/FileComplaint'));
const ComplaintDetail     = lazy(() => import('./pages/student/ComplaintDetail'));
const ComplaintResolvedSuccess = lazy(() => import('./pages/student/ComplaintResolvedSuccess'));
const LaundryBooking      = lazy(() => import('./pages/student/LaundryBooking'));
const MessPage            = lazy(() => import('./pages/student/MessPage'));
const NotificationInbox   = lazy(() => import('./pages/student/NotificationInbox'));
const StudentProfile      = lazy(() => import('./pages/student/StudentProfile'));

// Warden
const WardenDashboard     = lazy(() => import('./pages/warden/WardenDashboard'));
const ApprovalQueue       = lazy(() => import('./pages/warden/ApprovalQueue'));
const StudentRegistrations = lazy(() => import('./pages/warden/StudentRegistrations'));
const CreateStaffAccount  = lazy(() => import('./pages/warden/CreateStaffAccount'));
const ComplaintManagement = lazy(() => import('./pages/warden/ComplaintManagement'));
const HostelSettings      = lazy(() => import('./pages/warden/HostelSettings'));

// Staff
const LaundryManView      = lazy(() => import('./pages/staff/LaundryManView'));
const MessStaffView       = lazy(() => import('./pages/staff/MessStaffView'));

// ── TanStack Query client ─────────────────────────────────────────────────────

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 30,       // 30 seconds
            retry: 1,
        },
    },
});

// ── Minimal Suspense fallback (warm cream — no spinners) ──────────────────────

function PageFallback() {
    return <div style={{ minHeight: '100dvh', background: '#FFF5EE' }} />;
}

// ── Route declarations ────────────────────────────────────────────────────────

function AppRoutes() {
    return (
        <Suspense fallback={<PageFallback />}>
            <Routes>
                {/* ── Public ── */}
                <Route path="/auth/landing"   element={<Landing />} />
                <Route path="/auth/login"     element={<Login />} />
                <Route path="/auth/register"  element={<Register />} />
                <Route path="/auth/hostel-setup" element={<HostelSetup />} />
                <Route path="/auth/pending"   element={<RegistrationPending />} />
                <Route path="/auth/rejected"  element={<RegistrationRejected />} />

                {/* ── Student ── */}
                <Route
                    path="/student"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <StudentHome />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/onboarding"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <Onboarding />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/complaints"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <ComplaintTracker />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/complaints/new"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <FileComplaint />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/complaints/:id"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <ComplaintDetail />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/complaints/:id/resolved"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <ComplaintResolvedSuccess />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/laundry"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <LaundryBooking />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/mess"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <MessPage />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/notifications"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <NotificationInbox />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/student/profile"
                    element={
                        <ProtectedRoute allowedRoles={STUDENT_ROLES}>
                            <StudentProfile />
                        </ProtectedRoute>
                    }
                />

                {/* ── Warden ── */}
                <Route
                    path="/warden"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <WardenDashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/warden/approval-queue"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <ApprovalQueue />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/warden/registrations"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <StudentRegistrations />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/warden/staff/new"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <CreateStaffAccount />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/warden/complaints"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <ComplaintManagement />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/warden/settings"
                    element={
                        <ProtectedRoute allowedRoles={WARDEN_ROLES}>
                            <HostelSettings />
                        </ProtectedRoute>
                    }
                />

                {/* ── Staff ── */}
                <Route
                    path="/staff/laundry"
                    element={
                        <ProtectedRoute allowedRoles={LAUNDRY_STAFF_ROLES}>
                            <LaundryManView />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/staff/mess"
                    element={
                        <ProtectedRoute allowedRoles={MESS_STAFF_ROLES}>
                            <MessStaffView />
                        </ProtectedRoute>
                    }
                />

                {/* ── Default redirects ── */}
                <Route path="/" element={<Navigate to="/auth/landing" replace />} />
                <Route path="*" element={<Navigate to="/auth/landing" replace />} />
            </Routes>
        </Suspense>
    );
}

// ── Root ──────────────────────────────────────────────────────────────────────

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <AuthProvider>
                    <AppRoutes />
                </AuthProvider>
            </Router>
        </QueryClientProvider>
    );
}
