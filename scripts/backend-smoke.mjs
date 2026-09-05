#!/usr/bin/env node

import { spawnSync } from "node:child_process";

const environment = {
	...process.env,
	FASTAPI_ENV: "development",
	DEBUG: "true",
};

function run(command, args) {
	const result = spawnSync(command, args, {
		env: environment,
		stdio: "inherit",
	});
	if (result.error) throw result.error;
	if (result.status !== 0) process.exit(result.status ?? 1);
}

// backend:dev is deliberately development-only: it resets only local SQLite,
// enables the checked-in best.keras fallback, and starts the backend container.
run("pnpm", ["run", "backend:dev"]);
run("python", ["apps/backend/scripts/smoke_production.py"]);
