import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { FileSearch, CheckCircle2, AlertCircle, Sparkles, Upload, FileText, X } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import PageTransition from "../components/PageTransition.jsx";
import CircularProgress from "../components/CircularProgress.jsx";

export default function ResumeAnalyzer() {
  const [activeTab, setActiveTab] = useState("upload"); // 'upload' | 'text'
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [targetTitle, setTargetTitle] = useState("");
  const [targetDesc, setTargetDesc] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const ext = selected.name.toLowerCase();
      if (!ext.endsWith(".pdf") && !ext.endsWith(".docx") && !ext.endsWith(".doc") && !ext.endsWith(".txt")) {
        toast.error("Please select a PDF, DOCX, or TXT document.");
        return;
      }
      setFile(selected);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const selected = e.dataTransfer.files[0];
      const ext = selected.name.toLowerCase();
      if (!ext.endsWith(".pdf") && !ext.endsWith(".docx") && !ext.endsWith(".doc") && !ext.endsWith(".txt")) {
        toast.error("Please drop a PDF, DOCX, or TXT document.");
        return;
      }
      setFile(selected);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      let res;
      if (activeTab === "upload") {
        if (!file) {
          toast.error("Please upload a resume file first.");
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append("file", file);
        formData.append("target_job_title", targetTitle);
        formData.append("target_job_description", targetDesc);

        res = await api.post("/resume/upload-and-analyze", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      } else {
        if (!resumeText.trim() || resumeText.trim().length < 30) {
          toast.error("Paste more of your resume content for an accurate analysis.");
          setLoading(false);
          return;
        }
        res = await api.post("/resume/analyze", {
          resume_text: resumeText,
          target_job_title: targetTitle,
          target_job_description: targetDesc,
        });
      }
      setResult(res.data);
      toast.success("Analysis complete!");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to analyze resume");
    } finally {
      setLoading(false);
    }
  };

  const loadFromProfile = async () => {
    try {
      const res = await api.get("/students/me");
      if (res.data.resume_text) {
        setResumeText(res.data.resume_text);
        setActiveTab("text");
        toast.success("Loaded resume text from your profile.");
      } else {
        toast.error("No resume text saved in your profile yet.");
      }
    } catch {
      toast.error("Could not load profile.");
    }
  };

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-4xl mx-auto p-6">
          <div className="flex items-center gap-3 mb-1">
            <div className="bg-brand-100 text-brand-600 rounded-xl p-2">
              <FileSearch size={22} />
            </div>
            <h1 className="text-xl font-bold">AI Resume Analyzer</h1>
          </div>
          <p className="text-sm text-gray-500 mb-6 ml-12">
            Upload your resume PDF/Word document or paste text to get an instant ATS-style score, structure feedback, and keyword gap analysis.
          </p>

          <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm space-y-5">
            {/* Input Mode Selector */}
            <div className="flex border border-gray-200 rounded-xl p-1 bg-gray-50 max-w-md">
              <button
                type="button"
                onClick={() => setActiveTab("upload")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-medium rounded-lg transition ${
                  activeTab === "upload" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-800"
                }`}
              >
                <Upload size={14} /> Upload PDF / DOCX
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("text")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-medium rounded-lg transition ${
                  activeTab === "text" ? "bg-white text-brand-700 shadow-sm" : "text-gray-500 hover:text-gray-800"
                }`}
              >
                <FileText size={14} /> Paste Plain Text
              </button>
            </div>

            <form onSubmit={handleAnalyze} className="space-y-4">
              {activeTab === "upload" ? (
                <div>
                  {!file ? (
                    <div
                      onDragOver={(e) => e.preventDefault()}
                      onDrop={handleDrop}
                      className="border-2 border-dashed border-gray-300 hover:border-brand-500 rounded-2xl p-8 text-center bg-gray-50/50 hover:bg-brand-50/30 transition cursor-pointer"
                    >
                      <input
                        type="file"
                        id="resume-file-input"
                        accept=".pdf,.docx,.doc,.txt"
                        className="hidden"
                        onChange={handleFileChange}
                      />
                      <label htmlFor="resume-file-input" className="cursor-pointer space-y-2 block">
                        <div className="mx-auto w-12 h-12 bg-brand-100 text-brand-600 rounded-full flex items-center justify-center">
                          <Upload size={22} />
                        </div>
                        <p className="text-sm font-semibold text-gray-700">Click to upload or drag & drop</p>
                        <p className="text-xs text-gray-400">Supports PDF, DOCX, DOC, or TXT (Max 10MB)</p>
                      </label>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between p-4 border border-brand-200 bg-brand-50/50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <FileText className="text-brand-600" size={24} />
                        <div>
                          <p className="text-sm font-medium text-gray-800">{file.name}</p>
                          <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setFile(null)}
                        className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-white"
                      >
                        <X size={18} />
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs text-gray-500">Resume Content</label>
                    <button type="button" onClick={loadFromProfile} className="text-xs text-brand-600 font-medium">
                      Load from my profile
                    </button>
                  </div>
                  <textarea
                    rows={8}
                    required={activeTab === "text"}
                    placeholder="Paste your full resume text here..."
                    className="w-full border rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-brand-500/20"
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                  />
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-3 pt-2">
                <input
                  placeholder="Target job title (optional, e.g. Software Engineer)"
                  className="border rounded-xl px-3 py-2 text-sm"
                  value={targetTitle}
                  onChange={(e) => setTargetTitle(e.target.value)}
                />
              </div>
              <textarea
                rows={3}
                placeholder="Paste target job description for a role-specific keyword match (optional, but recommended)"
                className="w-full border rounded-xl px-3 py-2 text-sm"
                value={targetDesc}
                onChange={(e) => setTargetDesc(e.target.value)}
              />

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                disabled={loading}
                className="flex items-center gap-2 bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-5 py-2.5 font-medium disabled:opacity-50"
              >
                <Sparkles size={16} /> {loading ? "Analyzing Document..." : "Analyze Resume"}
              </motion.button>
            </form>
          </div>

          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-8 space-y-6"
              >
                <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                  <h2 className="font-semibold mb-4">Your Scores</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <ScoreItem value={result.ats_score} label="Overall ATS" />
                    <ScoreItem value={result.structure_score} label="Structure" />
                    <ScoreItem value={result.readability_score} label="Readability" />
                    <ScoreItem value={result.keyword_score} label="Keyword Match" />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                    <h3 className="font-semibold text-green-700 flex items-center gap-2 mb-3">
                      <CheckCircle2 size={18} /> Strengths
                    </h3>
                    <ul className="space-y-2 text-sm text-gray-600">
                      {result.strengths.map((s, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-green-500">•</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                    <h3 className="font-semibold text-amber-700 flex items-center gap-2 mb-3">
                      <AlertCircle size={18} /> Suggestions
                    </h3>
                    <ul className="space-y-2 text-sm text-gray-600">
                      {result.suggestions.map((s, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-amber-500">•</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {result.detected_skills?.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
                    <h3 className="font-semibold mb-3">Detected Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {result.detected_skills.map((s) => (
                        <span key={s} className="text-xs bg-brand-50 text-brand-700 px-2.5 py-1 rounded-full">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </PageTransition>
    </div>
  );
}

function ScoreItem({ value, label }) {
  return (
    <div className="flex flex-col items-center gap-2">
      <CircularProgress value={value} size={80} strokeWidth={7} />
      <span className="text-xs text-gray-500 text-center">{label}</span>
    </div>
  );
}
