import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "@/services/api";
import type { ChatMessageOut, QuickReply } from "@/types";

interface Bubble {
  id: number;
  role: "user" | "bot";
  text: string;
  time: string;
  recommendationId?: string | null;
  joined?: boolean;
}

function nowTime() {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

const DEFAULT_QUICK_REPLIES: QuickReply[] = [
  { label: "हिंदी", value: "हिंदी" },
  { label: "English", value: "English" },
];

function quickReplyIcon(label: string): string {
  const l = label.toLowerCase();
  if (/price|rupee|₹|rate|कीमत|मंडी/.test(l)) return "currency_rupee";
  if (/truck|load|route|transport|ट्रक|लोड/.test(l)) return "local_shipping";
  if (/join|जुड़/.test(l)) return "check_circle";
  if (/option|विकल्प/.test(l)) return "list";
  return "search";
}

export default function ChatPage() {
  const [sessionId] = useState(
    () => `web-${Math.random().toString(36).slice(2, 10)}${Date.now() % 100000}`,
  );
  const [messages, setMessages] = useState<Bubble[]>([
    {
      id: 0,
      role: "bot",
      text:
        "Namaste! 🙏 I'm *Unnati* — your farming copilot.\n\n" +
        "आप किस भाषा में बात करना चाहेंगे?\n" +
        "Which language would you like to chat in?",
      time: nowTime(),
      recommendationId: null,
      joined: false,
    },
  ]);
  const [quickReplies, setQuickReplies] = useState<QuickReply[]>(DEFAULT_QUICK_REPLIES);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [lang, setLang] = useState<"hi" | "en">("en");
  const [listening, setListening] = useState(false);
  const [micSupported] = useState(
    () =>
      typeof window !== "undefined" &&
      Boolean(
        (window as any).SpeechRecognition ||
          (window as any).webkitSpeechRecognition,
      ),
  );
  const nextId = useRef(1);
  const chatRef = useRef<HTMLDivElement>(null);
  const recRef = useRef<{ stop: () => void } | null>(null);

  function scrollToBottom() {
    requestAnimationFrame(() => {
      if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
    });
  }

  useEffect(scrollToBottom, [messages, typing]);

  useEffect(() => {
    return () => {
      recRef.current?.stop();
    };
  }, []);

  function toggleMic() {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    if (!SR || typing) return;
    const rec = new SR();
    rec.lang = lang === "hi" ? "hi-IN" : "en-IN";
    rec.interimResults = true;
    rec.continuous = false;
    const base = input.trim() ? input.trim() + " " : "";
    rec.onresult = (e: any) => {
      let transcript = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
      }
      setInput(base + transcript);
    };
    rec.onend = () => {
      recRef.current = null;
      setListening(false);
    };
    rec.onerror = () => {
      recRef.current = null;
      setListening(false);
    };
    recRef.current = rec;
    try {
      rec.start();
      setListening(true);
    } catch {
      setListening(false);
    }
  }

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed || typing) return;
    setMessages((m) => [
      ...m,
      { id: nextId.current++, role: "user", text: trimmed, time: nowTime() },
    ]);
    setInput("");
    setTyping(true);
    try {
      const turn = await api.chat(sessionId, trimmed);
      const reply: ChatMessageOut = turn.reply;
      // Track conversation language from the bot's script for the toggle state.
      if (/[\u0900-\u097F]/.test(reply.text) && lang === "en") setLang("hi");
      setMessages((m) => [
        ...m,
        {
          id: nextId.current++,
          role: "bot",
          text: reply.text,
          time: nowTime(),
          recommendationId: reply.recommendation_id,
          joined: reply.joined,
        },
      ]);
      if (reply.quick_replies.length > 0) {
        setQuickReplies(reply.quick_replies);
      }
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: nextId.current++,
          role: "bot",
          text:
            lang === "hi"
              ? "क्षमा करें, नेटवर्क नहीं मिल पाया। कृपया थोड़ी देर में फिर कोशिश करें।"
              : "Sorry, I couldn't reach the network just now. Please try again in a moment.",
          time: nowTime(),
          recommendationId: null,
          joined: false,
        },
      ]);
    } finally {
      setTyping(false);
    }
  }

  return (
    <div className="w-full h-[calc(100dvh-5rem)] min-h-[560px] px-container-padding py-6 flex justify-center overflow-hidden">
      {/* Assistant Panel */}
      <div className="card relative w-full max-w-3xl h-full flex flex-col overflow-hidden">
        {/* Header */}
        <div className="shrink-0 h-16 w-full flex items-center gap-3 px-5 border-b border-white/[0.07] bg-white/[0.03]">
          <div className="relative shrink-0">
            <img
              src="/unnati_logo.png"
              alt="Unnati Assistant"
              className="w-10 h-10 rounded-full object-cover ring-1 ring-primary/30"
            />
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-primary rounded-full ring-2 ring-night"></div>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold text-on-surface leading-tight truncate">
              Unnati Assistant
            </span>
            <span className="text-xs text-primary/80 leading-tight flex items-center gap-1.5">
              <span
                className={`inline-block w-1.5 h-1.5 rounded-full ${
                  typing ? "bg-amber-300 animate-pulse" : "bg-primary"
                }`}
              ></span>
              {typing ? "Typing…" : "Online · AI farming copilot"}
            </span>
          </div>
          <div className="ml-auto flex items-center rounded-full p-0.5 bg-white/[0.05] border border-white/[0.07]">
            {(["hi", "en"] as const).map((code) => (
              <button
                key={code}
                onClick={() => {
                  if (lang !== code && !typing) {
                    setLang(code);
                    send(code === "hi" ? "हिंदी" : "English");
                  }
                }}
                disabled={typing}
                className={`px-3 py-1 rounded-full text-xs font-bold transition-colors ${
                  lang === code
                    ? "bg-primary/20 text-primary"
                    : "text-on-surface-variant hover:text-primary"
                }`}
              >
                {code === "hi" ? "हिंदी" : "EN"}
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-5 py-6 flex flex-col gap-4 scroll-smooth"
          ref={chatRef}
        >
          {messages.map((msg) =>
            msg.role === "bot" ? (
              <div key={msg.id} className="flex gap-3 max-w-[85%] self-start animate-fade-up">
                <img
                  src="/unnati_logo.png"
                  alt=""
                  className="w-7 h-7 rounded-full object-cover ring-1 ring-primary/25 shrink-0 self-end mb-0.5"
                />
                <div className="min-w-0">
                  <div className="rounded-2xl rounded-bl-md bg-white/[0.06] border border-white/[0.08] px-4 py-3 text-sm text-on-surface leading-relaxed flex flex-col gap-2.5">
                    <p className="whitespace-pre-line">{msg.text}</p>
                    {(msg.recommendationId || msg.joined) && (
                      <div className="flex flex-wrap gap-2">
                        {msg.recommendationId && (
                          <Link
                            to={`/recommendation/${msg.recommendationId}`}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/30 text-xs font-semibold text-primary hover:bg-primary/20 transition-colors"
                          >
                            <span className="material-symbols-outlined text-[14px]">
                              insights
                            </span>
                            {lang === "hi"
                              ? "पूरी सिफ़ारिश देखें"
                              : "View full recommendation"}
                          </Link>
                        )}
                        {msg.joined && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/30 text-xs font-semibold text-primary">
                            <span className="material-symbols-outlined text-[14px]">
                              task_alt
                            </span>
                            {lang === "hi" ? "पूल में जुड़ गए" : "Pool joined"}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="mt-1 ml-1 text-[10px] font-mono uppercase tracking-wider text-clay/60">
                    Unnati · {msg.time}
                  </div>
                </div>
              </div>
            ) : (
              <div key={msg.id} className="max-w-[75%] self-end animate-fade-up">
                <div className="rounded-2xl rounded-br-md bg-mint-gradient px-4 py-3 text-sm font-medium text-emerald-950 leading-relaxed shadow-glow">
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>
                <div className="mt-1 mr-1 text-right text-[10px] font-mono uppercase tracking-wider text-clay/60">
                  You · {msg.time}
                </div>
              </div>
            ),
          )}

          {/* Typing Indicator */}
          {typing && (
            <div className="flex gap-3 self-start animate-fade-up">
              <img
                src="/unnati_logo.png"
                alt=""
                className="w-7 h-7 rounded-full object-cover ring-1 ring-primary/25 shrink-0 self-end mb-0.5"
              />
              <div className="rounded-2xl rounded-bl-md bg-white/[0.06] border border-white/[0.08] px-4 py-3.5 flex items-center gap-1.5">
                <span className="dot-pulse"></span>
                <span className="dot-pulse dot-delay-1"></span>
                <span className="dot-pulse dot-delay-2"></span>
              </div>
            </div>
          )}

          <div className="h-2"></div>
        </div>

        {/* Composer */}
        <div className="shrink-0 border-t border-white/[0.07] bg-white/[0.02] px-5 pt-3 pb-4">
          {quickReplies.length > 0 && (
            <div className="flex gap-2 overflow-x-auto pb-3 -mx-1 px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
              {quickReplies.map((qr) => (
                <button
                  key={qr.label + qr.value}
                  onClick={() => send(qr.value)}
                  disabled={typing}
                  className="shrink-0 inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/[0.05] border border-emerald-400/20 text-xs font-semibold text-emerald-200 hover:border-emerald-400/50 hover:bg-emerald-400/[0.12] transition-all disabled:opacity-50 disabled:pointer-events-none"
                >
                  <span className="material-symbols-outlined text-[14px] text-primary">
                    {quickReplyIcon(qr.label)}
                  </span>
                  {qr.label}
                </button>
              ))}
            </div>
          )}
          <form
            className="flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <div className="field-input flex-1 !py-2.5 flex items-center gap-2">
              <input
                className="bg-transparent border-none outline-none w-full text-sm text-ink placeholder:text-clay/50"
                placeholder={
                  listening
                    ? lang === "hi"
                      ? "सुन रहे हैं…"
                      : "Listening…"
                    : lang === "hi"
                      ? "अपना सवाल पूछें…"
                      : "Ask about prices, transport, pooling…"
                }
                type="text"
                value={input}
                autoFocus
                onChange={(e) => setInput(e.target.value)}
              />
              {micSupported && (
                <button
                  type="button"
                  onClick={toggleMic}
                  disabled={typing}
                  aria-label={listening ? "Stop listening" : "Speak a message"}
                  className={`shrink-0 cursor-pointer transition-colors ${
                    listening
                      ? "text-red-500 animate-pulse"
                      : "text-clay hover:text-emerald-300"
                  }`}
                >
                  <span className="material-symbols-outlined text-[22px]">
                    {listening ? "mic_filled" : "mic"}
                  </span>
                </button>
              )}
            </div>
            <button
              type="submit"
              className="btn-primary !px-4 !py-2.5 shrink-0"
              disabled={typing || input.trim() === ""}
              aria-label="Send message"
            >
              <span className="material-symbols-outlined text-[18px]">send</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
