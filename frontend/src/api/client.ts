/**
 * api/client.ts — HostelOps AI
 * Shared Axios instance. All API call functions import from here.
 * Handles: baseURL, Bearer token injection, 401 → refresh → retry flow.
 */

import axios from 'axios';

const BASE = import.meta.env.VITE_API_URL
    ? `${import.meta.env.VITE_API_URL}/api`
    : 'http://localhost:8000/api';

const client = axios.create({
    baseURL: BASE,
    headers: { 'Content-Type': 'application/json' },
});

// ── Request: attach Bearer token from localStorage ──────────────────────────
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// ── Response: 401 → refresh → retry ─────────────────────────────────────────
let isRefreshing = false;
type QueueEntry = { resolve: (token: string) => void; reject: (err: unknown) => void };
let failQueue: QueueEntry[] = [];

function drainQueue(error: unknown, token: string | null) {
    failQueue.forEach((p) => (error ? p.reject(error) : p.resolve(token!)));
    failQueue = [];
}

function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

client.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config as typeof error.config & { _retry?: boolean };

        if (error.response?.status !== 401 || original._retry) {
            return Promise.reject(error);
        }

        // Queue subsequent 401s while refresh is in-flight
        if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
                failQueue.push({ resolve, reject });
            }).then((token) => {
                original.headers.Authorization = `Bearer ${token}`;
                return client(original);
            });
        }

        original._retry = true;
        isRefreshing = true;

        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            clearTokens();
            window.location.href = '/auth/login';
            return Promise.reject(error);
        }

        try {
            // Use plain axios (not client) to avoid interceptor loop
            const res = await axios.post(`${BASE}/auth/refresh`, {
                refresh_token: refreshToken,
            });
            const { access_token, refresh_token } = res.data as {
                access_token: string;
                refresh_token: string;
            };
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);
            drainQueue(null, access_token);
            original.headers.Authorization = `Bearer ${access_token}`;
            return client(original);
        } catch (refreshError) {
            drainQueue(refreshError, null);
            clearTokens();
            window.location.href = '/auth/login';
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    },
);

export default client;
