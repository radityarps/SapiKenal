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

export const load: PageServerLoad = async ({ locals, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	let existingBreedKeys: string[] = [];
	let categorySortOrders: Record<string, number[]> = {};
	try {
		const res = await backendJson<{
			existing_breed_keys?: string[];
			category_sort_orders?: Record<string, number[]>;
		}>(
			api(),
			{ headers: bearerHeaders(locals.sessionToken) },
			fetch,
		);
		existingBreedKeys = res?.existing_breed_keys || [];
		categorySortOrders = res?.category_sort_orders || {};
	} catch {
		existingBreedKeys = [];
		categorySortOrders = {};
	}
	return { user: locals.user, existingBreedKeys, categorySortOrders };
};

export const actions: Actions = {
	create: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const is_breed_profile = form.get("is_breed_profile") === "true";
		const breed_key = String(form.get("breed_key") || "").trim();
		let category = String(form.get("category") || "app_usage").trim();
		const sort_order = Number(form.get("sort_order") || 0);
		const sources = String(form.get("sources") || "")
			.split("\n")
			.map((source) => source.trim())
			.filter(Boolean);

		const actionType = String(form.get("action_type") || "");
		const publishImmediately = actionType === "publish";

		const title = String(form.get("title") || "").trim();
		const summary = String(form.get("summary") || "").trim();
		const body = String(form.get("body") || "").trim();
		const content_blocks_raw = String(form.get("content_blocks") || "").trim();

		let content_blocks: any = null;
		if (content_blocks_raw) {
			try {
				content_blocks = JSON.parse(content_blocks_raw);
			} catch {
				content_blocks = null;
			}
		}

		let article_key = String(form.get("article_key") || "").trim();
		if (is_breed_profile) {
			if (!breed_key) {
				return fail(400, {
					error: "Jenis sapi wajib dipilih untuk artikel profil jenis sapi.",
					values: { title, summary, body, category, sort_order, sources: String(form.get("sources") || "") },
				});
			}
			article_key = `${breed_key}_1`;
			category = breed_key;
		} else if (!article_key) {
			article_key = slugify(title);
		}

		const formValues = {
			article_key,
			is_breed_profile,
			breed_key,
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

		const payload = {
			article_key,
			is_breed_profile,
			breed_key: is_breed_profile ? breed_key : null,
			category,
			sort_order,
			title,
			summary,
			body,
			content_blocks,
			sources,
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
