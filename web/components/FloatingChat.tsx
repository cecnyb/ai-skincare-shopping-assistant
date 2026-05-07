// components/FloatingChat.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import Chat from "./Chat";
import { useAuraUserId } from "@/app/hooks/useAuraUserId";

export default function FloatingChat() {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const panelRef = useRef<HTMLDivElement>(null);
  const popRef = useRef<HTMLDivElement>(null);
  const { uid, resetUid } = useAuraUserId();

// Outside click: keep the panel open. Only hide the small popover.
useEffect(() => {
  function onDocMouseDown(e: MouseEvent) {
    if (!open) return;

    const target = e.target as Node;
    const inPanel = !!panelRef.current?.contains(target);
    const inPopover = !!popRef.current?.contains(target);

    // If the confirm popover is open:
    if (confirmOpen) {
      // Clicked anywhere outside the popover? Hide just the popover.
      if (!inPopover) setConfirmOpen(false);
      // DO NOT close the panel on outside clicks.
      return;
    }

    // Default: DO NOT close the panel on outside clicks anymore.
    // If you want to close only when clicking a special overlay, do it here.
  }

  document.addEventListener("mousedown", onDocMouseDown);
  return () => document.removeEventListener("mousedown", onDocMouseDown);
}, [open, confirmOpen]);

  // ESC closes panel
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  const panelHeight = open ? (collapsed ? 56 : 520) : 0;

  return (
    <>
      {/* Launcher button (only when visually closed) */}
      {!open && (
        <button
          onClick={() => { setOpen(true); setCollapsed(false); }}
          aria-label="Open chat"
          style={{
            position: "fixed",
            right: 20,
            bottom: 20,
            width: 56,
            height: 56,
            borderRadius: 999,
            border: "1px solid #444444ff",
            background: "#ffffff",
            color: "#111",
            boxShadow: "0 8px 30px rgba(0,0,0,0.12)",
            zIndex: 1000,
            cursor: "pointer",
          }}
        >
          💬
        </button>
      )}

      {/* Always-mounted panel. We just animate height/opacity/pointer-events */}
      <div
        ref={panelRef}
        role="dialog"
        aria-label="Chat panel"
        style={{
          position: "fixed",
          right: 20,
          bottom: 20,
          width: 360,
          maxWidth: "90vw",
          height: panelHeight,                 // collapse when closed OR minimized
          maxHeight: "75vh",
          background: "#111",
          color: "#fff",
          border: "1px solid #333",
          borderRadius: 16,
          boxShadow: "0 18px 60px rgba(0,0,0,0.35)",
          zIndex: 1000,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          transition: "height 180ms ease, opacity 150ms ease",
          opacity: open ? 1 : 0,
          pointerEvents: open ? "auto" : "none",
        }}
      >
        {/* Header */}
        <header
          style={{
            padding: "10px 12px",
            borderBottom: collapsed ? "none" : "1px solid #2a2a2a",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontWeight: 600,
            letterSpacing: 0.2,
            position: "relative", // anchor for the popover
            height: 56,
          }}
        >
          <strong>Consolutation with AURA</strong>

          <div style={{ display: "flex", gap: 6 }}>
            {/* Minimize / Expand */}
            <button
              onClick={() => {
                setCollapsed((v) => !v);
                setConfirmOpen(false);
              }}
              aria-label={collapsed ? "Expand chat" : "Minimize chat"}
              title={collapsed ? "Expand" : "Minimize"}
              style={{
                border: "1px solid #444",
                background: "#1e1e1e",
                color: "#fff",
                borderRadius: 8,
                padding: "4px 8px",
                cursor: "pointer",
              }}
            >
              {collapsed ? "▴" : "▾"}
            </button>

            {/* Close button → toggles popover */}
            <button
              onMouseDown={(e) => e.stopPropagation()} // prevent outside-close
              onClick={() => setConfirmOpen((v) => !v)}
              aria-label="Close chat"
              title="Close (and optionally clear chat)"
              style={{
                border: "1px solid #444",
                background: "#1e1e1e",
                color: "#fff",
                borderRadius: 8,
                padding: "4px 8px",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          </div>

          {/* Popover anchored to header */}
          {confirmOpen && (
            <div
              ref={popRef}
              onMouseDown={(e) => e.stopPropagation()} // make clicks not count as outside
              style={{
                position: "absolute",
                top: "42px",
                right: "12px",
                background: "#1a1a1a",
                border: "1px solid #333",
                borderRadius: 8,
                padding: 8,
                display: "flex",
                flexDirection: "column",
                gap: 6,
                zIndex: 2000,
                boxShadow: "0 8px 30px rgba(0,0,0,0.45)",
                fontSize: 13,
                minWidth: 180,
              }}
            >
              <button
                onClick={() => {
                  resetUid();     // new session id
                  setOpen(false); // close panel
                  setConfirmOpen(false);
                }}
                style={{
                  background: "#d93737",
                  color: "#fff",
                  border: "none",
                  padding: "6px 10px",
                  borderRadius: 6,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                Clear chat & close
              </button>
              <button
                onClick={() => setConfirmOpen(false)} // just hide options
                style={{
                  background: "transparent",
                  color: "#bbb",
                  border: "1px dashed #333",
                  padding: "6px 10px",
                  borderRadius: 6,
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                Cancel
              </button>
            </div>
          )}
        </header>

        {/* Body stays mounted; we just visually collapse it when minimized */}
        <div
          style={{
            flex: 1,
            minHeight: 0,
            height: collapsed ? 0 : "auto",
            overflow: "hidden",
            opacity: collapsed ? 0 : 1,
            pointerEvents: collapsed ? "none" : "auto",
            transition: "height 180ms ease, opacity 150ms ease",
          }}
        >
          <Chat embed userId={uid ?? undefined} key={uid ?? "pending"} />
        </div>
      </div>
    </>
  );
}
