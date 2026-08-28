import { env } from "$env/dynamic/private";
import { backendJson } from "$lib/server/backend";
import type { Handle } from "@sveltejs/kit";

const modelUploadMaxBytes = Number(env.MODEL_UPLOAD_MAX_BYTES || "250000000");

export const handle: Handle = async ({ event, resolve }) => {
	const contentLength = Number(event.request.headers.get("content-length"));
	if (
		event.url.pathname === "/models" &&
		event.request.method === "POST" &&
		event.request.headers
			.get("content-type")
			?.toLowerCase()
			.startsWith("multipart/form-data") &&
		Number.isFinite(modelUploadMaxBytes) &&
		Number.isFinite(contentLength) &&
		contentLength > modelUploadMaxBytes + 1_048_576
	) {
		return new Response("Model upload exceeds the configured size limit", {
			status: 413,
			headers: { "content-type": "text/plain; charset=utf-8" },
		});
	}
	const token = event.cookies.get("sapikenal_session") || null;
	event.locals.sessionToken = token;
	event.locals.user = null;

	if (token) {
		try {
			const response = await backendJson<{ user: App.Locals["user"] }>(
				"/api/auth/me",
				{
					headers: { authorization: `Bearer ${token}` },
				},
			);
			event.locals.user = response.user;
		} catch {
			event.cookies.delete("sapikenal_session", { path: "/" });
			event.locals.sessionToken = null;
		}
	}

	return resolve(event);
};
