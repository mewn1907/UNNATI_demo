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
    <div className="relative w-full py-12 px-container-padding flex justify-center overflow-hidden">
      {/* Background Decor */}
      <div className="absolute inset-0 w-full h-full pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px]"></div>
      </div>

      {/* Phone Frame Container */}
      <div
        className="relative w-full max-w-[400px] h-[800px] max-h-[870px] bg-surface-container rounded-[40px] shadow-2xl shadow-primary/10 overflow-hidden flex flex-col mx-auto"
        style={{
          boxShadow:
            "inset 0 0 0 1px rgba(110, 231, 183, 0.15), 0 25px 50px -12px rgba(16, 24, 20, 0.8)",
        }}
      >
        {/* Status Bar Mockup */}
        <div className="h-12 w-full flex items-center justify-between px-6 pt-2 z-20">
          <span className="font-label-mono text-label-mono text-on-surface">12:34</span>
          <div className="flex items-center gap-2 text-on-surface">
            <span className="material-symbols-outlined text-[16px]">
              signal_cellular_4_bar
            </span>
            <span className="material-symbols-outlined text-[16px]">wifi</span>
            <span className="material-symbols-outlined text-[16px]">battery_full</span>
          </div>
        </div>

        {/* Chat Header */}
        <div
          className="h-16 w-full flex items-center px-4 bg-surface-container-high/80 backdrop-blur-md z-20"
          style={{ boxShadow: "inset 0 -1px 0 0 rgba(110, 231, 183, 0.1)" }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center relative">
              <img
                src="/unnati_logo.png"
                alt="Unnati Assistant"
                className="w-10 h-10 rounded-full object-cover"
              />
              <div className="absolute bottom-0 right-0 w-3 h-3 bg-primary rounded-full ring-2 ring-surface-container-high"></div>
            </div>
            <div className="flex flex-col">
              <span className="font-data-lg text-body-md text-on-surface leading-tight">
                Unnati Assistant
              </span>
              <span className="font-body-md text-[12px] text-primary/80 leading-tight">
                {typing ? "Typing…" : "Online"}
              </span>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-3 text-on-surface-variant">
            {/* Language toggle */}
            <div
              className="flex items-center rounded-full p-0.5 bg-surface-container-high/80"
              style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.15)" }}
            >
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
                  className={`px-2.5 py-1 rounded-full text-[11px] font-bold transition-colors ${
                    lang === code
                      ? "bg-primary/20 text-primary"
                      : "text-on-surface-variant hover:text-primary"
                  }`}
                >
                  {code === "hi" ? "हिंदी" : "EN"}
                </button>
              ))}
            </div>
            <span className="material-symbols-outlined text-[20px] cursor-pointer hover:text-primary transition-colors">
              more_vert
            </span>
          </div>
        </div>

        {/* Chat Area */}
        <div
          className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scroll-smooth wa-wallpaper"
          ref={chatRef}
        >
          {/* Date Separator */}
          <div className="flex justify-center my-2">
            <span className="font-label-mono text-[10px] uppercase bg-surface-container-high text-on-surface-variant px-3 py-1 rounded-full shadow-sm">
              Today
            </span>
          </div>

          {messages.map((msg) =>
            msg.role === "bot" ? (
              <div key={msg.id} className="flex gap-2 max-w-[85%] self-start animate-fade-up">
                <div className="w-6 h-6 rounded-full bg-primary/20 flex-shrink-0 flex items-center justify-center mt-auto">
                  <img
                    src="/unnati_logo.png"
                    alt=""
                    className="w-6 h-6 rounded-full object-cover"
                  />
                </div>
                <div
                  className="bg-surface-container-highest/60 backdrop-blur-md p-3 rounded-2xl rounded-bl-sm text-on-surface font-body-md shadow-md flex flex-col gap-2"
                  style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.1)" }}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>
                  {(msg.recommendationId || msg.joined) && (
                    <div className="flex flex-wrap gap-2">
                      {msg.recommendationId && (
                        <Link
                          to={`/recommendation/${msg.recommendationId}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-surface/50 border border-primary/30 text-xs font-semibold text-primary hover:bg-primary/10 transition-colors"
                        >
                          <span className="material-symbols-outlined text-[14px]">
                            insights
                          </span>
                          {lang === "hi" ? "पूरी सिफ़ारिश देखें" : "View full recommendation"}
                        </Link>
                      )}
                      {msg.joined && (
                        <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-primary/15 border border-primary/30 text-xs font-semibold text-primary">
                          <span className="material-symbols-outlined text-[14px]">
                            task_alt
                          </span>
                          {lang === "hi" ? "पूल में जुड़ गए" : "Pool joined"}
                        </span>
                      )}
                    </div>
                  )}
                  <div className="text-[10px] text-on-surface-variant text-right mt-1 font-label-mono">
                    {msg.time}
                  </div>
                </div>
              </div>
            ) : (
              <div
                key={msg.id}
                className="flex gap-2 max-w-[85%] self-end flex-row-reverse animate-fade-up"
              >
                <div
                  className="bg-gradient-to-br from-primary-fixed to-primary-container p-3 rounded-2xl rounded-br-sm text-on-primary-fixed shadow-lg"
                  style={{ boxShadow: "0 4px 15px -3px rgba(78, 222, 163, 0.3)" }}
                >
                  <p>{msg.text}</p>
                  <div className="flex justify-end items-center gap-1 mt-1 text-[10px] font-label-mono text-on-primary-fixed/70">
                    <span>{msg.time}</span>
                    <span className="material-symbols-outlined text-[14px]">done_all</span>
                  </div>
                </div>
              </div>
            ),
          )}

          {/* Bot Typing Indicator */}
          {typing && (
            <div className="flex gap-2 max-w-[85%] self-start animate-fade-up">
              <div
                className="bg-surface-container-highest/60 backdrop-blur-md p-3 rounded-2xl rounded-bl-sm flex items-center gap-1 shadow-md"
                style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.1)" }}
              >
                <div className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce"
                  style={{ animationDelay: "0.4s" }}
                ></div>
              </div>
            </div>
          )}

          <div className="h-4"></div>
        </div>

        {/* Quick Replies */}
        <div className="flex flex-wrap gap-2 px-4 pb-2 pt-3 z-20">
          {quickReplies.map((qr) => (
            <button
              key={qr.label + qr.value}
              onClick={() => send(qr.value)}
              disabled={typing}
              className="px-4 py-2 bg-surface-container-high/80 backdrop-blur text-sm text-on-surface-variant rounded-full hover:bg-primary/20 hover:text-primary transition-all shadow-sm flex items-center gap-1 disabled:opacity-50 disabled:pointer-events-none"
              style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.2)" }}
            >
              <span className="material-symbols-outlined text-[16px]">
                {quickReplyIcon(qr.label)}
              </span>
              {qr.label}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div
          className="p-4 bg-surface-container/90 backdrop-blur-xl z-20"
          style={{ boxShadow: "inset 0 1px 0 0 rgba(110, 231, 183, 0.1)" }}
        >
          <div className="flex items-center gap-2">
            <button
              className="p-2 text-on-surface-variant hover:text-primary transition-colors"
              aria-label="Attach"
              tabIndex={-1}
            >
              <span className="material-symbols-outlined">add_circle</span>
            </button>
            <div
              className="flex-1 bg-surface-container-highest rounded-full px-4 py-2.5 flex items-center gap-2"
              style={{ boxShadow: "inset 0 0 0 1px rgba(110, 231, 183, 0.1)" }}
            >
              <input
                className="bg-transparent border-none outline-none w-full text-on-surface text-sm placeholder-on-surface-variant/50 font-body-md"
                placeholder={lang === "hi" ? "संदेश लिखें..." : "Type a message..."}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send(input);
                }}
              />
              {micSupported && (
                <button
                  type="button"
                  onClick={toggleMic}
                  disabled={typing}
                  aria-label={listening ? "Stop listening" : "Speak a message"}
                  className={`text-[20px] cursor-pointer transition-colors ${
                    listening
                      ? "text-red-500 animate-pulse"
                      : "text-on-surface-variant hover:text-primary"
                  }`}
                >
                  <span className="material-symbols-outlined">
                    {listening ? "mic_filled" : "mic"}
                  </span>
                </button>
              )}
            </div>
            <button
              className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary-container flex items-center justify-center shadow-[0_0_15px_rgba(78,222,163,0.4)] text-on-primary hover:scale-105 transition-transform disabled:opacity-60"
              onClick={() => send(input)}
              disabled={typing || input.trim() === ""}
              aria-label="Send message"
            >
              <span className="material-symbols-outlined text-[20px] ml-1">send</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
