import { render } from "svelte/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("$lib/server/backend", () => ({
	backendJson: vi.fn().mockResolvedValue({ status: "success" }),
	bearerHeaders: () => ({}),
	BackendRequestError: class extends Error {
		status = 400;
	},
}));
vi.mock("$lib/server/admin", () => ({ adminLogout: vi.fn() }));

import { backendJson } from "$lib/server/backend";
import Page from "./+page.svelte";
import { actions, load } from "./+page.server";

beforeEach(() => vi.clearAllMocks());

function actionEvent(fields: Record<string, string>) {
	return {
		request: new Request("http://localhost/articles", {
			method: "POST",
			body: new URLSearchParams(fields),
		}),
		locals: { sessionToken: "test-only" },
		fetch: vi.fn(),
	} as unknown as Parameters<NonNullable<typeof actions.create>>[0];
}

function articleFields() {
	return {
		article_key: "panduan-identifikasi",
		category: "app_usage",
		sort_order: "10",
		title: "Panduan identifikasi",
		summary: "Ringkasan panduan.",
		body: "Gunakan foto yang jelas.",
		sources: "https://example.org/guide\n https://example.org/terms ",
	};
}

describe("Artikel Panduan page server", () => {
	it("forwards category, publication, and revision filters", async () => {
		vi.mocked(backendJson).mockResolvedValueOnce({
			page: 2,
			page_size: 25,
			total: 0,
			items: [],
		});

		await load!({
			locals: { user: { id: "admin" }, sessionToken: "test-only" },
			url: new URL(
				"http://localhost/articles?page=2&category=bali&publication_status=active&revision_status=draft",
			),
			fetch: vi.fn(),
		} as never);

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles?page=2&page_size=25&category=bali&publication_status=active&revision_status=draft",
			expect.objectContaining({ headers: {} }),
			expect.any(Function),
		);
	});

	it("shows the active revision while the latest revision is draft", () => {
		const { body } = render(Page, {
			props: {
				data: {
					user: {
						id: "admin",
						email: "admin@example.com",
						display_name: "Administrator",
						role: "admin",
						status: "active",
						must_change_password: false,
					},
					articles: {
						page: 1,
						page_size: 25,
						total: 1,
						items: [
							{
								id: "article-1",
								article_key: "bali_1",
								publication_status: "active",
								revision: {
									revision: 2,
									status: "draft",
									category: "bali",
									title: "Draft terbaru",
									summary: "Ringkasan",
									content_reviewed: false,
								},
								active_revision: { revision: 1 },
							},
						],
					},
					filters: {
						category: "",
						publication_status: "",
						revision_status: "",
					},
					error: null,
				},
				form: null,
			},
		});

		expect(body).toContain("Revisi terbaru: v2 · Draft");
		expect(body).toContain("Publik saat ini: v1");
	});

	it("creates a draft article with normalized source URLs", async () => {
		await actions.create!(actionEvent(articleFields()));

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({
					...articleFields(),
					sort_order: 10,
					sources: ["https://example.org/guide", "https://example.org/terms"],
					content_reviewed: false,
				}),
			}),
			expect.any(Function),
		);
	});

	it("sends only revision fields when saving content", async () => {
		await actions.revise!(
			actionEvent({ id: "article/1", ...articleFields(), title: "Updated title" }),
		);

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles/article%2F1/revise",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({
					category: "app_usage",
					sort_order: 10,
					title: "Updated title",
					summary: "Ringkasan panduan.",
					body: "Gunakan foto yang jelas.",
					sources: ["https://example.org/guide", "https://example.org/terms"],
				}),
			}),
			expect.any(Function),
		);
		const request = JSON.parse(
			String(vi.mocked(backendJson).mock.calls[0][1]?.body),
		);
		expect(request).not.toHaveProperty("article_key");
		expect(request).not.toHaveProperty("locale");
		expect(request).not.toHaveProperty("content_reviewed");
	});

	it("requires an explicit review confirmation", async () => {
		const result = await actions.review!(actionEvent({ id: "article-1" }));

		expect(result).toMatchObject({ status: 422 });
		expect(backendJson).not.toHaveBeenCalled();
	});

	it("reviews saved content through the article endpoint", async () => {
		await actions.review!(
			actionEvent({ id: "article-1", content_reviewed: "true" }),
		);

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles/article-1/review",
			expect.objectContaining({
				method: "POST",
			}),
			expect.any(Function),
		);
	});

	it.each(["activate", "deactivate"])(
		"sends %s as a separate lifecycle action",
		async (action) => {
			await actions[action as "activate" | "deactivate"]!(
				actionEvent({ id: "article-1", reason: "Editorial decision" }),
			);

			expect(backendJson).toHaveBeenCalledWith(
				`/api/admin/articles/article-1/${action}`,
				expect.objectContaining({
					method: "POST",
					body: JSON.stringify({ reason: "Editorial decision" }),
				}),
				expect.any(Function),
			);
		},
	);
});

