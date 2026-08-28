import { env } from "$env/dynamic/private";
import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import {
	BackendRequestError,
	backendJson,
	bearerHeaders,
} from "$lib/server/backend";

const modelUploadMaxBytes = Number(env.MODEL_UPLOAD_MAX_BYTES || "250000000");

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
	if (!locals.user) throw redirect(303, "/login");
	const filters = {
		search: url.searchParams.get("search") || "",
		status: url.searchParams.get("status") || "",
		date_from: url.searchParams.get("date_from") || "",
		date_to: url.searchParams.get("date_to") || "",
	};
	const query = new URLSearchParams({
		page: url.searchParams.get("page") || "1",
		page_size: "25",
	});
	if (filters.search) query.set("search", filters.search);
	if (filters.status) query.set("status", filters.status);
	if (filters.date_from)
		query.set("registered_from", `${filters.date_from}T00:00:00+00:00`);
	if (filters.date_to)
		query.set("registered_to", `${filters.date_to}T23:59:59.999+00:00`);
	try {
		const models = await backendJson(
			`/api/admin/models?${query}`,
			{
				headers: bearerHeaders(locals.sessionToken),
			},
			fetch,
		);
		return { user: locals.user, models, filters, error: null };
	} catch (error) {
		return {
			user: locals.user,
			models: { items: [], total: 0 },
			filters,
			error: error instanceof Error ? error.message : "Backend tidak tersedia",
		};
	}
};

export const actions: Actions = {
	register: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const artifact = form.get("artifact");
		if (!artifact || typeof artifact === "string" || artifact.size === 0) {
			return fail(400, { registerError: "File model .keras wajib dipilih." });
		}
		if (
			Number.isFinite(modelUploadMaxBytes) &&
			artifact.size > modelUploadMaxBytes
		) {
			return fail(413, {
				registerError: "Ukuran file model melebihi batas upload.",
			});
		}
		const upload = new FormData();
		upload.set("version", String(form.get("version") || ""));
		upload.set("artifact", artifact, artifact.name);
		upload.set("input_size", String(form.get("input_size") || 224));
		upload.set("classes", String(form.get("classes") || ""));
		const notes = String(form.get("notes") || "").trim();
		if (notes) upload.set("notes", notes);
		try {
			await backendJson(
				"/api/admin/models/upload",
				{
					method: "POST",
					headers: bearerHeaders(locals.sessionToken),
					body: upload,
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				registerError:
					error instanceof Error ? error.message : "Gagal mengunggah model",
			});
		}
	},
	activate: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const id = String(form.get("id") || "");
		const reason = String(form.get("reason") || "").trim();
		try {
			await backendJson(
				`/api/admin/models/${id}/activate`,
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify({ reason }),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Aktivasi model gagal",
			});
		}
	},
	rollback: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		const id = String(form.get("id") || "");
		const reason = String(form.get("reason") || "").trim();
		try {
			await backendJson(
				`/api/admin/models/${id}/rollback`,
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify({ reason }),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(error instanceof BackendRequestError ? error.status : 400, {
				error: error instanceof Error ? error.message : "Rollback model gagal",
			});
		}
	},
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};
