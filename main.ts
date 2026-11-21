// SALMIRA v3 — copies the rendered poster into the output directory.
// The poster itself is entry.png, rendered by compose.py (PIL, deterministic).
// This program only copies one file; it never removes the output directory.
import { cpSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? join(here, "output");
mkdirSync(outDir, { recursive: true });
cpSync(join(here, "entry.png"), join(outDir, "entry.png"));
console.log("wrote entry.png to " + outDir);
