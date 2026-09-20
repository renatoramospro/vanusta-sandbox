/**
 * Trava por missão do Learning Lab — parte PURA. Duas chamadas simultâneas
 * (Scheduler/cron + UI + MCP) escolhiam a mesma etapa e duplicavam relatório
 * (e, com o sandbox, cada Programador duplicado disparava uma execução extra
 * no repositório público). A I/O está em missionLock.server.ts.
 */
export const MISSION_LOCK_TTL_MS = 10 * 60 * 1000;

/** Marca estável na mensagem — o erro perde a classe ao cruzar a server function. */
export const MISSION_BUSY_MARKER = "[missao-ocupada]";

export class MissionBusyError extends Error {
  constructor() {
    super(
      `${MISSION_BUSY_MARKER} Outra chamada está avançando esta missão agora — espere alguns segundos e tente de novo (nada foi duplicado).`,
    );
    this.name = "MissionBusyError";
  }
}

export function isMissionBusyError(err: unknown): boolean {
  const message = err instanceof Error ? err.message : typeof err === "string" ? err : "";
  return message.includes(MISSION_BUSY_MARKER);
}

/** Instante (ISO) em que a trava tomada em `now` expira — também serve de token da posse. */
export function lockExpiryIso(now: number, ttlMs: number = MISSION_LOCK_TTL_MS): string {
  return new Date(now + ttlMs).toISOString();
}
