"use client";
import { useEffect, useRef, useState } from "react";
import { useAuraUserId } from "@/app/hooks/useAuraUserId";

type Msg = { 
  role: "user" | "agent"; 
  text: string;
  recommendedIds?: Array<string | number>; 
};

const suggestionGroups = [
  [
    "Dry + sensitive — moisturizer under ₩30k",
    "Track my order",
    "Return policy?",
    "Niacinamide vs Vitamin C?",
  ],
  [
    "Routine for damaged moisture barrier",
    "Products safe for pregnancy?",
    "Best cleanser for redness?",
    "Can I layer retinol with AHA?",
  ],
  [
    "SPF that doesn’t pill under makeup",
    "Fragrance-free products",
    "Best Vitamin C products?",
    "Gentle routine for rosacea-type flush",
  ],
];

const ROTATE_MS = 5500;

export default function Chat({ embed = false, userId, }: { embed?: boolean; userId?: string;   }) {
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const { uid } = useAuraUserId(); // <-- get the string here
  const [paused, setPaused] = useState(false);
  const [typing, setTyping] = useState(false);
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (msgs.length > 0 || paused) return;
    const id = setInterval(() => {
      setSuggestionIndex((i) => (i + 1) % suggestionGroups.length);
    }, ROTATE_MS);
    return () => clearInterval(id);
  }, [msgs.length, paused]);

  useEffect(() => {
    const el = bodyRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [msgs, typing]);

  async function send() {
    const q = input.trim();
    if (!q || !uid) return;
    setMsgs((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setTyping(true);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": uid,
        },
        body: JSON.stringify({ question: q }),
      });

      const raw = await res.text();
      let data: any = null;
      try { data = JSON.parse(raw); } catch {}

      console.log("[/api/ask] raw json:", data);
      console.log("[/api/ask] meta:", data?.meta);
      console.log("[/api/ask] recommended_ids:", data?.meta?.recommended_ids);

      const text =
        data?.answer ??
        data?.message ??
        (res.ok ? "(no answer)" : `Error ${res.status}`);

      // ✅ Extract IDs from meta
      const recommendedIds = Array.isArray(data?.meta?.recommended_ids)
        ? data.meta.recommended_ids
        : [];

      // ✅ Store IDs in the message object
      setMsgs((m) => [
        ...m,
        {
          role: "agent",
          text,
          recommendedIds,
        },
      ]);

    } catch (err) {
      setMsgs((m) => [
        ...m,
        { role: "agent", text: "Network error, please try again." }
      ]);
    } finally {
      setTyping(false);
    }
  }



  function sendQuick(text: string) {
    if (!uid) return;
    setMsgs((m) => [...m, { role: "user", text }]);
    setTyping(true);

    (async () => {
      try {
        const res = await fetch("/api/ask", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Id": uid,
          },
          body: JSON.stringify({ question: text }),
        });

        const raw = await res.text();
        let data: any = null;
        try { data = JSON.parse(raw); } catch {}

        console.log("[/api/ask] raw json:", data);
        console.log("[/api/ask] meta:", data?.meta);

        const reply =
          data?.answer ??
          data?.message ??
          (res.ok ? "(no answer)" : `Error ${res.status}`);

        const recommendedIds = Array.isArray(data?.meta?.recommended_ids)
          ? data.meta.recommended_ids
          : [];

        console.log("[/api/ask] recommended_ids:", recommendedIds);

        setMsgs((m) => [
          ...m,
          { role: "agent", text: reply, recommendedIds }
        ]);
      } catch {
        setMsgs((m) => [...m, { role: "agent", text: "Network error, please try again." }]);
      } finally {
        setTyping(false);
      }
    })();
  }


  const containerStyle: React.CSSProperties = embed
    ? { height: "100%", display: "flex", flexDirection: "column", gap: 10, padding: 12 }
    : { display: "grid", gap: 10 };

  return (
    <div style={containerStyle}>
      <div
        ref={bodyRef}
        className="chat-body"
        style={{
          flex: 1,
          minHeight: embed ? 0 : 220,
          border: "1px solid #2a2a2a",
          borderRadius: 12,
          padding: 10,
          overflowY: "auto",
          background: "#0f0f0f",
        }}
      >
        {msgs.length === 0 && (
          <div style={{ textAlign: "center", marginTop: 16, opacity: 0.55, fontSize: 13 }}>
            I’m here and ready to help ✨<br />
            Ask me anything.
          </div>
        )}

        {msgs.map((m, i) => {
          const isUser = m.role === "user";

          function openProductModal(pid: string | number) {
            window.dispatchEvent(
              new CustomEvent("open-product", { detail: { pid: String(pid) } })
            );
          }

          return (
            <div
              key={i}
              style={{
                display: "flex",
                flexDirection: "column", // ← IMPORTANT to allow buttons below text
                alignItems: isUser ? "flex-end" : "flex-start",
                margin: "8px 0",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  justifyContent: isUser ? "flex-end" : "flex-start",
                  gap: 8,
                  width: "100%",
                }}
              >
                {!isUser && (
                  <div
                    style={{
                      width: 22,
                      height: 22,
                      borderRadius: "50%",
                      background: "#E6DED5",
                      border: "1px solid #d4ccc4",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                    }}
                  >
                    👩‍⚕️
                  </div>
                )}

                <span
                  style={{
                    padding: "8px 10px",
                    borderRadius: 12,
                    background: isUser ? "#e7e9ff" : "#ffffff",
                    color: "#111",
                    border: "1px solid rgba(0,0,0,0.06)",
                    maxWidth: "70%",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    fontSize: 14,
                    lineHeight: 1.35,
                  }}
                >
                  {m.text}
                </span>

                {isUser && (
                  <div
                    style={{
                      width: 22,
                      height: 22,
                      borderRadius: "50%",
                      background: "#1f1f1f",
                      border: "1px solid #3a3a3a",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 12,
                      color: "#e5e5e5",
                    }}
                  >
                    👩🏻‍💻
                  </div>
                )}
              </div>

              {/* ✅ Product chips under agent messages */}
              {!isUser && m.recommendedIds && m.recommendedIds.length > 0 && (
                <div
                  style={{
                    marginTop: 6,
                    display: "flex",
                    marginLeft: 22 + 8,
                    gap: 3,
                    flexWrap: "wrap",
                    maxWidth: "70%",
                  }}
                >
                  {m.recommendedIds.map((pid) => (
                    <button
                      key={pid}
                      onClick={() => openProductModal(pid)}
                      style={{
                        padding: "3px 7px",
                        fontSize: 12,
                        fontWeight: 700, 
                        fontStyle: "italic",  
                        borderRadius: 10,
                        letterSpacing: 0.2,
                        border: "1px dotted #454545",
                        background: "rgba(255, 255, 255, 1)",
                        backdropFilter: "blur(4px)",
                        color: "#0d2977dc",
                        cursor: "pointer",
                        boxShadow: "0 1px 0 rgba(255,255,255,0.06) inset",
                        transition: "background 120ms ease, border-color 120ms ease",
                      }}
                      onMouseEnter={(e) => {
                        (e.currentTarget as HTMLButtonElement).style.background = "#f5f5f5a9",
                        (e.currentTarget as HTMLButtonElement).style.borderColor = "#5a5a5a";
                      }}
                      onMouseLeave={(e) => {
                        (e.currentTarget as HTMLButtonElement).style.background = "white",
                        (e.currentTarget as HTMLButtonElement).style.borderColor = "#454545";
                      }}
                    >
                      View product
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}


        {typing && (
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              justifyContent: "flex-start",
              gap: 8,
              margin: "6px 0",
            }}
          >
            <div
              style={{
                width: 22,
                height: 22,
                borderRadius: "50%",
                background: "#E6DED5",
                border: "1px solid #d4ccc4",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
              }}
            >
              👩‍⚕️
            </div>
            <span
              style={{
                padding: "8px 10px",
                borderRadius: 12,
                background: "#ffffff",
                color: "#888",
                border: "1px solid rgba(0,0,0,0.05)",
                fontSize: 13,
                fontStyle: "italic",
              }}
            >
              typing…
            </span>
          </div>
        )}
      </div>

      {/* Suggestions */}
      {msgs.length === 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ fontSize: 11, color: "#7a7874", opacity: 0.75 }}>Example questions:</div>
          <div
            key={suggestionIndex}
            className="suggestions-rotating"
            onMouseEnter={() => setPaused(true)}
            onMouseLeave={() => setPaused(false)}
            style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
          >
            {suggestionGroups[suggestionIndex].map((t) => (
              <span key={t} className="suggestion-pill" onClick={() => sendQuick(t)}>
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Single input row (no duplicate textarea) */}
      <div style={{ display: "flex", gap: 8 }}>
        <textarea
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = e.target.scrollHeight + "px";
            setPaused(true);
          }}
          onBlur={() => setPaused(false)}
          placeholder={uid ? "Ask anything…" : "Loading…"}
          rows={1}
          style={{
            flex: 1,
            resize: "none",
            overflow: "hidden",
            minHeight: 38,
            maxHeight: 120,
            padding: "9px 10px",
            borderRadius: 10,
            border: "1px solid #3a3a3a",
            background: "#101010",
            color: "#f3f3f3",
            fontSize: 16,
            lineHeight: "1.3em",
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          disabled={!uid}
        />
        <button
          onClick={send}
          disabled={!uid}
          style={{
            padding: "9px 14px",
            borderRadius: 10,
            border: "1px solid #3a3a3a",
            background: "#1d1d1d",
            color: "#fff",
            fontSize: 14,
          }}
        >
          Send
        </button>
      </div>

      <style jsx global>{`
        .chat-body::-webkit-scrollbar { width: 10px; }
        .chat-body::-webkit-scrollbar-track { background: #121212; border-radius: 10px; }
        .chat-body::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 10px; border: 2px solid #121212; }
        .chat-body { scrollbar-color: #2a2a2a #121212; scrollbar-width: thin; }
        @keyframes lux-fade {
          0%   { opacity: 0; transform: translateY(2px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .suggestions-rotating { animation: lux-fade 700ms cubic-bezier(0.22, 0.61, 0.36, 1); }
        .suggestion-pill {
          padding: 5px 10px; border-radius: 14px; border: 1px dotted #d8d3ce;
          background: rgba(255,255,255,0.13); color: #fff; font-size: 11px; opacity: 0.78;
          cursor: pointer; transition: opacity 200ms ease, background-color 200ms ease;
        }
        .suggestion-pill:hover { opacity: 1; background: rgba(255,255,255,0.25); }
        @media (max-width: 480px) {
          textarea {
            font-size: 17px !important;
            padding: 12px !important;
          }
        }

      `}</style>
    </div>
  );
}
