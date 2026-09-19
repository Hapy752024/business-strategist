#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const output = process.argv[2] || "";
if (output) {
  const bridge = fileURLToPath(new URL('../../../../scripts/case_output_command.py', import.meta.url));
  if (execFileSync('python3', [bridge, '--inspect', '--destination', resolve(output)], {encoding:'utf8'}).trim() === 'managed') {
    execFileSync('python3', [bridge, '--file', '--destination', resolve(output), '--', process.execPath, fileURLToPath(import.meta.url), resolve(output)], {stdio:'inherit'});
    process.exit(0);
  }
}
const version = execFileSync("npm", ["view", "next@latest", "version", "--json"], { encoding: "utf8" }).trim().replace(/^\"|\"$/g, "");
if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error(`next@latest is not a stable semver: ${version}`);
const result = {
  next: version,
  source: "https://registry.npmjs.org/next/latest",
  docs: "https://nextjs.org/docs/app/getting-started/installation",
  resolved_at: new Date().toISOString(),
  prerelease_rejected: true,
};
if (output) writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
