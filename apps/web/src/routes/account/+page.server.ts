import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import { backendJson, bearerHeaders } from "$lib/server/backend";

export const load: PageServerLoad = ({ locals }) => {
	if (!locals.user) throw redirect(303, "/login");
	return { user: locals.user };
};

export const actions: Actions = {
	changePassword: async ({ request, locals, fetch }) => {
		const form = await request.formData();
		try {
			await backendJson(
				"/api/auth/change-password",
				{
					method: "POST",
					headers: {
						...bearerHeaders(locals.sessionToken),
						"content-type": "application/json",
					},
					body: JSON.stringify({
						current_password: String(form.get("current_password") || ""),
						new_password: String(form.get("new_password") || ""),
					}),
				},
				fetch,
			);
			return { success: true };
		} catch (error) {
			return fail(400, {
				error:
					error instanceof Error ? error.message : "Gagal mengubah password",
			});
		}
	},
	logout: async ({ locals, cookies, fetch }) =>
		adminLogout(locals, cookies, fetch),
};
