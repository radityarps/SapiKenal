import { fail, redirect } from "@sveltejs/kit";
import type { Actions, PageServerLoad } from "./$types";
import { adminLogout } from "$lib/server/admin";
import {
  BackendRequestError,
  backendJson,
  bearerHeaders,
} from "$lib/server/backend";

const api = (id = "") => `/api/admin/profiles${id ? `/${id}` : ""}`;

export const load: PageServerLoad = async ({ locals, url, fetch }) => {
  if (!locals.user) throw redirect(303, "/login");
  const query = new URLSearchParams({
    page: url.searchParams.get("page") || "1",
    page_size: "25",
  });
  const status = url.searchParams.get("status") || "";
  if (status) query.set("status", status);
  try {
    const profiles = await backendJson(
      `${api()}?${query}`,
      { headers: bearerHeaders(locals.sessionToken) },
      fetch,
    );
    return { user: locals.user, profiles, status, error: null };
  } catch (error) {
    return {
      user: locals.user,
      profiles: { items: [], total: 0, page: 1, page_size: 25 },
      status,
      error: error instanceof Error ? error.message : "Backend tidak tersedia",
    };
  }
};

export const actions: Actions = {
  create: async ({ request, locals, fetch }) => {
    const form = await request.formData();
    const payload = Object.fromEntries(
      [
        "slug",
        "model_class",
        "display_name",
        "summary",
        "strengths",
        "limitations",
        "disclaimer",
        "locale",
      ].map((key) => [key, String(form.get(key) || "").trim()]),
    );
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
        error: error instanceof Error ? error.message : "Profil gagal dibuat",
      });
    }
  },
  revise: async ({ request, locals, fetch }) => {
    const form = await request.formData();
    const id = String(form.get("id") || "");
    const payload = Object.fromEntries(
      [
        "model_class",
        "display_name",
        "summary",
        "strengths",
        "limitations",
        "disclaimer",
      ].map((key) => [key, String(form.get(key) || "").trim()]),
    );
    try {
      await backendJson(
        api(id),
        {
          method: "PATCH",
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
          error instanceof Error
            ? error.message
            : "Revisi profil gagal disimpan",
      });
    }
  },
  activate: async ({ request, locals, fetch }) =>
    mutate(request, locals.sessionToken, fetch, "activate"),
  deactivate: async ({ request, locals, fetch }) =>
    mutate(request, locals.sessionToken, fetch, "deactivate"),
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
        body: JSON.stringify({
          reason: String(form.get("reason") || "").trim(),
        }),
      },
      fetch,
    );
    return { success: true };
  } catch (error) {
    return fail(error instanceof BackendRequestError ? error.status : 400, {
      error:
        error instanceof Error
          ? error.message
          : "Status profil gagal diperbarui",
    });
  }
}
