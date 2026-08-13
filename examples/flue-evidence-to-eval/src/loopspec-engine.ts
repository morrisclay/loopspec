import { spawn } from "node:child_process";

import type { JsonValue } from "./types.js";

export const LOOPSPEC_CLI_PROTOCOL_VERSION = 1;

interface ProtocolEnvelope {
  protocol_version: number;
  valid: boolean;
}

export interface LoopSpecFinding {
  pattern: string;
  assurance: string;
  claim: string;
  repair?: string;
  evidence: Record<string, JsonValue>;
  [key: string]: JsonValue | undefined;
}

export interface LoopSpecFailure extends ProtocolEnvelope {
  valid: false;
  errors: string[];
}

export interface LoopSpecCheckSuccess extends ProtocolEnvelope {
  valid: true;
  spec: string;
  encodes: string;
  ir_version: number;
  ir_revision: string;
  errors: string[];
  warnings: string[];
  deprecations: string[];
  findings: LoopSpecFinding[];
}

export type LoopSpecCheckResult = LoopSpecCheckSuccess | LoopSpecFailure;

export interface CanonicalLoopSpec {
  loopspec_version: number;
  ir_revision: string;
  encodes: string;
  nodes: Array<Record<string, JsonValue>>;
  edges: Array<Record<string, JsonValue>>;
  loops: Array<Record<string, JsonValue>>;
  [key: string]: JsonValue;
}

export interface LoopSpecExpandSuccess extends ProtocolEnvelope {
  valid: true;
  spec: string;
  warnings: string[];
  findings: LoopSpecFinding[];
  document: CanonicalLoopSpec;
}

export type LoopSpecExpandResult = LoopSpecExpandSuccess | LoopSpecFailure;

export interface LoopSpecDiffSuccess extends ProtocolEnvelope {
  valid: true;
  changed: boolean;
  left: { spec: string; encodes: string; ir_revision: string; semantic_hash: string };
  right: { spec: string; encodes: string; ir_revision: string; semantic_hash: string };
  summary: Record<string, number>;
  document: Record<string, JsonValue>;
  nodes: Record<string, JsonValue>;
  edges: Record<string, JsonValue>;
  loops: Record<string, JsonValue>;
  findings: Record<string, JsonValue>;
}

export type LoopSpecDiffResult = LoopSpecDiffSuccess | LoopSpecFailure;

export interface LoopSpecEngine {
  check(spec: string): Promise<LoopSpecCheckResult>;
  expand(spec: string): Promise<LoopSpecExpandResult>;
  diff(before: string, after: string): Promise<LoopSpecDiffResult>;
}

export interface LoopSpecCliOptions {
  executable?: string;
  prefixArgs?: string[];
  cwd?: string;
  env?: NodeJS.ProcessEnv;
}

export class LoopSpecCliError extends Error {
  constructor(
    message: string,
    readonly exitCode: number | null,
    readonly stderr: string
  ) {
    super(message);
    this.name = "LoopSpecCliError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertEnvelope(value: unknown): asserts value is ProtocolEnvelope {
  if (!isRecord(value)) throw new LoopSpecCliError("LoopSpec returned non-object JSON", null, "");
  if (value.protocol_version !== LOOPSPEC_CLI_PROTOCOL_VERSION) {
    throw new LoopSpecCliError(
      `Unsupported LoopSpec CLI protocol ${String(value.protocol_version)}`,
      null,
      ""
    );
  }
  if (typeof value.valid !== "boolean") {
    throw new LoopSpecCliError("LoopSpec response has no validity marker", null, "");
  }
}

export class LoopSpecCliEngine implements LoopSpecEngine {
  readonly executable: string;
  readonly prefixArgs: string[];
  readonly cwd: string | undefined;
  readonly env: NodeJS.ProcessEnv;

  constructor(options: LoopSpecCliOptions = {}) {
    this.executable = options.executable ?? "loopspec";
    this.prefixArgs = options.prefixArgs ?? [];
    this.cwd = options.cwd;
    this.env = { ...process.env, ...options.env, PYTHONDONTWRITEBYTECODE: "1" };
  }

  async check(spec: string): Promise<LoopSpecCheckResult> {
    return this.run<LoopSpecCheckResult>(["check", spec, "--json"]);
  }

  async expand(spec: string): Promise<LoopSpecExpandResult> {
    return this.run<LoopSpecExpandResult>(["expand", spec, "--json"]);
  }

  async diff(before: string, after: string): Promise<LoopSpecDiffResult> {
    return this.run<LoopSpecDiffResult>(["diff", before, after, "--json"]);
  }

  private run<T extends ProtocolEnvelope>(args: string[]): Promise<T> {
    return new Promise((resolve, reject) => {
      const child = spawn(this.executable, [...this.prefixArgs, ...args], {
        cwd: this.cwd,
        env: this.env,
        stdio: ["ignore", "pipe", "pipe"]
      });
      let stdout = "";
      let stderr = "";
      child.stdout.setEncoding("utf8");
      child.stderr.setEncoding("utf8");
      child.stdout.on("data", (chunk: string) => {
        stdout += chunk;
      });
      child.stderr.on("data", (chunk: string) => {
        stderr += chunk;
      });
      child.on("error", (error) => {
        reject(new LoopSpecCliError(error.message, null, stderr));
      });
      child.on("close", (code) => {
        let value: unknown;
        try {
          value = JSON.parse(stdout);
          assertEnvelope(value);
        } catch (error) {
          reject(
            error instanceof LoopSpecCliError
              ? error
              : new LoopSpecCliError("LoopSpec returned invalid JSON", code, stderr)
          );
          return;
        }
        if (code !== 0 && value.valid) {
          reject(new LoopSpecCliError("LoopSpec command failed", code, stderr));
          return;
        }
        resolve(value as T);
      });
    });
  }
}
