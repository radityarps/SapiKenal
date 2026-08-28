import { env } from "$env/dynamic/private";

const backendUrl = env.BACKEND_INTERNAL_URL || "http://localhost:8000";

export class BackendRequestError extends Error {
	status: number;
	code: string | null;

	constructor(status: number, message: string, code: string | null = null) {
		super(message);
		this.name = "BackendRequestError";
		this.status = status;
		this.code = code;
	}
}

export function backendFetch(
	path: string,
	init: RequestInit = {},
	requestFetch: typeof fetch = globalThis.fetch,
) {
	const headers = new Headers(init.headers);
	headers.set("accept", "application/json");
	return requestFetch(`${backendUrl}${path}`, { ...init, headers });
}

export async function backendJson<T>(
	path: string,
	init: RequestInit = {},
	requestFetch: typeof fetch = globalThis.fetch,
): Promise<T> {
	const response = await backendFetch(path, init, requestFetch);
	let body: {
		message?: string;
		code?: string;
		error_code?: string;
	} = {};
	try {
		body = await response.json();
	} catch {
		body = {};
	}
	if (!response.ok) {
		throw new BackendRequestError(
			response.status,
			body?.message || "Backend request failed",
			body?.code || body?.error_code || null,
		);
	}
	return body as T;
}

export function bearerHeaders(token: string | null): HeadersInit {
	return token ? { authorization: `Bearer ${token}` } : {};
}
