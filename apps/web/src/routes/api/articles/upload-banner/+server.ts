import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { backendFetch, bearerHeaders } from "$lib/server/backend";

export const POST: RequestHandler = async ({ request, locals, fetch }) => {
	if (!locals.user) {
		return json({ error: "Sesi tidak valid atau telah berakhir. Silakan login kembali." }, { status: 401 });
	}

	const formData = await request.formData();
	const file = formData.get("file");
	if (!(file instanceof File) || file.size === 0) {
		return json({ error: "Berkas banner tidak ditemukan atau kosong." }, { status: 400 });
	}

	const backendFormData = new FormData();
	backendFormData.append("file", file, file.name);

	try {
		const res = await backendFetch(
			"/api/admin/articles/upload-banner",
			{
				method: "POST",
				headers: bearerHeaders(locals.sessionToken),
				body: backendFormData,
			},
			fetch,
		);

		const data = await res.json();
		if (!res.ok) {
			return json({ error: data.message || "Gagal mengunggah banner." }, { status: res.status });
		}
		return json(data);
	} catch (err) {
		return json(
			{ error: err instanceof Error ? err.message : "Terjadi kesalahan server saat mengunggah banner." },
			{ status: 500 },
		);
	}
};
