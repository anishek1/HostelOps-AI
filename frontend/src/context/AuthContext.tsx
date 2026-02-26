/**
 * context/AuthContext.tsx — HostelOps AI
 * Manages authentication state: current user, JWT token, login/logout.
 * Restores session from localStorage on app load.
 */

import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import { getMe, login as apiLogin } from '../api/authApi';
import type { LoginRequest, UserRead, UserRole } from '../types/user';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface AuthState {
    user: UserRead | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
}

interface AuthContextValue extends AuthState {
    login: (credentials: LoginRequest) => Promise<void>;
    logout: () => void;
    hasRole: (...roles: UserRole[]) => boolean;
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const AuthContext = createContext<AuthContextValue | null>(null);

// No local storage definitions needed// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<UserRead | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false); // No need to load from local storage

    const login = useCallback(async (credentials: LoginRequest) => {
        setIsLoading(true);
        try {
            const tokenData = await apiLogin(credentials);
            const accessToken = tokenData.access_token;
            setToken(accessToken);



            const userProfile = await getMe(accessToken);
            setUser(userProfile);
        } finally {
            setIsLoading(false);
        }
    }, []);

    const logout = useCallback(() => {
        setToken(null);
        setUser(null);
    }, []);

    const hasRole = useCallback(
        (...roles: UserRole[]) => {
            if (!user) return false;
            return roles.includes(user.role);
        },
        [user],
    );

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            token,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            hasRole,
        }),
        [user, token, isLoading, login, logout, hasRole],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ---------------------------------------------------------------------------
// Hook (internal — use useAuth.ts externally)
// ---------------------------------------------------------------------------

export function useAuthContext(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider');
    return ctx;
}

export default AuthContext;
