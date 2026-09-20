/**
 * Execução real de código entregue numa RESPOSTA do chat do Lab (ou do `ask` com
 * token de escrita) — parte PURA. A I/O está em labExecution.server.ts.
 */
import { excerptOutput } from "./sandboxPlan";
import { sandboxOutcome, type SandboxMeta } from "./sandboxLearning";

/** Quanto, no máximo, a resposta espera o resultado (poll a cada 10 s). */
export const LAB_EXEC_WAIT_CAP_MS = 75_000;
/** Orçamento total da requisição — proxies costumam cortar perto de 100 s. */
export const LAB_REQUEST_BUDGET_MS = 90_000;
const SECTION_OUTPUT_CHARS = 1_500;

/** Espera disponível depois de `elapsedMs` já gastos na requisição. */
export function labExecutionWaitMs(elapsedMs: number): number {
  return Math.max(
    0,
    Math.min(LAB_EXEC_WAIT_CAP_MS, LAB_REQUEST_BUDGET_MS - Math.max(0, elapsedMs)),
  );
}

/** Entra no preamble só quando a pergunta é de programação e não há projeto no contexto. */
export const SANDBOX_ANSWER_HINT =
  "Você pode verificar código de verdade. Quando a resposta incluir um exemplo executável pequeno e autocontido " +
  "(Python, JavaScript/Node ou testes pytest), entregue-o em blocos cercados por três crases com o caminho depois " +
  'da linguagem, assim: "```python path=main.py". Esses blocos serão EXECUTADOS de verdade num ambiente descartável e ' +
  "o resultado real aparece abaixo da sua resposta — então o exemplo deve terminar com código de saída 0 e imprimir o " +
  "que demonstra. Regras: (1) só exemplo sintético escrito por você — nunca inclua segredo, credencial, dado pessoal do " +
  "usuário nem código de projeto dele, porque o repositório de execução é PÚBLICO; (2) use path= só no código que " +
  "você quer que rode — trechos apenas ilustrativos vão em blocos comuns, sem path=; (3) não afirme na resposta o " +
  "resultado da execução, ele é mostrado à parte.";

const TITLE = "**Execução real do código acima**";

function oneLine(text: string | undefined, fallback: string): string {
  const clean = (text ?? "").replace(/\s+/g, " ").trim();
  return (clean || fallback).slice(0, 240);
}

/** Bloco em markdown que fecha a resposta com o resultado medido. */
export function labExecutionSection(meta: SandboxMeta): string {
  const link = meta.url ? ` [ver no GitHub](${meta.url})` : "";
  if (meta.status === "skipped") {
    return `${TITLE} — não executado: ${oneLine(meta.reason, "motivo não informado")}.`;
  }
  if (meta.status === "error") {
    return `${TITLE} — não foi possível executar: ${oneLine(meta.reason, "erro não informado")}.`;
  }
  if (meta.status === "pending") {
    return `${TITLE} — ainda em andamento quando esta resposta foi enviada, então o resultado não foi anexado.${link}`;
  }

  const outcome = sandboxOutcome(meta);
  const kind = meta.kind ?? "preset desconhecido";
  const verdict =
    outcome === "passed"
      ? `PASSOU (${kind}, código de saída 0)`
      : outcome === "inconclusive"
        ? "inconclusivo — falha de infraestrutura antes do experimento rodar"
        : meta.ended === true
          ? `FALHOU (${kind}, código de saída ${meta.exitCode ?? "desconhecido"})`
          : `FALHOU (${kind}, não terminou no tempo limite)`;
  const output = (meta.output ?? "").trim();
  const body = output
    ? `\n\n\`\`\`text\n${excerptOutput(output, SECTION_OUTPUT_CHARS).replace(/```/g, "'''")}\n\`\`\``
    : "";
  return `${TITLE} — ${verdict}.${link}${body}\n\n_Rodou no repositório público vanusta-sandbox (só exemplos sintéticos)._`;
}
