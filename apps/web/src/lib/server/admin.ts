import { redirect } from "@sveltejs/kit";
import { backendJson, bearerHeaders } from "./backend";

export async function adminLogout(
	locals: App.Locals,
	cookies: { delete: (name: string, opts: { path: string }) => void },
	requestFetch: typeof fetch,
): Promise<never> {
	if (locals.sessionToken) {
		await backendJson(
			"/api/auth/logout",
			{
				method: "POST",
				headers: bearerHeaders(locals.sessionToken),
			},
			requestFetch,
		).catch(() => undefined);
	}
	cookies.delete("sapikenal_session", { path: "/" });
	throw redirect(303, "/login");
}
