import { render } from "svelte/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockEnv = {
	ENV: "development",
	ADMIN_EMAIL: "admin@example.com",
	ADMIN_PASSWORD: "password",
	BACKEND_INTERNAL_URL: "http://localhost:8000",
};

let mockDev = true;

vi.mock("$app/environment", () => ({
	get dev() {
		return mockDev;
	},
}));

vi.mock("$env/dynamic/private", () => ({
	get env() {
		return mockEnv;
	},
}));

vi.mock("$lib/server/backend", () => ({
	backendJson: vi.fn().mockResolvedValue({
		session_token: "test-token",
		expires_at: "2026-12-31T23:59:59Z",
		user: { id: "admin-1", email: "admin@example.com" },
	}),
}));

import { backendJson } from "$lib/server/backend";
import Page from "./+page.svelte";
import { actions, load } from "./+page.server";

beforeEach(() => {
	vi.clearAllMocks();
	mockDev = true;
	mockEnv.ENV = "development";
	mockEnv.ADMIN_EMAIL = "admin@example.com";
	mockEnv.ADMIN_PASSWORD = "password";
});

describe("Login page server", () => {
	it("redirects to /dashboard if user is already authenticated", () => {
		expect(() =>
			load({ locals: { user: { id: "admin" } } } as never),
		).toThrow();

		try {
			load({ locals: { user: { id: "admin" } } } as never);
		} catch (redirectError: any) {
			expect(redirectError.status).toBe(303);
			expect(redirectError.location).toBe("/dashboard");
		}
	});

	it("returns default admin credentials when ENV is development", () => {
		mockEnv.ENV = "development";
		const result = load({ locals: { user: null } } as never);
		expect(result).toEqual({
			defaultEmail: "admin@example.com",
			defaultPassword: "password",
		});
	});

	it("returns custom admin credentials from env when ENV is development", () => {
		mockEnv.ENV = "development";
		mockEnv.ADMIN_EMAIL = "superadmin@sapikenal.id";
		mockEnv.ADMIN_PASSWORD = "custom-password-123";
		const result = load({ locals: { user: null } } as never);
		expect(result).toEqual({
			defaultEmail: "superadmin@sapikenal.id",
			defaultPassword: "custom-password-123",
		});
	});

	it("returns default credentials when dev is true and ENV is not production", () => {
		mockEnv.ENV = "";
		mockDev = true;
		const result = load({ locals: { user: null } } as never);
		expect(result).toEqual({
			defaultEmail: "admin@example.com",
			defaultPassword: "password",
		});
	});

	it("returns empty credentials when ENV is production", () => {
		mockEnv.ENV = "production";
		mockDev = false;
		const result = load({ locals: { user: null } } as never);
		expect(result).toEqual({
			defaultEmail: "",
			defaultPassword: "",
		});
	});

	it("returns empty credentials even if dev is true when ENV is explicitly production", () => {
		mockEnv.ENV = "production";
		mockDev = true;
		const result = load({ locals: { user: null } } as never);
		expect(result).toEqual({
			defaultEmail: "",
			defaultPassword: "",
		});
	});

	it("fails with 400 if email or password is missing on submit", async () => {
		const cookies = { set: vi.fn() };
		const request = new Request("http://localhost/login", {
			method: "POST",
			body: new URLSearchParams({ email: "", password: "" }),
		});

		const result = await actions.default({
			request,
			cookies,
			fetch: vi.fn(),
		} as never);

		expect(result).toMatchObject({
			status: 400,
			data: expect.objectContaining({
				message: expect.stringContaining("wajib diisi"),
			}),
		});
		expect(backendJson).not.toHaveBeenCalled();
	});

	it("sets session cookie and redirects to dashboard on successful login", async () => {
		const cookies = { set: vi.fn() };
		const request = new Request("http://localhost/login", {
			method: "POST",
			body: new URLSearchParams({
				email: "admin@example.com",
				password: "password",
			}),
		});

		await expect(
			actions.default({ request, cookies, fetch: vi.fn() } as never),
		).rejects.toMatchObject({
			status: 303,
			location: "/dashboard?toast=Login%20berhasil",
		});

		expect(backendJson).toHaveBeenCalledWith(
			"/api/auth/login",
			expect.objectContaining({
				method: "POST",
				body: JSON.stringify({
					email: "admin@example.com",
					password: "password",
				}),
			}),
			expect.any(Function),
		);
		expect(cookies.set).toHaveBeenCalledWith(
			"sapikenal_session",
			"test-token",
			expect.objectContaining({
				path: "/",
				httpOnly: true,
				sameSite: "lax",
			}),
		);
	});
});

describe("Login page component", () => {
	it("renders with pre-filled default admin credentials in development", () => {
		const { body } = render(Page, {
			props: {
				data: {
					defaultEmail: "admin@example.com",
					defaultPassword: "password",
				},
				form: null,
			},
		});

		expect(body).toContain('value="admin@example.com"');
		expect(body).toContain('value="password"');
	});

	it("renders empty input values when credentials are empty", () => {
		const { body } = render(Page, {
			props: {
				data: {
					defaultEmail: "",
					defaultPassword: "",
				},
				form: null,
			},
		});

		expect(body).toContain('value=""');
		expect(body).not.toContain('value="admin@example.com"');
		expect(body).not.toContain('value="password"');
	});

	it("prioritizes submitted email from form over defaultEmail on validation failure", () => {
		const { body } = render(Page, {
			props: {
				data: {
					defaultEmail: "admin@example.com",
					defaultPassword: "password",
				},
				form: {
					message: "Kredensial salah",
					email: "user-input@example.com",
				},
			},
		});

		expect(body).toContain('value="user-input@example.com"');
		expect(body).toContain("Kredensial salah");
	});
});
