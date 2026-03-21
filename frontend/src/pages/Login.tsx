/**
 * pages/Login.tsx — HostelOps AI
 * Login page using Shadcn/UI form components.
 * Calls authApi.login(), stores token via AuthContext, then redirects by role.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getDefaultRoute } from '../lib/rolePermissions';

export default function Login() {
    const { login, isAuthenticated, user } = useAuth();
    const navigate = useNavigate();
    const [roomNumber, setRoomNumber] = useState('');
    const [password, setPassword] = useState('');
    const [hostelCode, setHostelCode] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    // If already authenticated, redirect immediately
    if (isAuthenticated && user) {
        navigate(getDefaultRoute(user.role), { replace: true });
        return null;
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await login({ room_number: roomNumber, password, hostel_code: hostelCode });
            // After login, user and role are available — redirect based on role
            // We need to read fresh from auth context after state update
            // navigate() is called in the effect when user is set
        } catch (err: unknown) {
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError('Login failed. Please check your room number and password.');
            }
        } finally {
            setLoading(false);
        }
    }

    // Redirect after successful login (user state just set)
    if (isAuthenticated && user) {
        navigate(getDefaultRoute(user.role), { replace: true });
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="w-full max-w-md bg-white rounded-2xl shadow-md p-8 space-y-6">
                {/* Header */}
                <div className="text-center space-y-1">
                    <h1 className="text-2xl font-bold text-gray-900">HostelOps AI</h1>
                    <p className="text-sm text-gray-500">Sign in to your account</p>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Hostel Code */}
                    <div className="space-y-1">
                        <label
                            htmlFor="hostel_code"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Hostel Code
                        </label>
                        <input
                            id="hostel_code"
                            type="text"
                            autoComplete="organization"
                            required
                            value={hostelCode}
                            onChange={(e) => setHostelCode(e.target.value)}
                            placeholder="e.g. BH1"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Room Number */}
                    <div className="space-y-1">
                        <label
                            htmlFor="room_number"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Room Number
                        </label>
                        <input
                            id="room_number"
                            type="text"
                            autoComplete="username"
                            required
                            value={roomNumber}
                            onChange={(e) => setRoomNumber(e.target.value)}
                            placeholder="e.g. A-204"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Password */}
                    <div className="space-y-1">
                        <label
                            htmlFor="password"
                            className="block text-sm font-medium text-gray-700"
                        >
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </div>

                    {/* Error message */}
                    {error && (
                        <div
                            role="alert"
                            className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2"
                        >
                            {error}
                        </div>
                    )}

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
                    >
                        {loading ? 'Signing in…' : 'Sign In'}
                    </button>
                </form>

                <p className="text-center text-xs text-gray-400">
                    Don&apos;t have an account? Contact your hostel administration.
                </p>
            </div>
        </div>
    );
}
