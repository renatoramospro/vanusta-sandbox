import {
  excerptOutput,
  validateSandboxSpec,
  type SandboxFile,
  type SandboxKind,
  type SandboxSpec,
} from "./sandboxPlan";

export type SandboxMetaStatus = "pending" | "completed" | "skipped" | "error";

export interface SandboxMeta {
  status: SandboxMetaStatus;
  runId?: string;
  kind?: SandboxKind;
  files?: string[];
  startedAt?: string;
  reason?: string;
  passed?: boolean;
  exitCode?: number | null;
  started?: boolean;
  ended?: boolean;
  output?: string;
  url?: string | null;
}

export type SandboxOutcome = "passed" | "failed" | "inconclusive" | "none";

export interface SandboxSummary {
  outcome: SandboxOutcome;
  status: SandboxMetaStatus;
  kind: SandboxKind | null;
  runId: string | null;
  url: string | null;
  exitCode: number | null;
  note: string;
}

export const SANDBOX_META_OPEN = "<!--VANUSTA_SANDBOX ";
const MARKER_CLOSE = " -->";
const META_STATUSES: readonly string[] = ["pending", "completed", "skipped", "error"];

function serializeMeta(meta: SandboxMeta): string {
  return JSON.stringify(meta).replace(/</g, "\\u003c").replace(/>/g, "\\u003e");
}

function isMeta(value: unknown): value is SandboxMeta {
  if (typeof value !== "object" || value === null) return false;
  const status = (value as Record<string, unknown>)["status"];
  return typeof status === "string" && META_STATUSES.includes(status);
}

export function parseSandboxMeta(body: string): { main: string; meta: SandboxMeta | null } {
  const start = body.lastIndexOf(SANDBOX_META_OPEN);
  if (start === -1) return { main: body, meta: null };
  const end = body.indexOf(MARKER_CLOSE, start + SANDBOX_META_OPEN.length);
  if (end === -1) return { main: body, meta: null };
  const main = body.slice(0, start).trimEnd();
  try {
    const parsed: unknown = JSON.parse(body.slice(start + SANDBOX_META_OPEN.length, end));
    return isMeta(parsed) ? { main, meta: parsed } : { main, meta: null };
  } catch {
    return { main, meta: null };
  }
}

export function stripSandboxMeta(body: string): string {
  return parseSandboxMeta(body).main;
}

export function withSandboxMeta(body: string, meta: SandboxMeta): string {
  const main = parseSandboxMeta(body)
    .main.split(SANDBOX_META_OPEN)
    .join("<!--(marcador removido) ");
  return `${main}\n\n${SANDBOX_META_OPEN}${serializeMeta(meta)}${MARKER_CLOSE}`;
}

export function isPendingStale(
  meta: SandboxMeta,
  maxAgeMs: number = 20 * 60 * 1000,
  now: number = Date.now(),
): boolean {
  if (meta.status !== "pending" || !meta.startedAt) return false;
  const started = Date.parse(meta.startedAt);
  return Number.isFinite(started) && now - started > maxAgeMs;
}

const FENCE_RE = /^```([^\n]*)\n([\s\S]*?)^```[ \t]*$/gm;
const PATH_ATTR_RE = /(?:^|\s)path=(?:"([^"\n]+)"|'([^'\n]+)'|(\S+))/;

