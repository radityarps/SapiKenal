#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const mobileDir = resolve(__dirname, "../apps/mobile");
const isWin = process.platform === "win32";
const gradlewCmd = isWin ? "gradlew.bat" : "./gradlew";

const env = { ...process.env };
if (isWin) {
  if (!env.JAVA_HOME) {
    const candidateJava = [
      "C:\\Program Files\\Android\\Android Studio\\jbr",
      "C:\\Program Files\\Java\\jdk-25.0.4.1",
      "C:\\Program Files\\Java\\latest",
    ];
    for (const p of candidateJava) {
      if (existsSync(p)) {
        env.JAVA_HOME = p;
        break;
      }
    }
  }

  if (!env.ANDROID_HOME) {
    const defaultSdk = resolve(
      process.env.LOCALAPPDATA || "C:\\Users\\Raditya\\AppData\\Local",
      "Android\\Sdk",
    );
    if (existsSync(defaultSdk)) {
      env.ANDROID_HOME = defaultSdk;
    }
  }
}

const args = process.argv.slice(2);
const result = spawnSync(gradlewCmd, args, {
  cwd: mobileDir,
  stdio: "inherit",
  shell: isWin,
  env,
});

process.exit(result.status ?? 1);
