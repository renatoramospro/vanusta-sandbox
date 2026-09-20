/**
 * Guarda de segredos: roda ANTES de qualquer código subir para o repositório
 * PÚBLICO de execução (vanusta-sandbox). Regras conservadoras (formatos
 * conhecidos de chave/token, .env, credencial atribuída, URL com senha) — de
 * propósito não tenta pegar tudo, só o que quase certamente é segredo real,
 * pra não barrar exemplo didático com valor de mentira.
 */
import type { SandboxFile } from "./sandboxPlan";

export interface SecretFinding {
  path: string;
  reason: string;
}

const KEY_RULES: readonly { reason: string; pattern: RegExp }[] = [
  { reason: "chave privada", pattern: /-----BEGIN [A-Z ]*PRIVATE KEY-----/ },
  { reason: "chave de acesso AWS", pattern: /\bAKIA[0-9A-Z]{16}\b/ },
  {
    reason: "token do GitHub",
    pattern: /\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b/,
  },
  { reason: "chave de API (formato sk-)", pattern: /\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}/ },
  { reason: "token do Slack", pattern: /\bxox[baprs]-[A-Za-z0-9-]{10,}/ },
  { reason: "chave de API do Google", pattern: /\bAIza[0-9A-Za-z_-]{35}/ },
  {
    reason: "JWT",
    pattern: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/,
  },
];

const ENV_FILE = /(^|\/)\.env(\.[A-Za-z0-9_-]+)?$/;
const ENV_TEMPLATE = /\.(example|sample|template)$/i;

const ASSIGNMENT =
  /(?:api[_-]?key|secret|passw(?:or)?d|token|credential)[A-Za-z0-9_]*\s*[:=]\s*["']([^"'\s]{20,})["']/gi;
const ASSIGNMENT_PLACEHOLDER = /(?:your|example|placeholder|dummy|fake|changeme|xxx|test)/i;

const CREDENTIAL_URL = /\b[a-z][a-z0-9+.-]*:\/\/([^\s:@\/'"]+):([^\s@\/'"]+)@[^\s'"\/]+/gi;
const PLACEHOLDER_PASSWORD =
  /^(?:pass(?:word)?|secret|changeme|example|test|[0-9]{4,8}|x{3,}|\*+|<[^>]*>|\$\{?[A-Za-z_]+\}?)$/i;

function looksLikeRealValue(value: string): boolean {
  return /[A-Za-z]/.test(value) && /[0-9]/.test(value) && !ASSIGNMENT_PLACEHOLDER.test(value);
}

/** Primeiro achado suspeito nos arquivos, ou null se nada parece segredo. */
export function findSecretLikeContent(files: readonly SandboxFile[]): SecretFinding | null {
  for (const file of files) {
    if (ENV_FILE.test(file.path) && !ENV_TEMPLATE.test(file.path)) {
      return { path: file.path, reason: "arquivo .env" };
    }
    for (const rule of KEY_RULES) {
      if (rule.pattern.test(file.content)) return { path: file.path, reason: rule.reason };
    }
    for (const match of file.content.matchAll(ASSIGNMENT)) {
      if (looksLikeRealValue(match[1] ?? "")) {
        return { path: file.path, reason: "credencial atribuída no código" };
      }
    }
    for (const match of file.content.matchAll(CREDENTIAL_URL)) {
      if (!PLACEHOLDER_PASSWORD.test(match[2] ?? "")) {
        return { path: file.path, reason: "URL com usuário e senha" };
      }
    }
  }
  return null;
}

export function secretGuardMessage(finding: SecretFinding): string {
  return (
    `possível segredo em "${finding.path}" (${finding.reason}) — o repositório de execução é PÚBLICO, ` +
    "então nada foi enviado"
  );
}
