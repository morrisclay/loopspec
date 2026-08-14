import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { LoopSpecCliEngine } from "../src/loopspec-engine.js";

const here = dirname(fileURLToPath(import.meta.url));
const tutorialRoot = join(here, "..");
const repositoryRoot = join(tutorialRoot, "..", "..");
const engine = new LoopSpecCliEngine({
  executable: process.env.PYTHON ?? "python3",
  prefixArgs: [join(repositoryRoot, "tools", "loopspec.py")],
  cwd: repositoryRoot
});
const base = join(tutorialRoot, "loops", "support-triage.base.yaml");

describe("typed LoopSpec CLI engine", () => {
  it("checks, expands, and semantically compares through protocol v1", async () => {
    const [check, expansion, diff] = await Promise.all([
      engine.check(base),
      engine.expand(base),
      engine.diff(base, base)
    ]);

    expect(check.valid).toBe(true);
    expect(check.protocol_version).toBe(1);
    expect(expansion.valid && expansion.document.ir_revision).toBe("2.2");
    expect(diff.valid && diff.changed).toBe(false);
  });

  it("returns a typed invalid result instead of mistaking exit status 1 for transport failure", async () => {
    const directory = await mkdtemp(join(tmpdir(), "loopspec-node-client-"));
    const invalid = join(directory, "invalid.yaml");
    await writeFile(invalid, "loop: [not-valid\n");

    const result = await engine.check(invalid);

    expect(result.valid).toBe(false);
    if (!result.valid) expect(result.errors.length).toBeGreaterThan(0);
  });
});
