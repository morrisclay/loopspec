import { createHash } from "node:crypto";

/** Stable projection for correlation identifiers that may embed provider resource names. */
export function digestIdentifier(value: string): string {
  return `sha256:${createHash("sha256").update(value).digest("hex").slice(0, 32)}`;
}
