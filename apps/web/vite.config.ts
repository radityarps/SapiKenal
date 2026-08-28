import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";

export default defineConfig({
	// Tailwind's Vite plugin and SvelteKit resolve compatible Vite versions
	// through different pnpm peer paths; the runtime plugin contract is identical.
	plugins: [tailwindcss() as any, sveltekit()],
});
