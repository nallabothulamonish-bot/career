import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { UserCircle, FileText, MessageSquareText, ArrowRight } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import JobCard from "../components/JobCard.jsx";
import MatchScoreBadge from "../components/MatchScoreBadge.jsx";
import ChatbotWidget from "../components/ChatbotWidget.jsx";
import PageTransition from "../components/PageTransition.jsx";

export default function StudentDashboard() {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [tab, setTab] = useState("jobs");
  const [applyingId, setApplyingId] = useState(null);

  const load = async () => {
    const [jobsRes, appsRes] = await Promise.all([
      api.get("/jobs", { params: { status: "open" } }),
      api.get("/applications/mine"),
    ]);
    setJobs(jobsRes.data);
    setApplications(appsRes.data);
  };

  useEffect(() => { load(); }, []);

  const appliedJobIds = new Set(applications.map((a) => a.job?.id));

  const handleApply = async (jobId) => {
    setApplyingId(jobId);
    try {
      const res = await api.post(`/applications/${jobId}/apply`);
      toast.success(`Applied! AI match score: ${res.data.match_details.score}%`);
      await load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to apply");
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-5xl mx-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold">Student Dashboard</h1>
            <Link to="/profile" className="flex items-center gap-1.5 text-sm text-brand-600 font-medium">
              <UserCircle size={18} /> Edit Profile
            </Link>
          </div>

          <div className="grid md:grid-cols-2 gap-4 mb-8">
            <FeatureBanner
              to="/resume-analyzer" icon={FileText}
              title="AI Resume Analyzer"
              desc="Get an instant ATS score, keyword gaps, and improvement tips."
              gradient="from-brand-600 to-brand-500"
            />
            <FeatureBanner
              to="/mock-interview" icon={MessageSquareText}
              title="Mock Interview Practice"
              desc="Practice role-specific questions and get AI-scored feedback."
              gradient="from-accent-500 to-accent-400"
            />
          </div>

          <div className="flex gap-2 mb-6 border-b border-gray-200">
            {[
              { key: "jobs", label: "Open Drives" },
              { key: "applications", label: `My Applications (${applications.length})` },
            ].map((t) => (
              <button
                key={t.key} onClick={() => setTab(t.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                  tab === t.key ? "border-brand-600 text-brand-600" : "border-transparent text-gray-500"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {tab === "jobs" && (
            <div className="grid md:grid-cols-2 gap-4">
              {jobs.length === 0 && <p className="text-gray-400 text-sm">No open drives right now.</p>}
              {jobs.map((job, i) => (
                <JobCard
                  key={job.id} job={job} index={i}
                  actionSlot={
                    appliedJobIds.has(job.id) ? (
                      <span className="text-xs text-green-600 font-medium">✓ Already Applied</span>
                    ) : (
                      <motion.button
                        whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                        onClick={() => handleApply(job.id)}
                        disabled={applyingId === job.id}
                        className="bg-gradient-to-r from-brand-600 to-accent-500 text-white text-sm px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
                      >
                        {applyingId === job.id ? "Applying..." : "Apply with AI Match"}
                      </motion.button>
                    )
                  }
                />
              ))}
            </div>
          )}

          {tab === "applications" && (
            <div className="space-y-3">
              {applications.length === 0 && <p className="text-gray-400 text-sm">You haven't applied to any drives yet.</p>}
              {applications.map((app) => (
                <motion.div
                  key={app.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                  className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between shadow-sm"
                >
                  <div>
                    <p className="font-semibold text-gray-900">{app.job?.title}</p>
                    <p className="text-sm text-gray-500">{app.job?.company}</p>
                    {app.missing_skills?.length > 0 && (
                      <p className="text-xs text-amber-600 mt-1">Missing skills: {app.missing_skills.join(", ")}</p>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <MatchScoreBadge score={app.match_score} />
                    <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600">{app.status}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </PageTransition>
      <ChatbotWidget />
    </div>
  );
}

function FeatureBanner({ to, icon: Icon, title, desc, gradient }) {
  return (
    <Link to={to}>
      <motion.div
        whileHover={{ y: -3, scale: 1.01 }}
        className={`bg-gradient-to-br ${gradient} text-white rounded-2xl p-5 flex items-center justify-between shadow-md cursor-pointer`}
      >
        <div className="flex items-center gap-4">
          <div className="bg-white/20 rounded-xl p-3">
            <Icon size={24} />
          </div>
          <div>
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-white/80">{desc}</p>
          </div>
        </div>
        <ArrowRight size={20} />
      </motion.div>
    </Link>
  );
}
