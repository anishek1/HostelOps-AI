/**
 * api/authApi.ts — HostelOps AI
 * Auth API functions. All API calls go through /src/api/ — never inline in components.
 */

import axios from 'axios';
import type { LoginRequest, Token, UserCreate, UserRead } from '../types/user';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
});

export async function register(data: UserCreate): Promise<UserRead> {
    const response = await api.post<UserRead>('/api/auth/register', data);
    return response.data;
}

export async function login(credentials: LoginRequest): Promise<Token> {
    const response = await api.post<Token>('/api/auth/login', credentials);
    return response.data;
}

export async function getMe(token: string): Promise<UserRead> {
    const response = await api.get<UserRead>('/api/users/me', {
        headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
}

export default api;
