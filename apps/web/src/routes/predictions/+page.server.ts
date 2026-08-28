import { redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import { backendJson, bearerHeaders } from "$lib/server/backend";

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	const filters = {
		search: url.searchParams.get("search") || "",
		predicted_class: url.searchParams.get("predicted_class") || "",
		outcome: url.searchParams.get("outcome") || "",
		inference_mode: url.searchParams.get("inference_mode") || "",
		reliable: url.searchParams.get("reliable") || "",
		date_from: url.searchParams.get("date_from") || "",
		date_to: url.searchParams.get("date_to") || "",
	};
	const query = new URLSearchParams({
		page: url.searchParams.get("page") || "1",
		page_size: "25",
	});
	if (filters.search) query.set("search", filters.search);
	if (filters.predicted_class)
		query.set("predicted_class", filters.predicted_class);
	if (filters.outcome)
		query.set("outcome", filters.outcome);
	if (filters.inference_mode)
		query.set("inference_mode", filters.inference_mode);
	if (filters.reliable) query.set("reliable", filters.reliable);
	const startTimestamp = filters.date_from
		? Date.parse(`${filters.date_from}T00:00:00.000Z`)
		: Number.NaN;
	const endTimestamp = filters.date_to
		? Date.parse(`${filters.date_to}T23:59:59.999Z`)
		: Number.NaN;
	if (Number.isFinite(startTimestamp))
		query.set("date_from", String(startTimestamp));
	if (Number.isFinite(endTimestamp)) query.set("date_to", String(endTimestamp));
	try {
		const predictions = await backendJson(
			`/api/admin/predictions?${query}`,
			{
				headers: bearerHeaders(locals.sessionToken),
			},
			fetch,
		);
		return { user: locals.user, predictions, filters, error: null };
	} catch (error) {
		return {
			user: locals.user,
			predictions: { items: [], total: 0 },
			filters,
			error: error instanceof Error ? error.message : "Backend tidak tersedia",
		};
	}
};

export const actions: Actions = {
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};
