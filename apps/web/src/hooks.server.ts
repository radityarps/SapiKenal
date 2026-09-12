import { backendJson } from "$lib/server/backend";
import type { Handle } from "@sveltejs/kit";

export const handle: Handle = async ({ event, resolve }) => {
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