import { actions as createActions, load as createLoad } from "./create/+page.server";

describe("Artikel Panduan create page server", () => {
	it("redirects unauthenticated users to login", async () => {
		await expect(
			createLoad!({ locals: { user: null } } as never),
		).rejects.toMatchObject({ status: 303, location: "/login" });
	});

	it("creates an article without icon and redirects to /articles", async () => {
		await expect(
			createActions.create!(actionEvent(articleFields()) as never),
		).rejects.toMatchObject({ status: 303, location: "/articles" });

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({
					...articleFields(),
					sort_order: 10,
					sources: ["https://example.org/guide", "https://example.org/terms"],
					content_reviewed: false,
				}),
			}),
			expect.any(Function),
		);
		const request = JSON.parse(
			String(vi.mocked(backendJson).mock.calls[0][1]?.body),
		);
		expect(request).not.toHaveProperty("icon");
		expect(request).not.toHaveProperty("image");
	});

	it("creates article and auto-generates article_key from title", async () => {
		await expect(
			createActions.create!(
				actionEvent({
					category: "bali",
					sort_order: "5",
					sources: "https://example.org/bali",
					title: "Sapi Bali Unggulan",
					summary: "Ringkasan sapi Bali",
					body: "Deskripsi lengkap sapi Bali",
				}) as never,
			),
		).rejects.toMatchObject({ status: 303, location: "/articles" });

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({
					article_key: "sapi-bali-unggulan",
					category: "bali",
					sort_order: 5,
					title: "Sapi Bali Unggulan",
					summary: "Ringkasan sapi Bali",
					body: "Deskripsi lengkap sapi Bali",
					sources: ["https://example.org/bali"],
					content_reviewed: false,
				}),
			}),
			expect.any(Function),
		);
	});

	it("fails when content is incomplete", async () => {
		const result = await createActions.create!(
			actionEvent({
				category: "bali",
				title: "",
				summary: "Ringkasan saja",
				body: "",
				sources: "https://example.org/bali",
			}) as never,
		);
		expect(result).toMatchObject({
			status: 400,
			data: expect.objectContaining({
				error: expect.stringContaining("Judul, ringkasan, dan isi artikel wajib diisi lengkap"),
			}),
		});
		expect(backendJson).not.toHaveBeenCalled();
	});

	it("publishes immediately when action_type is publish", async () => {
		vi.mocked(backendJson).mockResolvedValue({
			status: "success",
			item: { id: "article-uuid-123" },
		});

		await expect(
			createActions.create!(
				actionEvent({
					action_type: "publish",
					category: "bali",
					sort_order: "5",
					sources: "https://example.org/bali",
					title: "Sapi Bali Unggulan",
					summary: "Ringkasan sapi Bali",
					body: "Deskripsi lengkap sapi Bali",
				}) as never,
			),
		).rejects.toMatchObject({ status: 303, location: "/articles" });

		expect(backendJson).toHaveBeenCalledTimes(3);
		expect(backendJson).toHaveBeenNthCalledWith(
			1,
			"/api/admin/articles",
			expect.any(Object),
			expect.any(Function),
		);
		expect(backendJson).toHaveBeenNthCalledWith(
			2,
			"/api/admin/articles/article-uuid-123/review",
			expect.any(Object),
			expect.any(Function),
		);
		expect(backendJson).toHaveBeenNthCalledWith(
			3,
			"/api/admin/articles/article-uuid-123/activate",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({ reason: "Publikasi langsung artikel baru" }),
			}),
			expect.any(Function),
		);
	});
});
