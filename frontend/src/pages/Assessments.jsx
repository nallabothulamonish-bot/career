import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { CheckCircle2, XCircle, ArrowRight, RotateCcw, Award, Code2, BookOpen, Clock, History } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import PageTransition from "../components/PageTransition.jsx";
import CircularProgress from "../components/CircularProgress.jsx";

const STAGES = { SELECT: "select", EXAM: "exam", REPORT: "report" };

export default function Assessments() {
  const [stage, setStage] = useState(STAGES.SELECT);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("Python");
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [userAnswers, setUserAnswers] = useState({}); // { [question_id]: selected_option_index }
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchCategories();
    fetchHistory();
  }, []);

  const fetchCategories = async () => {
    try {
      const res = await api.get("/assessments/categories");
      setCategories(res.data.categories);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await api.get("/assessments/history");
      setHistory(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const startTest = async () => {
    setLoading(true);
    try {
      const res = await api.post("/assessments/start", {
        category: selectedCategory,
        num_questions: 5,
      });
      setQuestions(res.data);
      setCurrentIdx(0);
      setUserAnswers({});
      setReport(null);
      setStage(STAGES.EXAM);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to start test session.");
    } finally {
      setLoading(false);
    }
  };

  const handleOptionSelect = (optionIdx) => {
    const qid = questions[currentIdx].id;
    setUserAnswers((prev) => ({ ...prev, [qid]: optionIdx }));
  };

  const submitTest = async () => {
    // Ensure all questions have an answer
    const answersPayload = questions.map((q) => ({
      question_id: q.id,
      selected_option: userAnswers[q.id] !== undefined ? userAnswers[q.id] : -1,
    }));

    setSubmitting(true);
    try {
      const res = await api.post("/assessments/submit", {
        category: selectedCategory,
        answers: answersPayload,
      });
      setReport(res.data);
      setStage(STAGES.REPORT);
      fetchHistory();
      toast.success("Exam submitted successfully!");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to submit test.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-4xl mx-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="bg-brand-100 text-brand-600 rounded-xl p-2.5">
                <BookOpen size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold">Placement Assessment & Practice Tests</h1>
                <p className="text-xs text-gray-500">Practice technical coding & aptitude exams for campus recruitment screening</p>
              </div>
            </div>
          </div>

          <AnimatePresence mode="wait">
            {stage === STAGES.SELECT && (
              <motion.div key="select" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                  <h2 className="text-base font-semibold text-gray-900 mb-2">Select Exam Domain</h2>
                  <p className="text-xs text-gray-500 mb-5">Each test consists of 5 timed multiple-choice / output-prediction questions.</p>

                  <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-3 mb-6">
                    {categories.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => setSelectedCategory(cat)}
                        className={`p-4 rounded-xl border text-left font-medium text-sm transition flex flex-col justify-between h-24 ${
                          selectedCategory === cat
                            ? "bg-brand-600 text-white border-brand-600 shadow-sm"
                            : "bg-white text-gray-800 border-gray-200 hover:border-brand-300 hover:bg-brand-50/20"
                        }`}
                      >
                        <div className="flex items-center justify-between w-full">
                          <Code2 size={18} className={selectedCategory === cat ? "text-white" : "text-brand-600"} />
                          <span className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold opacity-80 bg-black/10">
                            Practice
                          </span>
                        </div>
                        <span>{cat}</span>
                      </button>
                    ))}
                  </div>

                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={startTest}
                    disabled={loading}
                    className="flex items-center gap-2 bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-6 py-2.5 font-medium disabled:opacity-50 text-sm"
                  >
                    {loading ? "Preparing Exam..." : "Start Practice Exam"} <ArrowRight size={16} />
                  </motion.button>
                </div>

                {/* History Section */}
                {history.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                      <History className="text-brand-600" size={18} />
                      <h3 className="font-semibold text-gray-900 text-sm">Recent Test Attempts</h3>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-3">
                      {history.map((h) => (
                        <div key={h.id} className="p-4 border rounded-xl bg-gray-50/50 flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-sm text-gray-800">{h.category}</p>
                            <p className="text-xs text-gray-400">
                              {h.correct_answers}/{h.total_questions} Correct · {new Date(h.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <span
                            className={`text-sm font-bold px-2.5 py-1 rounded-lg ${
                              h.score_percentage >= 80
                                ? "bg-green-100 text-green-700"
                                : h.score_percentage >= 60
                                ? "bg-amber-100 text-amber-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {h.score_percentage}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}

            {stage === STAGES.EXAM && questions[currentIdx] && (
              <motion.div key={`exam-${currentIdx}`} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }} className="space-y-6">
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                  {/* Progress Header */}
                  <div className="flex items-center justify-between mb-4 border-b pb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold bg-brand-50 text-brand-700 px-3 py-1 rounded-full border border-brand-200">
                        Question {currentIdx + 1} of {questions.length}
                      </span>
                      <span className="text-xs text-gray-400 font-medium">{selectedCategory}</span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      <Clock size={14} /> Timed Assessment
                    </div>
                  </div>

                  {/* Question Title */}
                  <h2 className="text-base font-semibold text-gray-900 mb-3">{questions[currentIdx].question}</h2>

                  {/* Code Snippet if present */}
                  {questions[currentIdx].code_snippet && (
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-xl text-xs font-mono mb-4 overflow-x-auto border border-gray-800">
                      <code>{questions[currentIdx].code_snippet}</code>
                    </pre>
                  )}

                  {/* Options */}
                  <div className="space-y-2.5 mb-6">
                    {questions[currentIdx].options.map((opt, idx) => {
                      const qid = questions[currentIdx].id;
                      const isSelected = userAnswers[qid] === idx;
                      return (
                        <button
                          key={idx}
                          onClick={() => handleOptionSelect(idx)}
                          className={`w-full text-left p-3.5 rounded-xl border text-sm transition flex items-center justify-between ${
                            isSelected
                              ? "bg-brand-50/70 border-brand-500 text-brand-900 font-medium ring-1 ring-brand-500"
                              : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                              isSelected ? "bg-brand-600 text-white" : "bg-gray-100 text-gray-500"
                            }`}>
                              {String.fromCharCode(65 + idx)}
                            </span>
                            <span>{opt}</span>
                          </div>
                        </button>
                      );
                    })}
                  </div>

                  {/* Navigation Footer */}
                  <div className="flex items-center justify-between pt-4 border-t">
                    <button
                      onClick={() => setCurrentIdx((prev) => Math.max(0, prev - 1))}
                      disabled={currentIdx === 0}
                      className="px-4 py-2 text-xs font-medium text-gray-600 border rounded-xl disabled:opacity-40 hover:bg-gray-50"
                    >
                      Previous
                    </button>

                    {currentIdx + 1 < questions.length ? (
                      <button
                        onClick={() => setCurrentIdx((prev) => prev + 1)}
                        className="flex items-center gap-1.5 bg-brand-600 text-white px-5 py-2 text-xs font-medium rounded-xl hover:bg-brand-700"
                      >
                        Next Question <ArrowRight size={14} />
                      </button>
                    ) : (
                      <button
                        onClick={submitTest}
                        disabled={submitting}
                        className="flex items-center gap-1.5 bg-gradient-to-r from-brand-600 to-accent-500 text-white px-6 py-2 text-xs font-semibold rounded-xl shadow-sm disabled:opacity-50"
                      >
                        {submitting ? "Submitting..." : "Submit Exam"}
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {stage === STAGES.REPORT && report && (
              <motion.div key="report" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm text-center">
                  <Award className="mx-auto text-brand-600 mb-2" size={36} />
                  <h2 className="text-xl font-bold text-gray-900 mb-1">{report.category} Test Score</h2>
                  <CircularProgress value={report.score_percentage} size={110} strokeWidth={8} label="score" />
                  <p className="text-sm font-semibold text-gray-800 mt-4">
                    {report.correct_answers} / {report.total_questions} Questions Correct
                  </p>
                  <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">{report.performance_summary}</p>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 text-base">Detailed Question Explanations</h3>
                  {report.feedback.map((item, i) => (
                    <div key={i} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          {item.is_correct ? (
                            <CheckCircle2 className="text-green-600 shrink-0" size={20} />
                          ) : (
                            <XCircle className="text-red-500 shrink-0" size={20} />
                          )}
                          <p className="font-semibold text-sm text-gray-800">Q{i + 1}. {item.question}</p>
                        </div>
                        <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold shrink-0 ${
                          item.is_correct ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                        }`}>
                          {item.is_correct ? "Correct" : "Incorrect"}
                        </span>
                      </div>

                      {item.code_snippet && (
                        <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg text-xs font-mono overflow-x-auto">
                          <code>{item.code_snippet}</code>
                        </pre>
                      )}

                      <div className="space-y-1.5 text-xs">
                        <p className="text-gray-600">
                          <strong className="text-gray-700">Your Answer:</strong>{" "}
                          <span className={item.is_correct ? "text-green-700 font-medium" : "text-red-600 font-medium"}>
                            {item.user_selected >= 0 ? item.options[item.user_selected] : "Not Answered"}
                          </span>
                        </p>
                        {!item.is_correct && (
                          <p className="text-gray-600">
                            <strong className="text-gray-700">Correct Answer:</strong>{" "}
                            <span className="text-green-700 font-semibold">{item.options[item.correct_option]}</span>
                          </p>
                        )}
                      </div>

                      <div className="bg-blue-50/70 border border-blue-100 p-3 rounded-xl text-xs text-blue-900">
                        <strong>Explanation:</strong> {item.explanation}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={() => setStage(STAGES.SELECT)}
                    className="flex items-center gap-2 bg-brand-600 text-white rounded-xl px-5 py-2.5 font-medium text-xs hover:bg-brand-700"
                  >
                    <RotateCcw size={15} /> Practice Another Category
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </PageTransition>
    </div>
  );
}
