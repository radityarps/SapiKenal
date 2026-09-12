import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import {
	BackendRequestError,
	backendJson,
	bearerHeaders,
} from "$lib/server/backend";

const api = () => "/api/admin/articles";

function slugify(text: string): string {
	const cleaned = text
		.toLowerCase()
		.trim()
		.normalize("NFD")
		.replace(/[\u0300-\u036f]/g, "")
		.replace(/[^a-z0-9]+/g, "-")
		.replace(/^-+|-+$/g, "")
		.slice(0, 64);
	return cleaned || `artikel-${Date.now().toString(36)}`;
}

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.user) throw redirect(303, "/login");
	return { user: locals.user };
};

export const actions: Actions = {
	create: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const category = String(form.get("category") || "app_usage").trim();
		const sort_order = Number(form.get("sort_order") || 0);
		const sources = String(form.get("sources") || "")
			.split("\n")
			.map((source) => source.trim())
			.filter(Boolean);

		const actionType = String(form.get("action_type") || "");
		const publishImmediately =
			actionType === "publish" ||
			(actionType !== "draft" && form.get("publish_immediately") === "true");

		const title = String(form.get("title") || "").trim();
		const summary = String(form.get("summary") || "").trim();
		const body = String(form.get("body") || "").trim();
		const article_key =
			String(form.get("article_key") || "").trim() || slugify(title);

		const formValues = {
			article_key,
			category,
			sort_order,
			sources: String(form.get("sources") || ""),
			title,
			summary,
			body,
		};

		if (!title || !summary || !body) {
			return fail(400, {
				error: "Judul, ringkasan, dan isi artikel wajib diisi lengkap.",
				values: formValues,
			});
		}

		if (sources.length === 0) {
			return fail(400, {
				error: "Minimal satu tautan sumber rujukan valid (HTTP/HTTPS) wajib diisi.",
				values: formValues,
			});
		}

		const payload = {
			article_key,
			category,
			sort_order,
			title,
			summary,
			body,
			sources,
			content_reviewed: false,
		};

		try {
			const res = await backendJson<{ item?: { id: string } }>(
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

			if (publishImmediately && res?.item?.id) {
				await activateCreatedArticle(res.item.id, locals.sessionToken, fetch);
			}
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Artikel gagal dibuat",
				values: formValues,
			});
		}

		throw redirect(303, "/articles");
	},
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};

async function activateCreatedArticle(
	articleId: string,
	token: string | null,
	fetchFn: typeof globalThis.fetch,
) {
	await backendJson(
		`${api()}/${encodeURIComponent(articleId)}/review`,
		{
			method: "POST",
			headers: bearerHeaders(token),
		},
		fetchFn,
	);
	await backendJson(
		`${api()}/${encodeURIComponent(articleId)}/activate`,
		{
			method: "POST",
			headers: {
				...bearerHeaders(token),
				"content-type": "application/json",
			},
			body: JSON.stringify({ reason: "Publikasi langsung artikel baru" }),
		},
		fetchFn,
	);
}
