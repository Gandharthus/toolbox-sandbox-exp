import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import "./styles.css";
/** ---------- LLM CONFIG (placeholders) ---------- */
// Point this at your OpenAI-compatible endpoint (must expose /v1/chat/completions)
const LLM_BASE_URL = "local"; 
const LLM_API_KEY = "";
const LLM_MODEL = ""; //


// Optional: cap how many past turns you send to the model
const MAX_TURNS = 24; // user+assistant messages counted individually

/** ---------- Utilities ---------- */
const LS_KEY = "quiet-observer:sessions";

/** Simple message shape */
function makeMsg(role, content) {
  return {
    id: crypto.randomUUID(),
    role, // "user" | "bot"
    content,
    timestamp: new Date().toISOString(),
  };
}

/** One session (conversation) */
function makeSession(title = "Nouvelle discussion") {
  return {
    id: crypto.randomUUID(),
    title,
    messages: [
      makeMsg("bot", "Bonjour ! Je suis le Quiet Observer. Démarrons ?"),
    ],
    updatedAt: Date.now(),
  };
}

/** ---------- OpenAI-compatible Chat Call ---------- */
async function chatWithLLM({ history, abortSignal }) {
  // history = [{role: "user" | "bot", content: string}, ...]
  // Convert app roles to OpenAI roles
  const mapped = history.map((m) => ({
    role: m.role === "bot" ? "assistant" : "user",
    content: m.content,
  }));

  const system = {
    role: "system",
    content:
      "You are Quiet Observer, a concise, friendly assistant. Keep answers short and helpful.",
  };

  const trimmed = mapped.slice(-MAX_TURNS);

  const payload = {
    model: LLM_MODEL,
    messages: [system, ...trimmed],
    temperature: 0.6,
    // max_tokens: 512,
    // top_p: 1,
    // stream: false,
  };

  const res = await fetch(`${LLM_BASE_URL}/v1/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${LLM_API_KEY}`,
    },
    body: JSON.stringify(payload),
    signal: abortSignal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`LLM error ${res.status}: ${text || res.statusText}`);
  }

  const data = await res.json();
  const content =
    data?.choices?.[0]?.message?.content ??
    data?.choices?.[0]?.delta?.content ??
    "";
  return (content || "").trim();
}

