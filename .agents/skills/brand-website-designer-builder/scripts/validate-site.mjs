#!/usr/bin/env node
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(process.argv[2] || "website");
const errors = [];
const required = ["source", "public", "tests", "screenshots", "qa"];
for (const directory of required) if (!existsSync(join(root, directory))) errors.push(`missing directory: ${directory}`);
const forbidden = /NEXT_PUBLIC_(?:FAL|OPENROUTER)|FAL_(?:AI_)?API_KEY\s*[:=]|queue\.fal\.run|v3b\.fal\.media/;
function walk(directory) {
  if (!existsSync(directory)) return;
  for (const name of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, name.name);
    if (name.isDirectory() && name.name !== ".next" && name.name !== "node_modules") walk(path);
    else if (name.isFile() && /\.(?:js|jsx|ts|tsx|json|css|html|md)$/.test(name.name) && forbidden.test(readFileSync(path, "utf8"))) errors.push(`secret or temporary FAL reference: ${path}`);
  }
}
walk(root);
const result = { root, status: errors.length ? "fail" : "pass", errors };
console.log(JSON.stringify(result, null, 2));
process.exitCode = errors.length ? 1 : 0;
