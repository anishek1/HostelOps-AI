/**
 * context/AuthContext.tsx — HostelOps AI
 * Authentication state: tokens in localStorage, user in memory.
 * On mount: restores session from localStorage via GET /users/me.
 * login() stores both tokens; logout() clears storage and state.
 * setSession() allows external flows (hostel setup) to inject a session.
 */

import React, {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from 'react';
import { getMe, login as apiLogin, logout as apiLogout } from '../api/authApi';
import type { LoginRequest, UserRead, UserRole } from '../types/user';

// ── Types ────────────────────────────────────────────────────────────────────

interface AuthContextValue {
    user: UserRead | null;
    accessToken: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (credentials: LoginRequest) => Promise<void>;
    logout: () => Promise<void>;
    setSession: (accessToken: string, refreshToken: string, user: UserRead) => void;
    hasRole: (...roles: UserRole[]) => boolean;
}

// ── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext<AuthContextValue | null>(null);

// ── Storage helpers ──────────────────────────────────────────────────────────

function storeTokens(access: string, refresh: string) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<UserRead | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Restore session on mount
    useEffect(() => {
        const stored = localStorage.getItem('access_token');
        if (!stored) {
            setIsLoading(false);
            return;
        }
        getMe()
            .then((profile) => {
                setUser(profile);
                setAccessToken(stored);
            })
            .catch(() => {
                clearTokens();
            })
            .finally(() => setIsLoading(false));
    }, []);

    const login = useCallback(async (credentials: LoginRequest) => {
        const data = await apiLogin(credentials);
        storeTokens(data.access_token, data.refresh_token);
        setAccessToken(data.access_token);
        setUser(data.user);
    }, []);

    const logout = useCallback(async () => {
        try {
            await apiLogout();
        } catch {
            // Ignore — server may already have invalidated token
        } finally {
            clearTokens();
            setAccessToken(null);
            setUser(null);
        }
    }, []);

    // Used by flows that receive tokens without going through login() —
    // e.g. hostel setup, which returns tokens directly in its response.
    const setSession = useCallback(
        (newAccessToken: string, newRefreshToken: string, newUser: UserRead) => {
            storeTokens(newAccessToken, newRefreshToken);
            setAccessToken(newAccessToken);
            setUser(newUser);
        },
        [],
    );

    const hasRole = useCallback(
        (...roles: UserRole[]) => (user ? roles.includes(user.role) : false),
        [user],
    );

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            accessToken,
            isAuthenticated: !!user,
            isLoading,
            login,
            logout,
            setSession,
            hasRole,
        }),
        [user, accessToken, isLoading, login, logout, setSession, hasRole],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ── Internal hook (use useAuth.ts externally) ─────────────────────────────────

export function useAuthContext(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider');
    return ctx;
}

export default AuthContext;
