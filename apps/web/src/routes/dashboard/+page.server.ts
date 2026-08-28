import { redirect } from "@sveltejs/kit";
import type { PageServerLoad, Actions } from "./$types";
import { backendJson, bearerHeaders } from "$lib/server/backend";

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	const requestedPeriod = url.searchParams.get("period");
	const period = ["24h", "7d", "30d"].includes(requestedPeriod || "")
		? requestedPeriod
		: "7d";
	try {
		const dashboard = await backendJson(
			`/api/admin/dashboard?period=${period}`,
			{
				headers: bearerHeaders(locals.sessionToken),
			},
			fetch,
		);
		return { user: locals.user, dashboard, period, error: null };
	} catch (error) {
		return {
			user: locals.user,
			dashboard: null,
			period,
			error: error instanceof Error ? error.message : "Backend tidak tersedia",
		};
	}
};

export const actions: Actions = {
	logout: async ({ locals, cookies, fetch }) => {
		if (locals.sessionToken) {
			try {
				await backendJson(
					"/api/auth/logout",
					{
						method: "POST",
						headers: bearerHeaders(locals.sessionToken),
					},
					fetch,
				);
			} catch {
				// Clear the browser cookie even when the backend is unavailable.
			}
		}
		cookies.delete("sapikenal_session", { path: "/" });
		throw redirect(303, "/login");
	},
};