/** ---------- App ---------- */
export default function App() {
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed?.length ? parsed : [makeSession("Premiers pas")];
      } catch {
        return [makeSession("Premiers pas")];
      }
    }
    return [makeSession("Premiers pas")];
  });

  const [currentId, setCurrentId] = useState(() => sessions[0].id);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true); // retractable

  // Conversation scroll helpers
  const listRef = useRef(null);
  const [atBottom, setAtBottom] = useState(true);
  const scrollToBottom = useCallback((smooth = true) => {
    if (!listRef.current) return;
    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: smooth ? "smooth" : "auto",
    });
  }, []);
  const handleScroll = useCallback(() => {
    if (!listRef.current) return;
    const el = listRef.current;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    setAtBottom(distance < 40); // “near bottom” threshold
  }, []);

  // Keep a ref to abort in-flight LLM requests if user sends another message
  const abortRef = useRef(null);

  const current = useMemo(
    () => sessions.find((s) => s.id === currentId) ?? sessions[0],
    [sessions, currentId]
  );

  // Persist sessions
  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify(sessions));
  }, [sessions]);

  // Auto-scroll on new messages only if user is near the bottom
  useEffect(() => {
    if (atBottom) {
      scrollToBottom(true);
    }
  }, [current?.messages.length, atBottom, scrollToBottom]);

  const patchSession = (id, updater) => {
    setSessions((arr) =>
      arr.map((s) => (s.id === id ? updater({ ...s }) : s))
    );
  };

  const onSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    // Cancel any previous request in flight
    if (abortRef.current) {
      try {
        abortRef.current.abort();
      } catch {}
    }
    abortRef.current = new AbortController();

    // Push user message
    patchSession(current.id, (s) => {
      s.messages = [...s.messages, makeMsg("user", trimmed)];
      s.updatedAt = Date.now();
      return s;
    });
    setInput("");
    setIsSending(true);

    try {
      // Build the history (include the new user message we just added)
      const historyForLLM = [...current.messages, makeMsg("user", trimmed)];

      const reply = await chatWithLLM({
        history: historyForLLM,
        abortSignal: abortRef.current.signal,
      });

      patchSession(current.id, (s) => {
        s.messages = [...s.messages, makeMsg("bot", reply || "…")];
        s.updatedAt = Date.now();
        return s;
      });
    } catch (err) {
      console.error(err);
      patchSession(current.id, (s) => {
        s.messages = [
          ...s.messages,
          makeMsg(
            "bot",
            "⚠️ Je n’ai pas pu contacter le modèle. Vérifie l’endpoint, le token, la CORS policy et les logs serveur."
          ),
        ];
        s.updatedAt = Date.now();
        return s;
      });
    } finally {
      setIsSending(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  // ---- Historique actions
  const newChat = () => {
    const session = makeSession("Nouvelle discussion");
    setSessions((arr) => [session, ...arr]);
    setCurrentId(session.id);
    // When opening a new chat, ensure we're at bottom (empty thread)
    setTimeout(() => scrollToBottom(false), 0);
  };

  const selectChat = (id) => {
    setCurrentId(id);
    // auto-close on small screens for focus
    if (window.matchMedia("(max-width: 920px)").matches) {
      setSidebarOpen(false);
    }
    // Reset scroll-bottom tracking on chat switch
    setTimeout(() => {
      setAtBottom(true);
      scrollToBottom(false);
    }, 0);
  };

  const renameChat = (id, title) => {
    patchSession(id, (s) => {
      s.title = title?.trim() || "Sans titre";
      s.updatedAt = Date.now();
      return s;
    });
  };

  const deleteChat = (id) => {
    setSessions((arr) => {
      const filtered = arr.filter((s) => s.id !== id);
      const final = filtered.length
        ? filtered
        : [makeSession("Nouvelle discussion")];
      if (!final.find((s) => s.id === currentId)) {
        setCurrentId(final[0].id);
      }
      return final;
    });
  };

  return (
    <div
      className={`qo-shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}
    >
      {/* Sidebar / Historique */}
      <aside
        className={`qo-sidebar ${sidebarOpen ? "open" : ""}`}
        aria-label="Historique des discussions"
      >
        <div className="qo-sidebar__header">
          <span className="qo-sidebar__title">Historique</span>
          <button
            className="qo-button subtle"
            onClick={newChat}
            aria-label="Nouvelle discussion"
            title="Nouvelle discussion"
          >
            + Nouveau
          </button>
        </div>

        <nav
          className="qo-sidebar__list"
          role="listbox"
          aria-activedescendant={currentId}
        >
          {sessions
            .slice() // don’t mutate
            .sort((a, b) => b.updatedAt - a.updatedAt)
            .map((s) => (
              <HistoryItem
                key={s.id}
                session={s}
                active={s.id === currentId}
                onSelect={() => selectChat(s.id)}
                onRename={(title) => renameChat(s.id, title)}
                onDelete={() => deleteChat(s.id)}
              />
            ))}
        </nav>
        <div className="qo-sidebar__footer">
          <small className="muted">LaaS • Kibana • Elastic</small>
        </div>
      </aside>

      {/* Main column */}
      <div className="qo-main">
        {/* Header */}
        <header className="qo-header" role="banner">
          <button
            className="qo-iconbtn"
            aria-label={sidebarOpen ? "Réduire l’historique" : "Ouvrir l’historique"}
            title={sidebarOpen ? "Réduire l’historique" : "Ouvrir l’historique"}
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <ChevronIcon open={sidebarOpen} />
          </button>
          <div className="qo-header__title">Talk with your logs</div>
          <div className="qo-header__subtitle">
            historique • élégant • rétractable
          </div>
        </header>

        {/* Chat area (scrollable) */}
        <main
          className="qo-chat"
          ref={listRef}
          onScroll={handleScroll}
          aria-live="polite"
          aria-label="Chat messages"
          role="log"
        >
          {/* Optional "load older" placeholder shown when scrolled up (wire pagination later) */}
          {!atBottom && (
            <button
              className="qo-loadmore"
              onClick={() => {
                // TODO: fetch older messages & prepend
              }}
            >
              ↑ Charger plus d’anciens messages
            </button>
          )}

          {current?.messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          {isSending && <TypingIndicator />}

          {/* Jump-to-latest button appears when not at bottom */}
          {!atBottom && (
            <button
              className="qo-jump"
              onClick={() => scrollToBottom(true)}
              aria-label="Revenir en bas"
            >
              Revenir au dernier
            </button>
          )}
        </main>

        {/* Composer */}
        <footer className="qo-footer" role="contentinfo">
          <div className="qo-composer" role="form" aria-label="Message composer">
            <textarea
              className="qo-input"
              placeholder="Écrire un message…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              aria-label="Message input"
            />
            <button
              className="qo-send"
              onClick={onSend}
              disabled={!input.trim() || isSending}
              aria-label="Send message"
              title="Send (Enter)"
            >
              <PaperPlaneIcon />
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

/** ---------- Components ---------- */

function HistoryItem({ session, active, onSelect, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [val, setVal] = useState(session.title);

  useEffect(() => setVal(session.title), [session.title]);

  const commit = () => {
    setEditing(false);
    onRename(val);
  };

  const date = new Date(session.updatedAt);
  const stamp = date.toLocaleString([], {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "short",
  });

  return (
    <div
      className={`qo-history__item ${active ? "active" : ""}`}
      role="option"
      aria-selected={active}
      id={session.id}
      onClick={() => !editing && onSelect()}
    >
      <div className="qo-history__row">
        {editing ? (
          <input
            className="qo-history__edit"
            value={val}
            onChange={(e) => setVal(e.target.value)}
            autoFocus
            onBlur={commit}
            onKeyDown={(e) => {
              if (e.key === "Enter") commit();
              if (e.key === "Escape") {
                setEditing(false);
                setVal(session.title);
              }
            }}
          />
        ) : (
          <span className="qo-history__title" title={session.title}>
            {session.title}
          </span>
        )}

        <div
          className="qo-history__actions"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="qo-iconbtn subtle"
            aria-label="Renommer"
            title="Renommer"
            onClick={() => setEditing((v) => !v)}
          >
            <RenameIcon />
          </button>
          <button
            className="qo-iconbtn subtle"
            aria-label="Supprimer"
            title="Supprimer"
            onClick={onDelete}
          >
            <TrashIcon />
          </button>
        </div>
      </div>

      <div className="qo-history__meta">{stamp}</div>
    </div>
  );
}

/** Left/right-aligned message bubble with timestamp */
function MessageBubble({ msg }) {
  const isUser = msg.role === "user";
  const timeLabel = useMemo(() => {
    const d = new Date(msg.timestamp);
    const hh = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const dd = d.toLocaleDateString([], { month: "short", day: "numeric" });
    return `${dd} • ${hh}`;
  }, [msg.timestamp]);

  return (
    <div className={`qo-bubble ${isUser ? "is-user" : "is-bot"}`}>
      <div className="qo-bubble__content">{msg.content}</div>
      <div className="qo-bubble__meta" aria-hidden="true">
        {timeLabel}
      </div>
    </div>
  );
}

/** Subtle “typing…” indicator */
function TypingIndicator() {
  return (
    <div className="qo-typing">
      <span className="dot" />
      <span className="dot" />
      <span className="dot" />
    </div>
  );
}

/** Icons */
function PaperPlaneIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path
        d="M21.44 2.56a1 1 0 0 0-1.02-.24l-16 5.5a1 1 0 0 0 .06 1.92l6.93 2.07 2.07 6.93a1 1 0 0 0 1.92.06l5.5-16a1 1 0 0 0-.46-1.24Zm-5.58 16.6-1.49-5 3.9-3.9-5 1.49-8.05-2.4 12.64-4.34-4.34 12.64Z"
        fill="currentColor"
      />
    </svg>
  );
}

function ChevronIcon({ open }) {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path
        d={open ? "M8 5l8 7-8 7" : "M9 19l-7-7 7-7"}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path
        d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M6 6l1 14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function RenameIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path
        d="M4 20h4L20 8l-4-4L4 16v4Zm11-13 2 2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
