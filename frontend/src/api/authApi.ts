/**
 * api/authApi.ts — HostelOps AI
 * Auth + hostel API functions. All calls go through the shared Axios client.
 */

import type {
    HostelPublicInfo,
    HostelSetupRequest,
    HostelSetupResponse,
    LoginRequest,
    LoginResponse,
    Token,
    UserCreate,
    UserRead,
} from '../types/user';
import client from './client';

export async function register(data: UserCreate): Promise<UserRead> {
    const res = await client.post<UserRead>('/auth/register', data);
    return res.data;
}

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
    const res = await client.post<LoginResponse>('/auth/login', credentials);
    return res.data;
}

export async function refreshTokens(refreshToken: string): Promise<Token> {
    const res = await client.post<Token>('/auth/refresh', { refresh_token: refreshToken });
    return res.data;
}

export async function logout(): Promise<void> {
    await client.post('/auth/logout');
}

export async function getMe(): Promise<UserRead> {
    const res = await client.get<UserRead>('/users/me');
    return res.data;
}

export async function getHostelInfo(code: string): Promise<HostelPublicInfo> {
    const res = await client.get<HostelPublicInfo>(`/hostels/${encodeURIComponent(code)}/info`);
    return res.data;
}

export async function setupHostel(data: HostelSetupRequest): Promise<HostelSetupResponse> {
    const res = await client.post<HostelSetupResponse>('/hostels/setup', data);
    return res.data;
}
