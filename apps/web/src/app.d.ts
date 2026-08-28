declare global {
	namespace App {
		interface Locals {
			user: {
				id: string;
				email: string;
				display_name: string;
				role: string;
				status: string;
				must_change_password: boolean;
			} | null;
			sessionToken: string | null;
		}
	}
}

export {};
