import React, { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircle, X, Send, Bot, ExternalLink, Sparkles, MapPin, Briefcase, Building2, RefreshCw } from "lucide-react";
import api from "../api/axios.js";

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    {
      from: "bot",
      text: "Hi! I'm your CareerPilot AI Assistant. Ask me about active jobs, your applications, eligibility, resume tips, or mock interview prep!",
      jobs: [],
      suggestions: [
        "Show jobs in Bangalore",
        "Any internships in Hyderabad?",
        "Check my eligibility",
        "Analyze my resume"
      ]
    },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending, open]);

  const sendQuery = async (queryText) => {
    const text = queryText.trim();
    if (!text || sending) return;

    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setSending(true);

    try {
      const res = await api.post("/chatbot", {
        message: text,
        session_id: sessionId || undefined
      });

      const data = res.data;
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      setMessages((m) => [
        ...m,
        {
          from: "bot",
          text: data.message || "Here is what I found for you:",
          jobs: data.jobs || [],
          suggestions: data.suggestions || []
        }
      ]);
    } catch (err) {
      console.error("Chatbot API error:", err);
      setMessages((m) => [
        ...m,
        {
          from: "bot",
          text: "Sorry, I ran into an error connecting to the career database. Please try again!",
          jobs: [],
          suggestions: ["Show active jobs", "Check my eligibility"]
        }
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="w-[350px] sm:w-[410px] h-[530px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col mb-3 overflow-hidden font-sans"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-brand-600 to-indigo-600 text-white px-4 py-3.5 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
                  <Bot size={19} className="text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-sm leading-tight flex items-center gap-1.5">
                    CareerPilot AI Assistant <Sparkles size={13} className="text-amber-300 fill-amber-300" />
                  </h3>
                  <p className="text-[11px] text-brand-100 font-medium">Database-Aware Career Advisor</p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="w-7 h-7 rounded-full hover:bg-white/20 flex items-center justify-center transition-colors text-white"
              >
                <X size={18} />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 text-sm bg-gray-50/50">
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex flex-col ${m.from === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[88%] whitespace-pre-line px-3.5 py-2.5 rounded-2xl text-xs sm:text-sm leading-relaxed ${
                      m.from === "user"
                        ? "bg-brand-600 text-white rounded-br-none shadow-sm font-medium"
                        : "bg-white text-gray-800 rounded-bl-none border border-gray-200/80 shadow-sm"
                    }`}
                  >
                    {m.text}
                  </div>

                  {/* Inline Job Cards */}
                  {m.jobs && m.jobs.length > 0 && (
                    <div className="mt-2.5 space-y-2 w-full max-w-[92%]">
                      {m.jobs.map((job) => (
                        <div
                          key={job.id}
                          className="bg-white border border-gray-200 rounded-xl p-3 shadow-xs hover:border-brand-300 transition-all text-xs"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <div className="w-7 h-7 rounded-lg bg-brand-100 text-brand-700 font-bold text-xs flex items-center justify-center shrink-0">
                                {job.company?.[0]?.toUpperCase() || "C"}
                              </div>
                              <div>
                                <span className="font-bold text-gray-900 leading-tight block">{job.title}</span>
                                <span className="text-[11px] text-gray-600 font-medium">{job.company}</span>
                              </div>
                            </div>
                            {job.match_score != null && (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 shrink-0">
                                {Math.round(job.match_score)}% Match
                              </span>
                            )}
                          </div>

                          <div className="flex items-center gap-2 mt-2 text-[11px] text-gray-500">
                            <span className="flex items-center gap-0.5 font-medium text-gray-700">
                              <Briefcase size={11} className="text-brand-500" /> {job.job_type || "Full-Time"}
                            </span>
                            <span>•</span>
                            <span className="flex items-center gap-0.5 truncate">
                              <MapPin size={11} className="text-gray-400" /> {job.location || "Remote"}
                            </span>
                          </div>

                          {job.application_url && (
                            <a
                              href={job.application_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-2.5 w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-gray-900 hover:bg-gray-800 text-white rounded-lg text-[11px] font-semibold transition shadow-xs"
                            >
                              Apply on Official Site <ExternalLink size={11} />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Interactive Suggestion Chips */}
                  {m.suggestions && m.suggestions.length > 0 && i === messages.length - 1 && !sending && (
                    <div className="flex flex-wrap gap-1.5 mt-2.5 max-w-[95%]">
                      {m.suggestions.map((sug, idx) => (
                        <button
                          key={idx}
                          onClick={() => sendQuery(sug)}
                          className="text-[11px] font-medium bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200/80 px-2.5 py-1 rounded-full transition-colors flex items-center gap-1"
                        >
                          <Sparkles size={10} className="text-brand-500" /> {sug}
                        </button>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}

              {/* Typing Skeleton */}
              {sending && (
                <div className="flex items-center gap-2 text-gray-400 bg-white border border-gray-200 px-3 py-2 rounded-2xl rounded-bl-none w-fit text-xs">
                  <RefreshCw size={12} className="animate-spin text-brand-600" />
                  <span>Searching career database...</span>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {/* Input Footer */}
            <div className="p-2.5 border-t border-gray-200 bg-white flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendQuery(input)}
                placeholder="Ask about jobs, eligibility, applications..."
                className="flex-1 border border-gray-200 rounded-xl px-3.5 py-2 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-gray-50"
              />
              <button
                onClick={() => sendQuery(input)}
                disabled={sending || !input.trim()}
                className="bg-brand-600 hover:bg-brand-700 text-white rounded-xl px-3.5 flex items-center justify-center transition disabled:opacity-50 shadow-sm"
              >
                <Send size={15} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen((o) => !o)}
        className="bg-gradient-to-br from-brand-600 to-indigo-600 text-white rounded-full p-3.5 shadow-xl border border-white/20 flex items-center justify-center"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </motion.button>
    </div>
  );
}
