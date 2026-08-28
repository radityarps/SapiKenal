import { describe, expect, it } from "vitest";
import { backendFetch, bearerHeaders } from "./backend";

describe("backend client", () => {
	it("creates a bearer header without exposing token storage to browser code", () => {
		expect(bearerHeaders("opaque-session-token")).toEqual({
			authorization: "Bearer opaque-session-token",
		});
		expect(bearerHeaders(null)).toEqual({});
	});

	it("uses the request-scoped fetch supplied by a server load or action", async () => {
		let requestedUrl = "";
		const requestFetch = async (input: RequestInfo | URL) => {
			requestedUrl = String(input);
			return new Response("{}");
		};

		await backendFetch("/api/health", {}, requestFetch);

		expect(requestedUrl).toBe("http://localhost:8000/api/health");
	});

	it("serializes prediction queries with outcome and class filters", async () => {
		let requestedUrl = "";
		const requestFetch = async (input: RequestInfo | URL) => {
			requestedUrl = String(input);
			return new Response(JSON.stringify({ status: "success", items: [], total: 0 }));
		};

		const query = new URLSearchParams({
			page: "1",
			page_size: "25",
			outcome: "rejected",
			predicted_class: "non_cattle",
		});

		await backendFetch(`/api/admin/predictions?${query}`, {}, requestFetch);

		expect(requestedUrl).toBe(
			"http://localhost:8000/api/admin/predictions?page=1&page_size=25&outcome=rejected&predicted_class=non_cattle"
		);
	});
});
