import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import {
  MessageSquareText,
  ArrowRight,
  RotateCcw,
  Award,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  History,
  Calendar,
  Trash2,
  ChevronDown,
  ChevronUp,
  Database,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import PageTransition from "../components/PageTransition.jsx";
import CircularProgress from "../components/CircularProgress.jsx";

const STAGES = { PICK_ROLE: "pick_role", IN_PROGRESS: "in_progress", RESULTS: "results" };

export default function MockInterview() {
  const [stage, setStage] = useState(STAGES.PICK_ROLE);
  const [categories, setCategories] = useState([]);
  const [role, setRole] = useState("");
  const [session, setSession] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [lastFeedback, setLastFeedback] = useState(null);
  const [finalResult, setFinalResult] = useState(null);
  const [starting, setStarting] = useState(false);
  const [history, setHistory] = useState([]);
  const [expandedHistoryId, setExpandedHistoryId] = useState(null);

  // Mic & Speech Synthesis state
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);

  const recognitionRef = useRef(null);
  const baseTextRef = useRef("");
  const finalSpeechRef = useRef("");

  useEffect(() => {
    fetchCategories();
    fetchHistory();

    // Setup Web Speech API for voice recording
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setSpeechSupported(true);
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = "en-US";

      rec.onresult = (event) => {
        let newFinal = "";
        let currentInterim = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const textChunk = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            newFinal += textChunk + " ";
          } else {
            currentInterim += textChunk;
          }
        }

        if (newFinal) {
          finalSpeechRef.current += newFinal;
        }

        const fullSpeech = (finalSpeechRef.current + currentInterim).trim();
        const base = baseTextRef.current ? baseTextRef.current.trim() : "";
        const combined = base ? `${base} ${fullSpeech}` : fullSpeech;

        setAnswer(combined);
      };

      rec.onerror = (err) => {
        console.error("Speech recognition error:", err);
        setIsListening(false);
      };

      rec.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = rec;
    }
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await api.get("/interview/categories");
      setCategories(res.data.categories);
    } catch (err) {
      console.error("Error fetching categories:", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await api.get("/interview/history");
      setHistory(res.data);
    } catch (err) {
      console.error("Error fetching interview history:", err);
    }
  };

  // Speak AI question out loud when current question changes
  useEffect(() => {
    if (stage === STAGES.IN_PROGRESS && questions[currentIdx] && voiceEnabled) {
      speakText(`Question ${currentIdx + 1}: ${questions[currentIdx].question}`);
    }
  }, [currentIdx, stage, questions, voiceEnabled]);

  const speakText = (text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel(); // stop previous audio
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  };

  const toggleListening = () => {
    if (!speechSupported) {
      toast.error("Web Speech API is not supported in this browser. Try Chrome or Edge.");
      return;
    }
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        baseTextRef.current = answer.trim();
        finalSpeechRef.current = "";
        recognitionRef.current?.start();
        setIsListening(true);
        toast.success("Microphone active — start speaking your answer!");
      } catch (err) {
        console.error(err);
        toast.error("Failed to start microphone. Please try again.");
      }
    }
  };

  const clearAnswer = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }
    setAnswer("");
    baseTextRef.current = "";
    finalSpeechRef.current = "";
  };

  const startInterview = async () => {
    if (!role) return toast.error("Pick a role first.");
    setStarting(true);
    try {
      const res = await api.post("/interview/start", { role_category: role, num_questions: 5 });
      setSession(res.data.session_id);
      setQuestions(res.data.questions);
      setCurrentIdx(0);
      setAnswer("");
      baseTextRef.current = "";
      finalSpeechRef.current = "";
      setLastFeedback(null);
      setStage(STAGES.IN_PROGRESS);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to start interview");
    } finally {
      setStarting(false);
    }
  };

  const submitAnswer = async () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }
    if (!answer.trim() || answer.trim().length < 5) {
      toast.error("Please provide a more complete answer.");
      return;
    }
    setSubmitting(true);
    try {
      const q = questions[currentIdx];
      const res = await api.post("/interview/answer", {
        session_id: session,
        question_id: q.question_id,
        question: q.question,
        category: q.category,
        answer: answer.trim(),
      });
      setLastFeedback(res.data);
      if (voiceEnabled) {
        speakText(`Your score is ${res.data.score} percent. ${res.data.feedback.join(". ")}`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to submit answer");
    } finally {
      setSubmitting(false);
    }
  };

  const nextQuestion = async () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    if (currentIdx + 1 < questions.length) {
      setCurrentIdx((i) => i + 1);
      setAnswer("");
      baseTextRef.current = "";
      finalSpeechRef.current = "";
      setLastFeedback(null);
    } else {
      try {
        const res = await api.post("/interview/complete", { session_id: session });
        setFinalResult(res.data);
        setStage(STAGES.RESULTS);
        fetchHistory(); // Refresh database history
        if (voiceEnabled) {
          speakText(`Interview session complete. Your overall score is ${res.data.overall_score} percent.`);
        }
      } catch (err) {
        toast.error(err.response?.data?.detail || "Failed to complete session");
      }
    }
  };

  const restart = () => {
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setStage(STAGES.PICK_ROLE);
    setRole("");
    setSession(null);
    setQuestions([]);
    setCurrentIdx(0);
    setAnswer("");
    baseTextRef.current = "";
    finalSpeechRef.current = "";
    setLastFeedback(null);
    setFinalResult(null);
  };

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-3xl mx-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-brand-500/10 to-accent-500/10 text-brand-600 rounded-xl p-2.5 border border-brand-200/50">
                <MessageSquareText size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI Voice Mock Interview</h1>
                <p className="text-xs text-gray-500">
                  Speak into your microphone or type answers to practice real-time technical & behavioral rounds
                </p>
              </div>
            </div>

            {/* Voice controls */}
            <button
              onClick={() => setVoiceEnabled(!voiceEnabled)}
              title={voiceEnabled ? "Mute AI Voice" : "Enable AI Voice"}
              className={`p-2.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition ${
                voiceEnabled
                  ? "bg-brand-50 border-brand-200 text-brand-700 shadow-sm"
                  : "bg-gray-100 border-gray-200 text-gray-500"
              }`}
            >
              {voiceEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
              {voiceEnabled ? "AI Voice ON" : "AI Voice OFF"}
            </button>
          </div>

          <AnimatePresence mode="wait">
            {stage === STAGES.PICK_ROLE && (
              <motion.div key="pick" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                  <p className="text-sm font-semibold text-gray-800 mb-3">Choose Role Domain to Practice:</p>
                  <div className="grid sm:grid-cols-3 gap-3 mb-6">
                    {categories.map((c) => (
                      <motion.button
                        key={c}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setRole(c)}
                        className={`p-4 rounded-xl border text-sm font-medium transition text-left flex flex-col justify-between h-20 ${
                          role === c
                            ? "bg-brand-600 text-white border-brand-600 shadow-md ring-2 ring-brand-400/30"
                            : "bg-white text-gray-700 border-gray-200 hover:border-brand-400 hover:bg-gray-50"
                        }`}
                      >
                        <span className="text-xs opacity-75 font-normal">Practice Domain</span>
                        <span className="font-semibold">{c}</span>
                      </motion.button>
                    ))}
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={startInterview}
                    disabled={starting}
                    className="flex items-center gap-2 bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-6 py-2.5 font-medium disabled:opacity-50 text-sm shadow-sm"
                  >
                    {starting ? "Initializing AI Interviewer..." : "Start Interview Round"} <ArrowRight size={16} />
                  </motion.button>
                </div>

                {/* Past Sessions Saved in Database */}
                {history.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <History className="text-brand-600" size={18} />
                        <h3 className="font-semibold text-gray-900 text-sm">Past Interview History</h3>
                      </div>
                      <span className="inline-flex items-center gap-1.5 text-xs text-green-700 bg-green-50 px-2.5 py-1 rounded-full border border-green-200 font-medium">
                        <Database size={13} /> Connected to Database
                      </span>
                    </div>

                    <div className="space-y-3">
                      {history.map((s) => {
                        const isExpanded = expandedHistoryId === s.id;
                        return (
                          <div key={s.id} className="border rounded-xl bg-gray-50/60 overflow-hidden transition">
                            <button
                              onClick={() => setExpandedHistoryId(isExpanded ? null : s.id)}
                              className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-100/60 transition"
                            >
                              <div className="flex items-center gap-3">
                                <div className="p-2 bg-brand-50 text-brand-600 rounded-lg">
                                  <Sparkles size={16} />
                                </div>
                                <div>
                                  <p className="font-semibold text-sm text-gray-900">{s.role_category}</p>
                                  <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                                    <Calendar size={12} /> {new Date(s.created_at).toLocaleDateString()} · Saved in DB
                                  </p>
                                </div>
                              </div>

                              <div className="flex items-center gap-3">
                                <span
                                  className={`text-xs font-bold px-3 py-1 rounded-lg ${
                                    s.overall_score >= 80
                                      ? "bg-green-100 text-green-700 border border-green-200"
                                      : s.overall_score >= 60
                                      ? "bg-amber-100 text-amber-700 border border-amber-200"
                                      : "bg-red-100 text-red-700 border border-red-200"
                                  }`}
                                >
                                  {s.overall_score}%
                                </span>
                                {isExpanded ? <ChevronUp size={16} className="text-gray-400" /> : <ChevronDown size={16} className="text-gray-400" />}
                              </div>
                            </button>

                            {/* Expanded details saved in DB */}
                            {isExpanded && s.answers && (
                              <div className="p-4 bg-white border-t border-gray-200 space-y-3">
                                <p className="text-xs text-gray-600 italic bg-brand-50/50 p-2.5 rounded-lg border border-brand-100">
                                  "{s.summary}"
                                </p>

                                <div className="space-y-2">
                                  {s.answers.map((a, idx) => (
                                    <div key={idx} className="p-3 border rounded-lg bg-gray-50/40 text-xs space-y-1.5">
                                      <div className="flex items-center justify-between font-semibold text-gray-800">
                                        <span>Q{idx + 1}: {a.question}</span>
                                        <span className="text-brand-700 font-bold bg-brand-50 px-2 py-0.5 rounded border border-brand-200">
                                          {a.score}%
                                        </span>
                                      </div>
                                      <p className="text-gray-600 bg-white p-2 rounded border border-gray-100 italic">
                                        "{a.answer}"
                                      </p>
                                      {a.feedback && a.feedback.length > 0 && (
                                        <ul className="text-gray-500 space-y-0.5 pl-2">
                                          {a.feedback.map((f, fIdx) => (
                                            <li key={fIdx}>• {f}</li>
                                          ))}
                                        </ul>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {stage === STAGES.IN_PROGRESS && questions[currentIdx] && (
              <motion.div
                key={`q-${currentIdx}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-medium text-brand-600 bg-brand-50 px-3 py-1 rounded-full border border-brand-200">
                    Question {currentIdx + 1} of {questions.length} · {questions[currentIdx].category}
                  </span>
                  <button
                    onClick={() => speakText(questions[currentIdx].question)}
                    className="text-xs text-brand-600 flex items-center gap-1 font-medium hover:underline"
                  >
                    <Volume2 size={14} /> Replay Question Audio
                  </button>
                </div>

                <h2 className="font-semibold text-gray-900 text-lg mb-4">{questions[currentIdx].question}</h2>

                {!lastFeedback ? (
                  <>
                    <div className="relative mb-4">
                      <textarea
                        rows={6}
                        placeholder="Type your response or click the microphone button below to speak..."
                        className="w-full border border-gray-300 rounded-xl px-3.5 py-3 text-sm focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition"
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                      />

                      {/* Clear text button */}
                      {answer.length > 0 && (
                        <button
                          onClick={clearAnswer}
                          title="Clear answer text"
                          className="absolute top-3 right-3 text-gray-400 hover:text-red-500 p-1 transition"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}

                      {/* Mic active live indicator */}
                      {isListening && (
                        <div className="absolute bottom-3 left-3 flex items-center gap-2 bg-red-50 text-red-600 px-3 py-1 rounded-full text-xs font-semibold border border-red-200 animate-pulse">
                          <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
                          Live Mic Active — speak clearly...
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <motion.button
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={toggleListening}
                          type="button"
                          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-xs transition border ${
                            isListening
                              ? "bg-red-500 text-white border-red-500 shadow-md animate-pulse"
                              : "bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200"
                          }`}
                        >
                          {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                          {isListening ? "Stop Listening" : "Speak Answer (Mic)"}
                        </motion.button>
                      </div>

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={submitAnswer}
                        disabled={submitting}
                        className="bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-6 py-2.5 text-sm font-semibold disabled:opacity-50 shadow-sm"
                      >
                        {submitting ? "Evaluating Answer..." : "Submit Answer"}
                      </motion.button>
                    </div>
                  </>
                ) : (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                    <div className="flex items-center gap-4 bg-gray-50 p-4 rounded-xl border border-gray-200">
                      <CircularProgress value={lastFeedback.score} size={76} strokeWidth={7} />
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-base font-bold text-gray-900">Answer Score: {lastFeedback.score}%</p>
                          <span
                            className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                              lastFeedback.score >= 80
                                ? "bg-green-50 text-green-700 border-green-200"
                                : lastFeedback.score >= 65
                                ? "bg-amber-50 text-amber-700 border-amber-200"
                                : "bg-red-50 text-red-700 border-red-200"
                            }`}
                          >
                            {lastFeedback.score >= 80 ? "High Relevance" : lastFeedback.score >= 65 ? "Good Answer" : "Needs Detail"}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          Evaluated on technical concept match, word count, active ownership language & delivery.
                        </p>
                      </div>
                    </div>

                    <div className="bg-white p-4 rounded-xl border border-gray-200 space-y-2">
                      <p className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                        <CheckCircle2 size={14} className="text-brand-600" /> AI Feedback & Actionable Insights:
                      </p>
                      <ul className="space-y-2 text-xs text-gray-600">
                        {lastFeedback.feedback.map((f, i) => (
                          <li key={i} className="flex items-start gap-2 bg-gray-50 p-2.5 rounded-lg border border-gray-100">
                            <span className="text-brand-500 font-bold mt-0.5">•</span>
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={nextQuestion}
                      className="flex items-center gap-2 bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-5 py-2.5 font-medium text-sm shadow-sm"
                    >
                      {currentIdx + 1 < questions.length ? "Next Question" : "Finish & Save Session to Database"}{" "}
                      <ArrowRight size={16} />
                    </motion.button>
                  </motion.div>
                )}
              </motion.div>
            )}

            {stage === STAGES.RESULTS && finalResult && (
              <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm text-center">
                  <Award className="mx-auto text-brand-600 mb-2" size={36} />
                  <h2 className="text-xl font-bold text-gray-900 mb-2">Interview Performance Summary</h2>
                  <CircularProgress value={finalResult.overall_score} size={110} strokeWidth={9} label="overall" />
                  <p className="text-gray-700 text-sm font-medium mt-4 max-w-md mx-auto">{finalResult.summary}</p>
                  <p className="text-xs text-green-600 mt-2 font-semibold flex items-center justify-center gap-1">
                    <CheckCircle2 size={14} /> Saved to Database History
                  </p>
                </div>

                <div className="space-y-3">
                  {finalResult.answers.map((a, i) => (
                    <div key={i} className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-sm text-gray-800">Q{i + 1}. {a.question}</p>
                        <span className="text-xs font-bold text-brand-700 bg-brand-50 px-2.5 py-0.5 rounded border border-brand-200">
                          {a.score}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg italic">"{a.answer}"</p>
                      <ul className="text-xs text-gray-600 space-y-1 pl-2">
                        {a.feedback.map((f, j) => (
                          <li key={j}>• {f}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={restart}
                  className="flex items-center gap-2 bg-gray-100 text-gray-700 rounded-xl px-5 py-2.5 font-medium text-sm hover:bg-gray-200"
                >
                  <RotateCcw size={16} /> Practice Another Round
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </PageTransition>
    </div>
  );
}
