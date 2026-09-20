import { describe, expect, it } from "vitest";
import { findSecretLikeContent, secretGuardMessage } from "./sandboxGuard";

function file(path: string, content: string) {
  return { path, content };
}
// Os valores de teste são montados em tempo de execução para nenhum arquivo do
// repositório conter um token com formato real.
const rep = (ch: string, n: number) => ch.repeat(n);

describe("findSecretLikeContent — formatos conhecidos", () => {
  it("chave privada", () => {
    const f = findSecretLikeContent([file("a.py", "-----BEGIN " + "RSA PRIVATE KEY-----\nabc")]);
    expect(f?.reason).toBe("chave privada");
  });
  it("AWS, GitHub, sk-, Slack, Google e JWT", () => {
    expect(findSecretLikeContent([file("a.py", "k = 'AKIA" + rep("A", 16) + "'")])?.reason).toBe("chave de acesso AWS");
    expect(findSecretLikeContent([file("a.py", "t = 'ghp_" + rep("a", 36) + "'")])?.reason).toBe("token do GitHub");
    expect(findSecretLikeContent([file("a.py", "t = 'github_pat_" + rep("a", 30) + "'")])?.reason).toBe("token do GitHub");
    expect(findSecretLikeContent([file("a.py", "k = 'sk-" + rep("a", 30) + "'")])?.reason).toBe("chave de API (formato sk-)");
    expect(findSecretLikeContent([file("a.py", "k = 'sk-ant-" + rep("a", 30) + "'")])?.reason).toBe("chave de API (formato sk-)");
    expect(findSecretLikeContent([file("a.py", "t = 'xoxb-" + rep("1", 12) + "'")])?.reason).toBe("token do Slack");
    expect(findSecretLikeContent([file("a.py", "k = 'AIza" + rep("a", 35) + "'")])?.reason).toBe("chave de API do Google");
    const jwt = "eyJ" + rep("a", 12) + "." + rep("b", 12) + "." + rep("c", 12);
    expect(findSecretLikeContent([file("a.py", `t = '${jwt}'`)])?.reason).toBe("JWT");
  });
  it("arquivo .env barra; .env.example passa", () => {
    expect(findSecretLikeContent([file(".env", "A=1")])?.reason).toBe("arquivo .env");
    expect(findSecretLikeContent([file("cfg/.env.local", "A=1")])?.reason).toBe("arquivo .env");
    expect(findSecretLikeContent([file(".env.example", "A=1")])).toBeNull();
  });
  it("devolve o caminho do arquivo suspeito", () => {
    const f = findSecretLikeContent([file("ok.py", "print(1)"), file("src/x.py", "k = 'AKIA" + rep("B", 16) + "'")]);
    expect(f?.path).toBe("src/x.py");
  });
});

describe("findSecretLikeContent — atribuição e URL", () => {
  it("credencial atribuída com valor que parece real", () => {
    expect(findSecretLikeContent([file("a.py", 'API_KEY = "abcd1234efgh5678ijkl9012"')])?.reason).toBe("credencial atribuída no código");
    expect(findSecretLikeContent([file("a.js", "const db_password = 'Zx9Qw81LmN0pRt5VbC3aa7'")])?.reason).toBe("credencial atribuída no código");
  });
  it("exemplo didático não é barrado", () => {
    expect(findSecretLikeContent([file("a.py", 'password = "correct-horse-battery-staple"')])).toBeNull();
    expect(findSecretLikeContent([file("a.py", 'token = "your-token-here-1234567890abcdef"')])).toBeNull();
    expect(findSecretLikeContent([file("a.py", 'secret = "curto123"')])).toBeNull();
  });
  it("URL com usuário e senha reais barra; placeholder e URL comum passam", () => {
    expect(findSecretLikeContent([file("a.py", 'u = "postgres://admin:S3cr3tPassw0rd@db.example.com/x"')])?.reason).toBe("URL com usuário e senha");
    expect(findSecretLikeContent([file("a.py", 'u = "postgres://user:password@localhost:5432/db"')])).toBeNull();
    expect(findSecretLikeContent([file("a.py", 'u = "postgres://user:1234@localhost/db"')])).toBeNull();
    expect(findSecretLikeContent([file("a.py", 'u = "https://example.com/path?x=1"')])).toBeNull();
  });
  it("código comum e palavras parecidas não disparam", () => {
    const code = "def soma(a, b):\n    return a + b\nprint('disk-usage-monitor-configuration-value', soma(1, 2))\n";
    expect(findSecretLikeContent([file("main.py", code)])).toBeNull();
    expect(findSecretLikeContent([file("a.py", "task-1234567890123456789012345")])).toBeNull();
  });
  it("mensagem cita o arquivo, o motivo e que nada foi enviado", () => {
    const m = secretGuardMessage({ path: "a.py", reason: "JWT" });
    expect(m).toContain('"a.py"');
    expect(m).toContain("JWT");
    expect(m).toContain("nada foi enviado");
  });
});
