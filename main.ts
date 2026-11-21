// SALMIRA v2 — writes the rendered poster to the grader's output dir.
// The image is rendered by compose.py (PIL, deterministic); this program
// only copies it into $MAKEFUN_OUTPUT_DIR as entry.png.
import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? join(here, "output");
mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));
console.log("wrote entry.png");
