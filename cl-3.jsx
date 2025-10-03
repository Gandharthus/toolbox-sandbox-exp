import React, { useEffect, useMemo, useRef, useState } from "react";
import "./styles.css";

/** ---------- Utilities ---------- */
const LS_KEY = "quiet-observer:sessions";

/** Simple message shape */
function makeMsg(role, content) {
  return {
    id: crypto.randomUUID(),
    role,
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
  const listRef = useRef(null);

  const current = useMemo(
    () => sessions.find((s) => s.id === currentId) ?? sessions[0],
    [sessions, currentId]
  );

  // Persist sessions
  useEffect(() => {
    localStorage.setItem(LS_KEY, JSON.stringify(sessions));
  }, [sessions]);

  // Auto-scroll on new messages
  useEffect(() => {
    if (!listRef.current) return;
    listRef.current.scrollTo({
      top: listRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [current?.messages.length]);

  // ---- Chat actions
  const fakeBotReply = (userText) => {
    const replies = [
      "Bien reçu. Tu veux que je peaufine ?",
      "On garde ça clair et posé.",
      "OK. Simplicité, constance, élégance.",
      "C’est noté. J’avance avec douceur.",
    ];
    const pick = replies[Math.floor(Math.random() * replies.length)];
    return pick;
  };

  const patchSession = (id, updater) => {
    setSessions((arr) =>
      arr.map((s) => (s.id === id ? updater({ ...s }) : s))
    );
  };

  const onSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    // push user message
    patchSession(current.id, (s) => {
      s.messages = [...s.messages, makeMsg("user", trimmed)];
      s.updatedAt = Date.now();
      return s;
    });
    setInput("");
    setIsSending(true);

    // Simulate latency + bot reply
    await new Promise((r) => setTimeout(r, 450));
    patchSession(current.id, (s) => {
      s.messages = [...s.messages, makeMsg("bot", fakeBotReply(trimmed))];
      s.updatedAt = Date.now();
      return s;
    });
    setIsSending(false);
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
  };

  const selectChat = (id) => {
    setCurrentId(id);
    // auto-close on small screens for focus
    if (window.matchMedia("(max-width: 920px)").matches) {
      setSidebarOpen(false);
    }
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
      // ensure at least one session exists
      const final = filtered.length ? filtered : [makeSession("Nouvelle discussion")];
      // keep selection sane
      if (!final.find((s) => s.id === currentId)) {
        setCurrentId(final[0].id);
      }
      return final;
    });
  };

  return (
    <div className={`qo-shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
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

        <nav className="qo-sidebar__list" role="listbox" aria-activedescendant={currentId}>
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
          <div className="qo-header__subtitle">historique • élégant • rétractable</div>
        </header>

        {/* Chat area */}
        <main
          className="qo-chat"
          ref={listRef}
          aria-live="polite"
          aria-label="Chat messages"
          role="log"
        >
          {current?.messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          {isSending && <TypingIndicator />}
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

        <div className="qo-history__actions" onClick={(e) => e.stopPropagation()}>
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
