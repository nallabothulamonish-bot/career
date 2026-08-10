import React, { useState, useRef, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MessageCircle, X, Send, Bot } from "lucide-react";
import api from "../api/axios.js";

export default function ChatbotWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi! I'm your placement assistant. Ask me about open drives, eligibility, your application status, resume tips, or mock interviews." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setMessages((m) => [...m, { from: "user", text }]);
    setInput("");
    setSending(true);
    try {
      const res = await api.post("/chatbot", { message: text });
      setMessages((m) => [...m, { from: "bot", text: res.data.reply }]);
    } catch {
      setMessages((m) => [...m, { from: "bot", text: "Sorry, something went wrong. Please try again." }]);
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
            className="w-80 h-96 bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col mb-3 overflow-hidden"
          >
            <div className="bg-gradient-to-r from-brand-600 to-accent-500 text-white px-4 py-3 flex items-center justify-between">
              <span className="flex items-center gap-2 font-medium text-sm">
                <Bot size={18} /> Placement Assistant
              </span>
              <button onClick={() => setOpen(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3 space-y-2 text-sm">
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`max-w-[85%] whitespace-pre-line px-3 py-2 rounded-lg ${
                    m.from === "user"
                      ? "bg-brand-600 text-white ml-auto rounded-br-none"
                      : "bg-gray-100 text-gray-800 rounded-bl-none"
                  }`}
                >
                  {m.text}
                </motion.div>
              ))}
              <div ref={bottomRef} />
            </div>
            <div className="p-2 border-t border-gray-200 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Ask something..."
                className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-brand-500"
              />
              <button
                onClick={send}
                disabled={sending}
                className="bg-brand-600 text-white rounded-lg px-3 flex items-center justify-center disabled:opacity-50"
              >
                <Send size={16} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setOpen((o) => !o)}
        className="bg-gradient-to-br from-brand-600 to-accent-500 text-white rounded-full p-4 shadow-lg"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </motion.button>
    </div>
  );
}
