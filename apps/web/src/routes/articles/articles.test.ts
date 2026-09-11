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
		locale: "en-US",
		category: "app_usage",
		icon: "📖",
		sort_order: "10",
		title: "Identify cattle",
		summary: "A short guide.",
		body: "Use a clear image.",
		sources: "https://example.org/guide\n https://example.org/terms ",
	};
}

describe("Artikel Panduan page server", () => {
	it("forwards category, locale, publication, and revision filters", async () => {
		vi.mocked(backendJson).mockResolvedValueOnce({
			page: 2,
			page_size: 25,
			total: 0,
			items: [],
		});

		await load!({
			locals: { user: { id: "admin" }, sessionToken: "test-only" },
			url: new URL(
				"http://localhost/articles?page=2&category=bali&locale=en-US&publication_status=active&revision_status=draft",
			),
			fetch: vi.fn(),
		} as never);

		expect(backendJson).toHaveBeenCalledWith(
			"/api/admin/articles?page=2&page_size=25&category=bali&locale=en-US&publication_status=active&revision_status=draft",
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
								locale: "id-ID",
								publication_status: "active",
								revision: {
									revision: 2,
									status: "draft",
									category: "bali",
									icon: "🐄",
									title: "Draft terbaru",
									summary: "Ringkasan",
									content_reviewed: false,
								},
								active_revision: { revision: 1 },
								locale_pair: { locale: "en-US", status: "active" },
							},
						],
					},
					filters: {
						category: "",
						locale: "",
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
					icon: "📖",
					sort_order: 10,
					title: "Updated title",
					summary: "A short guide.",
					body: "Use a clear image.",
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

	it("detects locale-pair metadata independently of the filtered page", async () => {
		vi.mocked(backendJson).mockResolvedValueOnce({
			items: [
				{
					article_key: "bali_1",
					locale: "id-ID",
					locale_pair: { locale: "en-US", status: "active" },
				},
			],
		});
		const result = await load!({
			locals: { user: { id: "admin" }, sessionToken: "test-only" },
			url: new URL("http://localhost/articles?locale=id-ID"),
			fetch: vi.fn(),
		} as never);
		expect((result as any).articles.items[0].locale_pair).toEqual({
			locale: "en-US",
			status: "active",
		});
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
