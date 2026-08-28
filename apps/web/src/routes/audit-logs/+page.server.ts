import { redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import { backendJson, bearerHeaders } from "$lib/server/backend";

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	const filters = {
		search: url.searchParams.get("search") || "",
		action: url.searchParams.get("action") || "",
		status: url.searchParams.get("status") || "",
		date_from: url.searchParams.get("date_from") || "",
		date_to: url.searchParams.get("date_to") || "",
	};
	const query = new URLSearchParams({
		page: url.searchParams.get("page") || "1",
		page_size: "25",
	});
	if (filters.search) query.set("search", filters.search);
	if (filters.action) query.set("action", filters.action);
	if (filters.status) query.set("status", filters.status);
	if (filters.date_from)
		query.set("date_from", `${filters.date_from}T00:00:00+00:00`);
	if (filters.date_to)
		query.set("date_to", `${filters.date_to}T23:59:59.999+00:00`);
	try {
		const logs = await backendJson(
			`/api/admin/audit-logs?${query}`,
			{
				headers: bearerHeaders(locals.sessionToken),
			},
			fetch,
		);
		return { user: locals.user, logs, filters, error: null };
	} catch (error) {
		return {
			user: locals.user,
			logs: { items: [], total: 0 },
			filters,
			error: error instanceof Error ? error.message : "Backend tidak tersedia",
		};
	}
};

export const actions: Actions = {
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};
