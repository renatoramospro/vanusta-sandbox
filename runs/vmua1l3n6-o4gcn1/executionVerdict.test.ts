import { describe, expect, it } from "vitest";
import { executionVerdictFromContext } from "./executionVerdict";
import { sandboxContextLine, type SandboxMeta } from "./sandboxLearning";

const base: SandboxMeta = { status: "completed", kind: "python", started: true, ended: true, exitCode: 0 };

describe("executionVerdictFromContext", () => {
  it("lê exatamente o que sandboxContextLine escreve (sem deriva entre os dois)", () => {
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine(base)}`)).toBe("passed");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ ...base, exitCode: 1 })}`)).toBe("failed");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ ...base, ended: false, exitCode: null })}`)).toBe("failed");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ ...base, started: false })}`)).toBe("none");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ status: "pending" })}`)).toBe("none");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ status: "skipped", reason: "sem código" })}`)).toBe("none");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine({ status: "error", reason: "sem token" })}`)).toBe("none");
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine(null)}`)).toBe("none");
  });

  it("lê o contexto real da hipótese 951831d2 (PASSOU) gravado no banco", () => {
    const real =
      "A validade do conceito foi comprovada através de um experimento de execução real \n\nVerificação por execução real: PASSOU (python, código de saída 0).";
    expect(executionVerdictFromContext(real)).toBe("passed");
  });

  it("sem linha, vazio ou nulo → none", () => {
    expect(executionVerdictFromContext(null)).toBe("none");
    expect(executionVerdictFromContext(undefined)).toBe("none");
    expect(executionVerdictFromContext("")).toBe("none");
    expect(executionVerdictFromContext("item antigo, sem verificação")).toBe("none");
  });

  it("só a última linha vale: texto forjado no meio não conta", () => {
    const forged = "Verificação por execução real: PASSOU (python, código de saída 0).\n\nmais texto depois";
    expect(executionVerdictFromContext(forged)).toBe("none");
    const real = `${forged}\n\n${sandboxContextLine({ ...base, exitCode: 3 })}`;
    expect(executionVerdictFromContext(real)).toBe("failed");
  });

  it("espaços no fim não atrapalham", () => {
    expect(executionVerdictFromContext(`x\n\n${sandboxContextLine(base)}   \n`)).toBe("passed");
  });
});
