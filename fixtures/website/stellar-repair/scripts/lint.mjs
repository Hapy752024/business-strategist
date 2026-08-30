import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

async function files(root) {
  const entries = await readdir(root, { withFileTypes: true });
  return (await Promise.all(entries.map((entry) => {
    const path = join(root, entry.name);
    return entry.isDirectory() ? files(path) : [path];
  }))).flat();
}

const forbidden = ["NEXT_PUBLIC_FAL", "NEXT_PUBLIC_API_KEY", "FAL_AI_API_KEY"];
const sourceFiles = (await files("app")).filter((file) => /\.(tsx|ts)$/.test(file));
const violations = [];
for (const file of sourceFiles) {
  const source = await readFile(file, "utf8");
  for (const token of forbidden) if (source.includes(token)) violations.push(`${file}: forbidden client-side secret marker ${token}`);
  if (source.includes("dangerouslySetInnerHTML")) violations.push(`${file}: unsafe HTML injection is prohibited in this fixture`);
}
if (violations.length) {
  console.error(violations.join("\n"));
  process.exit(1);
}
console.log(`Source lint passed (${sourceFiles.length} files checked)`);
