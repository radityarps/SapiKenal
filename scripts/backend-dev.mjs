#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { copyFileSync, existsSync, readFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const backend = resolve(root, "apps/backend");
const envPath = resolve(backend, ".env");
const envExamplePath = resolve(backend, ".env.example");

function parseEnvFile(filePath) {
	if (!existsSync(filePath)) return {};
	const content = readFileSync(filePath, "utf-8");
	const env = {};
	for (const line of content.split("\n")) {
		const trimmed = line.trim();
		if (!trimmed || trimmed.startsWith("#")) continue;
		const eqIndex = trimmed.indexOf("=");
		if (eqIndex === -1) continue;
		const key = trimmed.slice(0, eqIndex).trim();
		let val = trimmed.slice(eqIndex + 1).trim();
		if (
			(val.startsWith('"') && val.endsWith('"')) ||
			(val.startsWith("'") && val.endsWith("'"))
		) {
			val = val.slice(1, -1);
		}
		env[key] = val;
	}
	return env;
}

// Bootstrap .env from .env.example if missing
if (!existsSync(envPath) && existsSync(envExamplePath)) {
	copyFileSync(envExamplePath, envPath);
	console.log("Created apps/backend/.env from .env.example");
}

const fileEnv = {
	...parseEnvFile(envExamplePath),
	...parseEnvFile(envPath),
};

const activeFastapiEnv = process.env.FASTAPI_ENV ?? fileEnv.FASTAPI_ENV ?? "development";
const activeDebug = process.env.DEBUG ?? fileEnv.DEBUG ?? "true";

if (activeFastapiEnv !== "development") {
	console.error(
		`backend:dev requires FASTAPI_ENV=development (got "${activeFastapiEnv}"); refusing a destructive reset.`,
	);
	process.exit(1);
}
if (activeDebug.toLowerCase() !== "true") {
	console.error(
		`backend:dev requires DEBUG=true (got "${activeDebug}"); refusing a destructive reset.`,
	);
	process.exit(1);
}

const environment = {
	...fileEnv,
	...process.env,
	FASTAPI_ENV: "development",
	DEBUG: "true",
	DATABASE_URL: process.env.DATABASE_URL || fileEnv.DATABASE_URL || "sqlite:///./data/admin.sqlite3",
	ALLOW_DEV_DB_RESET: "true",
	MODEL_STARTUP_FALLBACK_ENABLED: "true",
};

if (!environment.DATABASE_URL.startsWith("sqlite:///")) {
	console.error(
		"backend:dev only resets a local SQLite database; refusing a non-SQLite DATABASE_URL.",
	);
	process.exit(1);
}

function sqlitePath(databaseUrl) {
	if (databaseUrl.includes(":memory:")) return null;
	const rawPath = databaseUrl.slice("sqlite:///".length);
	return rawPath.startsWith("/") ? rawPath : resolve(backend, rawPath);
}

function configuredPath(rawPath) {
	return rawPath.startsWith("/") ? rawPath : resolve(backend, rawPath);
}

function runCompose(args) {
	execFileSync("docker", ["compose", ...args], {
		cwd: backend,
		env: environment,
		stdio: "inherit",
	});
}

console.log("Resetting development backend containers and SQLite databases...");
runCompose(["down", "-v", "--remove-orphans"]);
for (const path of new Set([
	sqlitePath(environment.DATABASE_URL),
	configuredPath(environment.HISTORY_DB_PATH || "./data/history.sqlite3"),
])) {
	if (path) rmSync(path, { force: true });
}

console.log("Building backend image to apply dependency changes...");
runCompose(["build", "backend"]);
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
