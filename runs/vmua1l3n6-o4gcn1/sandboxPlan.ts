export type SandboxKind = "python" | "pytest" | "node" | "npm_test" | "tsc";

export const SANDBOX_KINDS: readonly SandboxKind[] = [
  "python",
  "pytest",
  "node",
  "npm_test",
  "tsc",
] as const;

export interface SandboxFile {
  path: string;
  content: string;
}

export interface SandboxSpec {
  kind: SandboxKind;
  files: SandboxFile[];
  entry?: string;
  packages?: string[];
}

export const SANDBOX_LIMITS = {
  maxFiles: 30,
  maxFileChars: 100_000,
  maxTotalChars: 300_000,
  maxPackages: 12,
  maxPathChars: 200,
  outputChars: 6_000,
} as const;

const PATH_PATTERN = /^[A-Za-z0-9_.\-/@+]+$/;
const ENTRY_PATTERN = /^[A-Za-z0-9_.\-/]+$/;
const PACKAGE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*(?:[<>=~!]=?[A-Za-z0-9._*-]+)?$/;

export type SpecValidation = { ok: true; spec: SandboxSpec } | { ok: false; error: string };

function validatePath(path: string): string | null {
  if (!path) return "caminho vazio";
  if (path.length > SANDBOX_LIMITS.maxPathChars) return `caminho longo demais: ${path.slice(0, 40)}…`;
  if (!PATH_PATTERN.test(path)) return `caminho com caractere inválido: ${path}`;
  if (path.startsWith("/")) return `caminho não pode ser absoluto: ${path}`;
  if (path.split("/").some((seg) => seg === ".." || seg === "" || seg === ".git")) {
    return `caminho inválido: ${path}`;
  }
  if (path.startsWith(".github/") || path === ".github") return `caminho reservado: ${path}`;
  if (path === "run.sh") return "run.sh é reservado (gerado automaticamente)";
  return null;
}

export function validateSandboxSpec(input: SandboxSpec): SpecValidation {
  if (!SANDBOX_KINDS.includes(input.kind)) {
    return { ok: false, error: `kind inválido (use: ${SANDBOX_KINDS.join(", ")})` };
  }
  if (!input.files.length) return { ok: false, error: "envie pelo menos um arquivo" };
  if (input.files.length > SANDBOX_LIMITS.maxFiles) {
    return { ok: false, error: `arquivos demais (máx. ${SANDBOX_LIMITS.maxFiles})` };
  }

  const seen = new Set<string>();
  let total = 0;
  for (const f of input.files) {
    const pathError = validatePath(f.path);
    if (pathError) return { ok: false, error: pathError };
    if (seen.has(f.path)) return { ok: false, error: `arquivo repetido: ${f.path}` };
    seen.add(f.path);
    if (!f.content) return { ok: false, error: `arquivo vazio: ${f.path}` };
    if (f.content.length > SANDBOX_LIMITS.maxFileChars) {
      return { ok: false, error: `arquivo grande demais (máx. ${SANDBOX_LIMITS.maxFileChars} caracteres): ${f.path}` };
    }
    total += f.content.length;
  }
  if (total > SANDBOX_LIMITS.maxTotalChars) {
    return { ok: false, error: `total grande demais (máx. ${SANDBOX_LIMITS.maxTotalChars} caracteres)` };
  }

  const packages = input.packages ?? [];
  if (packages.length > SANDBOX_LIMITS.maxPackages) {
    return { ok: false, error: `pacotes demais (máx. ${SANDBOX_LIMITS.maxPackages})` };
  }
  for (const p of packages) {
    if (!PACKAGE_PATTERN.test(p)) return { ok: false, error: `nome de pacote inválido: ${p}` };
  }
  if (packages.length && input.kind !== "python" && input.kind !== "pytest") {
    return { ok: false, error: "packages só vale para python/pytest (Node usa package.json)" };
  }

  const needsEntry = input.kind === "python" || input.kind === "node";
  const defaultEntry = input.kind === "python" ? "main.py" : "index.js";
  const entry = input.entry ?? (needsEntry ? defaultEntry : undefined);
  if (entry !== undefined) {
    if (!ENTRY_PATTERN.test(entry) || validatePath(entry)) {
      return { ok: false, error: `entry inválido: ${entry}` };
    }
    if (needsEntry && !seen.has(entry)) {
      return { ok: false, error: `entry "${entry}" não está entre os arquivos enviados` };
    }
  }
  if (input.kind === "npm_test" && !seen.has("package.json")) {
    return { ok: false, error: "npm_test exige um package.json entre os arquivos" };
  }

  const spec: SandboxSpec = { kind: input.kind, files: input.files };
  if (entry !== undefined) spec.entry = entry;
  if (packages.length) spec.packages = packages;
  return { ok: true, spec };
}

export function excerptOutput(text: string, max: number): string {
  if (text.length <= max) return text;
  const marker = (n: number) => `\n[… ${n} caracteres omitidos …]\n`;
  const budget = max - marker(text.length).length;
  if (budget < 40) return text.slice(0, max);
  const head = Math.floor(budget * 0.4);
  const tail = budget - head;
  return `${text.slice(0, head)}${marker(text.length - head - tail)}${text.slice(text.length - tail)}`;
}
