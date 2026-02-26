/**
 * App.tsx — HostelOps AI
 * Root component: provides AuthContext and declares all routes.
 * Protected routes redirect to /login if not authenticated.
 */

import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth';
import ApprovalQueue from './pages/ApprovalQueue';
import LaundryBooking from './pages/LaundryBooking';
import Login from './pages/Login';
import MessFeedback from './pages/MessFeedback';
import StudentDashboard from './pages/StudentDashboard';
import WardenDashboard from './pages/WardenDashboard';

// ---------------------------------------------------------------------------
// ProtectedRoute — redirects to /login if not authenticated
// ---------------------------------------------------------------------------
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500 text-sm">Loading…</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// ---------------------------------------------------------------------------
// AppRoutes — all routes declared here
// ---------------------------------------------------------------------------
function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />

      {/* Student */}
      <Route
        path="/student"
        element={
          <ProtectedRoute>
            <StudentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/laundry"
        element={
          <ProtectedRoute>
            <LaundryBooking />
          </ProtectedRoute>
        }
      />
      <Route
        path="/student/mess"
        element={
          <ProtectedRoute>
            <MessFeedback />
          </ProtectedRoute>
        }
      />

      {/* Warden */}
      <Route
        path="/warden"
        element={
          <ProtectedRoute>
            <WardenDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/warden/approval-queue"
        element={
          <ProtectedRoute>
            <ApprovalQueue />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

// ---------------------------------------------------------------------------
// App — root export
// ---------------------------------------------------------------------------
export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}
