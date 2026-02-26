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

const TOKEN_KEY = 'hostelops_token';

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<UserRead | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Restore session on mount
    useEffect(() => {
        const stored = localStorage.getItem(TOKEN_KEY);
        if (stored) {
            getMe(stored)
                .then((u) => {
                    setToken(stored);
                    setUser(u);
                })
                .catch(() => {
                    localStorage.removeItem(TOKEN_KEY);
                })
                .finally(() => setIsLoading(false));
        } else {
            setIsLoading(false);
        }
    }, []);

    const login = useCallback(async (credentials: LoginRequest) => {
        const tokenData = await apiLogin(credentials);
        const accessToken = tokenData.access_token;
        const userProfile = await getMe(accessToken);
        localStorage.setItem(TOKEN_KEY, accessToken);
        setToken(accessToken);
        setUser(userProfile);
    }, []);

    const logout = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
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
