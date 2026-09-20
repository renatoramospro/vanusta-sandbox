import { describe, expect, it } from "vitest";
import {
  LAB_EXEC_WAIT_CAP_MS,
  SANDBOX_ANSWER_HINT,
  labExecutionSection,
  labExecutionWaitMs,
} from "./labExecution";
import type { SandboxMeta } from "./sandboxLearning";

const passed: SandboxMeta = {
  status: "completed",
  kind: "python",
  started: true,
  ended: true,
  exitCode: 0,
  output: "ok 42",
  url: "https://github.com/x/y/actions/runs/1",
};

describe("labExecutionWaitMs", () => {
  it("usa o teto quando sobra folga e encolhe conforme o tempo já gasto", () => {
    expect(labExecutionWaitMs(0)).toBe(LAB_EXEC_WAIT_CAP_MS);
    expect(labExecutionWaitMs(-5)).toBe(LAB_EXEC_WAIT_CAP_MS);
    expect(labExecutionWaitMs(30_000)).toBe(60_000);
    expect(labExecutionWaitMs(89_000)).toBe(1_000);
  });
  it("zera quando o orçamento da requisição acabou", () => {
    expect(labExecutionWaitMs(90_000)).toBe(0);
    expect(labExecutionWaitMs(200_000)).toBe(0);
  });
});

describe("labExecutionSection", () => {
  it("passou: veredito, link e saída real", () => {
    const s = labExecutionSection(passed);
    expect(s).toContain("PASSOU (python, código de saída 0)");
    expect(s).toContain("[ver no GitHub](https://github.com/x/y/actions/runs/1)");
    expect(s).toContain("ok 42");
    expect(s).toContain("repositório público");
  });
  it("falhou com código de saída, e não terminou", () => {
    expect(labExecutionSection({ ...passed, exitCode: 1, output: "Traceback" })).toContain("FALHOU (python, código de saída 1)");
    expect(labExecutionSection({ ...passed, ended: false, exitCode: null })).toContain("não terminou no tempo limite");
  });
  it("infraestrutura, pendente, pulado e erro dizem o que houve", () => {
    expect(labExecutionSection({ status: "completed", started: false, ended: false })).toContain("inconclusivo");
    expect(labExecutionSection({ status: "pending", url: "https://x.test/r" })).toContain("ainda em andamento");
    expect(labExecutionSection({ status: "pending", url: "https://x.test/r" })).toContain("[ver no GitHub](https://x.test/r)");
    expect(labExecutionSection({ status: "skipped", reason: "vários .py" })).toContain("não executado: vários .py");
    expect(labExecutionSection({ status: "error", reason: "possível segredo\nem a.py" })).toContain("não foi possível executar: possível segredo em a.py");
  });
  it("saída com três crases não quebra o bloco; saída enorme é cortada", () => {
    const s = labExecutionSection({ ...passed, output: "a ``` b" });
    expect(s).not.toContain("a ``` b");
    expect(s).toContain("a ''' b");
    const long = labExecutionSection({ ...passed, output: "x".repeat(10_000) });
    expect(long).toContain("omitidos");
    expect(long.length).toBeLessThan(2_400);
  });
});

describe("SANDBOX_ANSWER_HINT", () => {
  it("pede path=, avisa que é público e que só vale exemplo sintético", () => {
    expect(SANDBOX_ANSWER_HINT).toContain("path=");
    expect(SANDBOX_ANSWER_HINT).toContain("PÚBLICO");
    expect(SANDBOX_ANSWER_HINT).toContain("sintético");
    expect(SANDBOX_ANSWER_HINT).toContain("código de saída 0");
  });
});
