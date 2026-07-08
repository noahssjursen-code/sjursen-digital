export class ApiError extends Error {
	status: number;
	constructor(status: number, message: string) {
		super(message);
		this.status = status;
	}
}

export async function api<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
	const res = await fetch(path, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(options.headers ?? {})
		}
	});
	if (!res.ok) {
		throw new ApiError(res.status, await res.text());
	}
	return res.json();
}

export function fmtTime(iso: string | null): string {
	if (!iso) return '—';
	const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
	return d.toLocaleString();
}

export function timeAgo(iso: string | null): string {
	if (!iso) return 'never';
	const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
	const s = Math.max(0, Math.floor((Date.now() - d.getTime()) / 1000));
	if (s < 60) return `${s}s ago`;
	if (s < 3600) return `${Math.floor(s / 60)}m ago`;
	if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
	return `${Math.floor(s / 86400)}d ago`;
}
