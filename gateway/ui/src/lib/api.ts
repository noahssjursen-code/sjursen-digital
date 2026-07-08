import { goto } from '$app/navigation';

const TOKEN_KEY = 'sjursen_digital_gateway_token';

export function getSessionToken(): string {
	if (typeof window === 'undefined') return '';
	return localStorage.getItem(TOKEN_KEY) ?? '';
}

export function setSessionToken(token: string): void {
	if (typeof window === 'undefined') return;
	localStorage.setItem(TOKEN_KEY, token.trim());
}

export function clearSessionToken(): void {
	if (typeof window === 'undefined') return;
	localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
	status: number;
	constructor(status: number, message: string) {
		super(message);
		this.status = status;
	}
}

export async function api<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
	const token = getSessionToken();
	
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string> ?? {})
	};

	if (token) {
		headers['Authorization'] = `Bearer ${token}`;
	}

	const res = await fetch(path, {
		...options,
		headers
	});

	if (res.status === 401) {
		clearSessionToken();
		// If we are not already on the login page, redirect to it
		if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
			goto('/login');
		}
		throw new ApiError(401, 'Unauthorized. Please login.');
	}

	if (!res.ok) {
		throw new ApiError(res.status, await res.text());
	}

	return res.json();
}