export function extractPathBlocks(body: string): { files: SandboxFile[]; unlabeled: number } {
  const byPath = new Map<string, string>();
  let unlabeled = 0;
  for (const match of body.matchAll(FENCE_RE)) {
    const info = match[1] ?? "";
    const attr = PATH_ATTR_RE.exec(info);
    const raw = attr ? (attr[1] ?? attr[2] ?? attr[3] ?? "") : "";
    if (!raw) {
      unlabeled++;
      continue;
    }
    const path = raw.replace(/^\.\//, "");
    const content = (match[2] ?? "").replace(/\n$/, "");
    byPath.set(path, content);
  }
  return { files: [...byPath.entries()].map(([path, content]) => ({ path, content })), unlabeled };
}

const TEST_PY_RE = /(^|\/)(test_[^/]+\.py|[^/]+_test\.py)$/;

function readPackages(requirements: string): string[] {
  return requirements
    .split("\n")
    .map((line) => line.replace(/\s+#.*$/, "").trim())
    .filter((line) => line && !line.startsWith("#") && !line.startsWith("-"));
}

function packageJsonHasTest(content: string): boolean {
  try {
    const pkg: unknown = JSON.parse(content);
    if (typeof pkg !== "object" || pkg === null) return false;
    const scripts = (pkg as Record<string, unknown>)["scripts"];
    if (typeof scripts !== "object" || scripts === null) return false;
    const test = (scripts as Record<string, unknown>)["test"];
    return typeof test === "string" && test.trim().length > 0;
  } catch {
    return false;
  }
}

export type SpecBuild = { ok: true; spec: SandboxSpec } | { ok: false; reason: string };

export function buildSandboxSpec(body: string): SpecBuild {
  const { files: all, unlabeled } = extractPathBlocks(body);
  if (!all.length) {
    return {
      ok: false,
      reason: unlabeled
        ? `${unlabeled} bloco(s) de código sem o atributo path= — só blocos com path= são executados`
        : "nenhum bloco de código com path= na resposta (normal em missões sem código)",
    };
  }

  const requirements = all.find((f) => f.path === "requirements.txt");
  const files = all.filter((f) => f.path !== "requirements.txt");
  const packages = requirements ? readPackages(requirements.content) : [];
  const paths = files.map((f) => f.path);
  const contentOf = new Map(files.map((f) => [f.path, f.content] as const));

  const py = paths.filter((p) => p.endsWith(".py"));
  const js = paths.filter((p) => /\.(m|c)?js$/.test(p));
  const ts = paths.filter((p) => /\.tsx?$/.test(p));
  const packageJson = contentOf.get("package.json");

  let spec: SandboxSpec;
  if (py.some((p) => TEST_PY_RE.test(p))) {
    spec = { kind: "pytest", files, ...(packages.length ? { packages } : {}) };
  } else if (py.length) {
    const only = py.length === 1 ? py[0] : undefined;
    const entry = paths.includes("main.py") ? "main.py" : only;
    if (entry === undefined) {
      return { ok: false, reason: "vários arquivos .py e nenhum main.py — não há como saber qual executar" };
    }
    spec = { kind: "python", files, entry, ...(packages.length ? { packages } : {}) };
  } else if (packageJson !== undefined && packageJsonHasTest(packageJson)) {
    spec = { kind: "npm_test", files };
  } else if (js.length) {
    const only = js.length === 1 ? js[0] : undefined;
    const entry = paths.includes("index.js") ? "index.js" : only;
    if (entry === undefined) {
      return { ok: false, reason: "vários arquivos .js e nenhum index.js — não há como saber qual executar" };
    }
    spec = { kind: "node", files, entry };
  } else if (ts.length && paths.includes("tsconfig.json")) {
    spec = { kind: "tsc", files };
  } else {
    return {
      ok: false,
      reason:
        "os arquivos entregues não formam nada executável (esperado: .py, .js, package.json com script test, ou .ts com tsconfig.json)",
    };
  }

  const validation = validateSandboxSpec(spec);
  return validation.ok ? { ok: true, spec: validation.spec } : { ok: false, reason: validation.error };
}

export function sandboxOutcome(meta: SandboxMeta | null): SandboxOutcome {
  if (!meta) return "none";
  if (meta.status === "pending") return "inconclusive";
  if (meta.status !== "completed") return "none";
  if (meta.started !== true) return "inconclusive";
  return meta.ended === true && meta.exitCode === 0 ? "passed" : "failed";
}

export function sandboxContextLine(meta: SandboxMeta | null): string {
  const prefix = "Verificação por execução real: ";
  if (!meta) return `${prefix}nenhuma (o Programador não entregou experimento executável).`;
  if (meta.status === "skipped") return `${prefix}não executado (${meta.reason ?? "sem motivo informado"}).`;
  if (meta.status === "error") return `${prefix}não foi possível executar (${meta.reason ?? "erro"}).`;
  if (meta.status === "pending") return `${prefix}execução iniciada, sem resultado até aqui.`;
  const outcome = sandboxOutcome(meta);
  const kind = meta.kind ?? "preset desconhecido";
  if (outcome === "passed") return `${prefix}PASSOU (${kind}, código de saída 0).`;
  if (outcome === "inconclusive") return `${prefix}inconclusiva (falha de infraestrutura).`;
  return meta.ended === true
    ? `${prefix}FALHOU (${kind}, código de saída ${meta.exitCode ?? "desconhecido"}).`
    : `${prefix}FALHOU (${kind}, não terminou no tempo limite).`;
}
