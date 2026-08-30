#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(process.argv[2] || "website");
const run = process.argv.includes("--run");
if (existsSync(root) && process.argv.includes("--refuse-nonempty") && readdirSync(root).length) {
  throw new Error(`refusing non-empty target: ${root}`);
}
mkdirSync(root, { recursive: true });
const command = "pnpm create next-app@latest source --ts --eslint --tailwind --app --src-dir --use-pnpm --import-alias '@/*'";
writeFileSync(join(root, "scaffold-command.txt"), `${command}\n`);
if (run) {
  if (process.env.CONFIRM_INSTALL !== "1") throw new Error("set CONFIRM_INSTALL=1 to install the selected stack");
  // next-app requires an empty target; create support folders only after it finishes.
  if (existsSync(join(root, "source")) && readdirSync(join(root, "source")).length) {
    throw new Error(`refusing non-empty source target: ${join(root, "source")}`);
  }
  execFileSync("pnpm", ["create", "next-app@latest", "source", "--ts", "--eslint", "--tailwind", "--app", "--src-dir", "--use-pnpm", "--import-alias", "@/*"], { cwd: root, stdio: "inherit" });
  mkdirSync(join(root, "public"), { recursive: true });
  mkdirSync(join(root, "tests"), { recursive: true });
  mkdirSync(join(root, "screenshots"), { recursive: true });
  mkdirSync(join(root, "qa"), { recursive: true });
} else {
  mkdirSync(join(root, "source", "app"), { recursive: true });
  mkdirSync(join(root, "public"), { recursive: true });
  mkdirSync(join(root, "tests"), { recursive: true });
  mkdirSync(join(root, "screenshots"), { recursive: true });
  mkdirSync(join(root, "qa"), { recursive: true });
  console.log(JSON.stringify({ root, command, next_step: "review website-preferences.json and run the recorded command after approval" }, null, 2));
}
