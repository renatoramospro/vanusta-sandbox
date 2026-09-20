/**
 * Lê, do TEXTO do contexto de um item de conhecimento, o resultado da
 * verificação por execução real (a linha que sandboxContextLine anexa no FIM
 * do contexto). Só vale a ÚLTIMA linha do texto — um trecho parecido no meio
 * da resposta de um modelo não conta. Sem coluna nova: itens antigos, sem a
 * linha, ficam "none".
 */
export type ContextExecutionVerdict = "passed" | "failed" | "none";

export const EXECUTION_LINE_PREFIX = "Verificação por execução real: ";

export function executionVerdictFromContext(
  context: string | null | undefined,
): ContextExecutionVerdict {
  if (!context) return "none";
  const text = context.trimEnd();
  const start = text.lastIndexOf(EXECUTION_LINE_PREFIX);
  if (start === -1) return "none";
  const line = text.slice(start + EXECUTION_LINE_PREFIX.length);
  if (line.includes("\n")) return "none";
  if (line.startsWith("PASSOU")) return "passed";
  if (line.startsWith("FALHOU")) return "failed";
  return "none";
}
