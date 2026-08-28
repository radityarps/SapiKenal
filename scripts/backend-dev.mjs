#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = resolve(root, "apps/backend");

if (process.env.FASTAPI_ENV && process.env.FASTAPI_ENV !== "development") {
	console.error(
		"backend:dev requires FASTAPI_ENV=development; refusing a destructive reset.",
	);
	process.exit(1);
}
if (process.env.DEBUG && process.env.DEBUG.toLowerCase() !== "true") {
	console.error(
		"backend:dev requires DEBUG=true; refusing a destructive reset.",
	);
	process.exit(1);
}

const environment = {
	...process.env,
	FASTAPI_ENV: "development",
	DEBUG: "true",
	DATABASE_URL: process.env.DATABASE_URL || "sqlite:///./data/admin.sqlite3",
};

if (!environment.DATABASE_URL.startsWith("sqlite:")) {
	console.error(
		"backend:dev only resets a local SQLite database; refusing a non-SQLite DATABASE_URL.",
	);
	process.exit(1);
}

function runCompose(args) {
	execFileSync("docker", ["compose", ...args], {
		cwd: backend,
		env: environment,
		stdio: "inherit",
	});
}

function composeImage() {
	return execFileSync("docker", ["compose", "config", "--images"], {
		cwd: backend,
		env: environment,
		encoding: "utf8",
	})
		.trim()
		.split("\n")[0];
}

console.log("Resetting development backend containers and SQLite databases...");
runCompose(["down", "-v", "--remove-orphans"]);
for (const filename of ["admin.sqlite3", "history.sqlite3"]) {
	rmSync(resolve(backend, "data", filename), { force: true });
}

const image = composeImage();
try {
	execFileSync("docker", ["image", "inspect", image], { stdio: "ignore" });
} catch {
	console.log(`Backend image ${image} is missing; building it once...`);
	runCompose(["build", "backend"]);
}
runCompose(["run", "--rm", "backend", "python", "-m", "scripts.init_dev_db"]);
runCompose([
	"run",
	"--rm",
	"backend",
	"sh",
	"-c",
	'if [ -n "$ADMIN_EMAIL" ] && [ -n "$ADMIN_PASSWORD" ] && [ -n "$ADMIN_NAME" ]; then python -m scripts.seed_admin --allow-weak-password; else echo "ADMIN_* not set; skipping admin seeder"; fi',
]);
runCompose(["up", "--force-recreate", "-d"]);
console.log(
	"Development backend is running with FASTAPI_ENV=development and DEBUG=true.",
);
