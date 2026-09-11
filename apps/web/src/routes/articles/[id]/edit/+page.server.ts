import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import {
	BackendRequestError,
	backendJson,
	bearerHeaders,
} from "$lib/server/backend";

const api = (id = "") =>
	`/api/admin/articles${id ? `/${encodeURIComponent(id)}` : ""}`;

export const load: PageServerLoad = async ({ locals, params, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	try {
		const article = await backendJson<{ item?: any }>(
			api(params.id),
			{ headers: bearerHeaders(locals.sessionToken) },
			fetch,
		);
		if (!article?.item) throw redirect(303, "/articles");
		return { user: locals.user, article: article.item };
	} catch {
		throw redirect(303, "/articles");
	}
};

export const actions: Actions = {
	revise: async ({ request, locals, params, fetch }) => {
		const form = await request.formData();
		const category = String(form.get("category") || "app_usage").trim();
		const sort_order = Number(form.get("sort_order") || 0);
		const title = String(form.get("title") || "").trim();
		const summary = String(form.get("summary") || "").trim();
		const body = String(form.get("body") || "").trim();
		const sources = String(form.get("sources") || "")
			.split("\n")
			.map((s) => s.trim())
			.filter(Boolean);

		if (!title || !summary || !body) {
			return fail(400, { error: "Judul, ringkasan, dan isi artikel wajib diisi." });
		}

		try {
			await backendJson(
				`${api(params.id)}/revise`,
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify({ category, sort_order, title, summary, body, sources }),
				},
				fetch,
			);
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Revisi artikel gagal disimpan",
			});
		}
		throw redirect(303, "/articles");
	},
	logout: async ({ locals, cookies, fetch }) => adminLogout(locals, cookies, fetch),
};
