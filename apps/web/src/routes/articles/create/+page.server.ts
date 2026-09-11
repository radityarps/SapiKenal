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

		// Check if request comes from single-locale format (e.g. tests)
		if (form.has("title") && !form.has("title_id")) {
			const article_key = String(form.get("article_key") || "").trim() || slugify(String(form.get("title") || ""));
			const locale = String(form.get("locale") || "id-ID").trim();
			const title = String(form.get("title") || "").trim();
			const summary = String(form.get("summary") || "").trim();
			const body = String(form.get("body") || "").trim();

			const payload = {
				article_key,
				locale,
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
					values: {
						article_key,
						locale,
						category,
						sort_order,
						title,
						summary,
						body,
						sources: String(form.get("sources") || ""),
					},
				});
			}

			throw redirect(303, "/articles");
		}

		// Multi-locale format (ID required, EN optional)
		const title_id = String(form.get("title_id") || "").trim();
		const summary_id = String(form.get("summary_id") || "").trim();
		const body_id = String(form.get("body_id") || "").trim();

		const title_en = String(form.get("title_en") || "").trim();
		const summary_en = String(form.get("summary_en") || "").trim();
		const body_en = String(form.get("body_en") || "").trim();

		const formValues = {
			category,
			sort_order,
			sources: String(form.get("sources") || ""),
			title_id,
			summary_id,
			body_id,
			title_en,
			summary_en,
			body_en,
		};

		if (!title_id || !summary_id || !body_id) {
			return fail(400, {
				error: "Konten Bahasa Indonesia (judul, ringkasan, dan isi artikel) wajib diisi lengkap.",
				values: formValues,
			});
		}

		const hasEn = Boolean(title_en || summary_en || body_en);
		if (hasEn && (!title_en || !summary_en || !body_en)) {
			return fail(400, {
				error: "Jika mengisi terjemahan Bahasa Inggris, judul, ringkasan, dan isi artikel EN harus diisi lengkap.",
				values: formValues,
			});
		}

		if (sources.length === 0) {
			return fail(400, {
				error: "Minimal satu tautan sumber rujukan valid (HTTP/HTTPS) wajib diisi.",
				values: formValues,
			});
		}

		const article_key = String(form.get("article_key") || "").trim() || slugify(title_id);

		try {
			// 1. Create Indonesian version
			const idPayload = {
				article_key,
				locale: "id-ID",
				category,
				sort_order,
				title: title_id,
				summary: summary_id,
				body: body_id,
				sources,
				content_reviewed: false,
			};

			const idRes = await backendJson<{ item?: { id: string } }>(
				api(),
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify(idPayload),
				},
				fetch,
			);

			if (publishImmediately && idRes?.item?.id) {
				await activateCreatedArticle(idRes.item.id, locals.sessionToken, fetch);
			}

			// 2. If English version is provided, create with the same article_key
			if (hasEn) {
				const enPayload = {
					article_key,
					locale: "en-US",
					category,
					sort_order,
					title: title_en,
					summary: summary_en,
					body: body_en,
					sources,
					content_reviewed: false,
				};

				const enRes = await backendJson<{ item?: { id: string } }>(
					api(),
					{
						method: "POST",
						headers: {
							...bearerHeaders(locals.sessionToken),
							"content-type": "application/json",
						},
						body: JSON.stringify(enPayload),
					},
					fetch,
				);

				if (publishImmediately && enRes?.item?.id) {
					await activateCreatedArticle(enRes.item.id, locals.sessionToken, fetch);
				}
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
