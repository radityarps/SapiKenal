import { backendFetch } from "$lib/server/backend";
import type { RequestHandler } from "./$types";

export const GET: RequestHandler = async ({ params, fetch }) => {
	const res = await backendFetch(`/media/${params.path}`, {}, fetch);
	return new Response(res.body, {
		status: res.status,
		headers: {
			"content-type": res.headers.get("content-type") || "application/octet-stream",
			"cache-control": res.headers.get("cache-control") || "public, max-age=86400",
		},
	});
};
