// hooks/useAuraUserId.ts
"use client";

import { useCallback, useEffect, useState } from "react";

function genUuid(): string {
  if (typeof window !== "undefined") {
    const c: any = (window as any).crypto || (window as any).msCrypto;
    if (c?.randomUUID) return c.randomUUID();
    if (c?.getRandomValues) {
      const bytes = new Uint8Array(16);
      c.getRandomValues(bytes);
      bytes[6] = (bytes[6] & 0x0f) | 0x40;
      bytes[8] = (bytes[8] & 0x3f) | 0x80;
      const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
      return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
    }
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (ch) => {
    const r = (Math.random() * 16) | 0;
    const v = ch === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function useAuraUserId() {
  const [uid, setUid] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const KEY = "aura_uid_v1";
    let stored = window.localStorage.getItem(KEY);
    if (!stored) {
      stored = genUuid();
      window.localStorage.setItem(KEY, stored);
    }
    setUid(stored);
  }, []);

  const resetUid = useCallback(() => {
    if (typeof window === "undefined") return;
    const KEY = "aura_uid_v1";
    const fresh = genUuid();
    window.localStorage.setItem(KEY, fresh);
    setUid(fresh);
  }, []);

  return { uid, resetUid };
}
