import { dev } from "$app/environment";
import { fail, redirect } from "@sveltejs/kit";
import { backendJson } from "$lib/server/backend";
import type { Actions, PageServerLoad } from "./$types";

export const load: PageServerLoad = ({ locals }) => {
	if (locals.user) throw redirect(303, "/dashboard");
};

export const actions: Actions = {
	default: async ({ request, cookies, fetch }) => {
		const form = await request.formData();
		const email = String(form.get("email") || "").trim();
		const password = String(form.get("password") || "");

		if (!email || !password) {
			return fail(400, { message: "Email dan kata sandi wajib diisi.", email });
		}

		try {
			const response = await backendJson<{
				session_token: string;
				expires_at: string;
				user: App.Locals["user"];
			}>(
				"/api/auth/login",
				{
					method: "POST",
					headers: { "content-type": "application/json" },
					body: JSON.stringify({ email, password }),
				},
				fetch,
			);

			cookies.set("sapikenal_session", response.session_token, {
				path: "/",
				httpOnly: true,
				sameSite: "lax",
				secure: !dev,
				expires: new Date(response.expires_at),
			});
		} catch (error) {
			return fail(401, {
				message: error instanceof Error ? error.message : "Login gagal.",
				email,
			});
		}

		throw redirect(303, "/dashboard?toast=Login%20berhasil");
	},
};
