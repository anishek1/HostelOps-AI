/**
 * hooks/useHostelLookup.ts — HostelOps AI
 * Debounced hostel code lookup. Used by Landing, Login, and Register.
 * Calls GET /hostels/{code}/info after 500ms idle, min 4 characters.
 */

import { useEffect, useState } from 'react';
import { getHostelInfo } from '../api/authApi';
import type { HostelPublicInfo } from '../types/user';

interface UseHostelLookupResult {
    hostelInfo: HostelPublicInfo | null;
    isLoading: boolean;
    error: string | null;
}

export function useHostelLookup(code: string, minLength = 4): UseHostelLookupResult {
    const [hostelInfo, setHostelInfo] = useState<HostelPublicInfo | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const trimmed = code.trim();

        if (trimmed.length < minLength) {
            setHostelInfo(null);
            setError(null);
            setIsLoading(false);
            return;
        }

        let cancelled = false;
        setIsLoading(true);
        setError(null);
        setHostelInfo(null);

        const timer = setTimeout(async () => {
            try {
                const info = await getHostelInfo(trimmed.toUpperCase());
                if (!cancelled) {
                    setHostelInfo(info);
                    setError(null);
                }
            } catch {
                if (!cancelled) {
                    setHostelInfo(null);
                    setError('Hostel not found. Check the code with your warden.');
                }
            } finally {
                if (!cancelled) setIsLoading(false);
            }
        }, 500);

        return () => {
            cancelled = true;
            clearTimeout(timer);
        };
    }, [code, minLength]);

    return { hostelInfo, isLoading, error };
}
