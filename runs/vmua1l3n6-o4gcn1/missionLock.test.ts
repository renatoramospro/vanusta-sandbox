import { describe, expect, it } from "vitest";
import {
  MISSION_BUSY_MARKER,
  MISSION_LOCK_TTL_MS,
  MissionBusyError,
  isMissionBusyError,
  lockExpiryIso,
} from "./missionLock";

describe("missionLock", () => {
  it("o erro carrega a marca estável e é reconhecido pela mensagem", () => {
    const err = new MissionBusyError();
    expect(err).toBeInstanceOf(Error);
    expect(err.message).toContain(MISSION_BUSY_MARKER);
    expect(isMissionBusyError(err)).toBe(true);
  });

  it("reconhece depois de perder a classe (só a mensagem atravessa a server function)", () => {
    expect(isMissionBusyError(new Error(new MissionBusyError().message))).toBe(true);
    expect(isMissionBusyError(`erro: ${MISSION_BUSY_MARKER} x`)).toBe(true);
  });

  it("outros erros e valores não são 'ocupada'", () => {
    expect(isMissionBusyError(new Error("falhou"))).toBe(false);
    expect(isMissionBusyError(null)).toBe(false);
    expect(isMissionBusyError(undefined)).toBe(false);
    expect(isMissionBusyError(42)).toBe(false);
  });

  it("lockExpiryIso soma o TTL e devolve ISO", () => {
    const now = Date.UTC(2026, 8, 20, 12, 0, 0);
    expect(lockExpiryIso(now)).toBe(new Date(now + MISSION_LOCK_TTL_MS).toISOString());
    expect(lockExpiryIso(now, 1000)).toBe("2026-09-20T12:00:01.000Z");
  });

  it("o TTL cobre a etapa mais longa (espera de 90 s + modelos)", () => {
    expect(MISSION_LOCK_TTL_MS).toBeGreaterThanOrEqual(5 * 60 * 1000);
  });
});
