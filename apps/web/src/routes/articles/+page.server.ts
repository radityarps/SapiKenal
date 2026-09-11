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

const revisionFields = (form: FormData) => ({
	category: String(form.get("category") || "app_usage").trim(),
	sort_order: Number(form.get("sort_order") || 0),
	title: String(form.get("title") || "").trim(),
	summary: String(form.get("summary") || "").trim(),
	body: String(form.get("body") || "").trim(),
	sources: String(form.get("sources") || "")
		.split("\n")
		.map((source) => source.trim())
		.filter(Boolean),
});

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	const filters = {
		category: url.searchParams.get("category") || "",
		locale: url.searchParams.get("locale") || "",
		publication_status: url.searchParams.get("publication_status") || "",
		revision_status: url.searchParams.get("revision_status") || "",
	};
	const query = new URLSearchParams({
		page: url.searchParams.get("page") || "1",
		page_size: "25",
	});
	for (const [key, value] of Object.entries(filters)) {
		if (value) query.set(key, value);
	}
	try {
		const articles = await backendJson(
			`${api()}?${query}`,
			{ headers: bearerHeaders(locals.sessionToken) },
			fetch,
		);
		return { user: locals.user, articles, filters, error: null };
	} catch (error) {
		return {
			user: locals.user,
			articles: { items: [], total: 0, page: 1, page_size: 25 },
			filters,
			error: error instanceof Error ? error.message : "Backend tidak tersedia",
		};
	}
};

export const actions: Actions = {
	create: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const payload = {
			article_key: String(form.get("article_key") || "").trim(),
			locale: String(form.get("locale") || "id-ID").trim(),
			...revisionFields(form),
			content_reviewed: false,
		};
		try {
			await backendJson(
				api(),
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify(payload),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Artikel gagal dibuat",
			});
		}
	},
	revise: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const id = String(form.get("id") || "");
		const payload = revisionFields(form);
		try {
			await backendJson(
				`${api(id)}/revise`,
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify(payload),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error:
					error instanceof Error ? error.message : "Revisi artikel gagal disimpan",
			});
		}
	},
	review: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const id = String(form.get("id") || "");
		if (!id || form.get("content_reviewed") !== "true") {
			return fail(422, {
				error: "Konfirmasi peninjauan isi dan sumber diperlukan.",
			});
		}
		try {
			await backendJson(
				`${api(id)}/review`,
				{
					method: "POST",
					headers: bearerHeaders(locals.sessionToken),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error:
					error instanceof Error ? error.message : "Review artikel gagal disimpan",
			});
		}
	},
	activate: async ({ request, locals, fetch }) =>
		mutate(request, locals.sessionToken, fetch, "activate"),
	deactivate: async ({ request, locals, fetch }) =>
		mutate(request, locals.sessionToken, fetch, "deactivate"),
	review_and_activate: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const id = String(form.get("id") || "");
		if (!id) return fail(400, { error: "ID artikel tidak ditemukan." });
		try {
			await backendJson(
				`${api(id)}/review`,
				{ method: "POST", headers: bearerHeaders(locals.sessionToken) },
				fetch,
			);
			await backendJson(
				`${api(id)}/activate`,
				{
					method: "POST",
					headers: { ...bearerHeaders(locals.sessionToken), "content-type": "application/json" },
					body: JSON.stringify({ reason: "Tinjau dan publikasikan sekaligus" }),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Gagal meninjau dan mempublikasikan artikel",
			});
		}
	},
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};

async function mutate(
	request: Request,
	token: string | null,
	fetch: typeof globalThis.fetch,
	action: "activate" | "deactivate",
) {
	const form = await request.formData();
	const id = String(form.get("id") || "");
	try {
		await backendJson(
			`${api(id)}/${action}`,
			{
				method: "POST",
				headers: {
					...bearerHeaders(token),
					"content-type": "application/json",
				},
				body: JSON.stringify({ reason: String(form.get("reason") || "").trim() }),
			},
			fetch,
		);
		return { success: true };
	} catch (error) {
		return fail(error instanceof BackendRequestError ? error.status : 400, {
			error:
				error instanceof Error ? error.message : "Status artikel gagal diperbarui",
		});
	}
}
