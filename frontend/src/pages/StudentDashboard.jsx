import React, { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { UserCircle, FileText, MessageSquareText, ArrowRight, Search, Filter, Sparkles, ChevronLeft, ChevronRight, RefreshCw, Briefcase, Building2, MapPin } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import JobCard from "../components/JobCard.jsx";
import MatchScoreBadge from "../components/MatchScoreBadge.jsx";
import ChatbotWidget from "../components/ChatbotWidget.jsx";
import PageTransition from "../components/PageTransition.jsx";

export default function StudentDashboard() {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [tab, setTab] = useState("jobs");
  
  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selectedCompany, setSelectedCompany] = useState("");
  const [selectedJobType, setSelectedJobType] = useState("");
  const [isRemoteOnly, setIsRemoteOnly] = useState(false);
  const [isRecommendedMode, setIsRecommendedMode] = useState(false);

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  const [loading, setLoading] = useState(true);
  const [applyingId, setApplyingId] = useState(null);

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [searchQuery]);

  // Load distinct hiring companies
  useEffect(() => {
    api.get("/jobs/companies")
      .then((res) => setCompanies(res.data || []))
      .catch((err) => console.error("Failed to load companies:", err));
  }, []);

  // Fetch Jobs based on filters & pagination
  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      if (isRecommendedMode) {
        const res = await api.get("/jobs/recommended", { params: { page, limit: 20 } });
        setJobs(res.data.jobs || []);
        setTotalPages(res.data.total_pages || 1);
        setTotalJobs(res.data.total || 0);
      } else {
        const params = {
          page,
          limit: 20,
          q: debouncedSearch || undefined,
          company: selectedCompany || undefined,
          job_type: selectedJobType || undefined,
          remote: isRemoteOnly ? true : undefined,
        };
        const res = await api.get("/jobs/search", { params });
        setJobs(res.data.jobs || []);
        setTotalPages(res.data.total_pages || 1);
        setTotalJobs(res.data.total || 0);
      }
    } catch (err) {
      console.error("Jobs load error:", err);
      toast.error(err.response?.data?.detail || "Failed to load active jobs");
    } finally {
      setLoading(false);
    }
  }, [page, debouncedSearch, selectedCompany, selectedJobType, isRemoteOnly, isRecommendedMode]);

  // Fetch Applications
  const fetchApplications = async () => {
    try {
      const res = await api.get("/applications/mine");
      setApplications(res.data || []);
    } catch (err) {
      console.error("Applications load error:", err);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  useEffect(() => {
    fetchApplications();
  }, []);

  const appliedJobIds = new Set(applications.map((a) => a.job?.id));

  const handleApply = async (jobId) => {
    setApplyingId(jobId);
    try {
      const res = await api.post(`/applications/${jobId}/apply`);
      toast.success(`Applied! AI match score: ${res.data.match_details?.score || 85}%`);
      await fetchApplications();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to submit application");
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50/60 pb-16">
      <Navbar />
      <PageTransition>
        <div className="max-w-6xl mx-auto p-4 sm:p-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Student Placement Portal</h1>
              <p className="text-sm text-gray-500 mt-0.5">Explore active company opportunities, track applications, and optimize your resume.</p>
            </div>
            <Link to="/profile" className="self-start sm:self-auto flex items-center gap-1.5 px-3.5 py-2 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-brand-600 hover:bg-brand-50 transition-colors shadow-sm">
              <UserCircle size={18} /> Edit Student Profile
            </Link>
          </div>

          {/* Top Banners */}
          <div className="grid md:grid-cols-2 gap-4 mb-8">
            <FeatureBanner
              to="/resume-analyzer" icon={FileText}
              title="AI Resume Analyzer"
              desc="Get instant ATS compliance score, keyword gap analysis, and section tips."
              gradient="from-brand-600 to-indigo-600"
            />
            <FeatureBanner
              to="/mock-interview" icon={MessageSquareText}
              title="Voice AI Mock Interview"
              desc="Practice role-specific technical questions with real-time speech evaluation."
              gradient="from-indigo-600 to-purple-600"
            />
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center justify-between border-b border-gray-200 mb-6">
            <div className="flex gap-2">
              {[
                { key: "jobs", label: `Active Opportunities (${totalJobs})` },
                { key: "applications", label: `My Applications (${applications.length})` },
              ].map((t) => (
                <button
                  key={t.key} onClick={() => setTab(t.key)}
                  className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition ${
                    tab === t.key ? "border-brand-600 text-brand-600" : "border-transparent text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {tab === "jobs" && (
              <button
                onClick={() => {
                  setIsRecommendedMode(!isRecommendedMode);
                  setPage(1);
                }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition ${
                  isRecommendedMode
                    ? "bg-brand-600 text-white shadow-sm"
                    : "bg-brand-50 text-brand-700 border border-brand-200 hover:bg-brand-100"
                }`}
              >
                <Sparkles size={14} /> {isRecommendedMode ? "Showing Tailored Matches" : "AI Recommended For You"}
              </button>
            )}
          </div>

          {/* JOBS TAB */}
          {tab === "jobs" && (
            <div>
              {/* Search & Filter Toolbar */}
              <div className="bg-white border border-gray-200/80 rounded-2xl p-4 shadow-sm mb-6 space-y-3">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1">
                    <Search className="absolute left-3.5 top-3 text-gray-400" size={18} />
                    <input
                      type="text"
                      placeholder="Search by job title, skill (e.g. React, Python), or location..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {/* Company Filter */}
                    <select
                      value={selectedCompany}
                      onChange={(e) => { setSelectedCompany(e.target.value); setPage(1); }}
                      className="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">All Companies ({companies.length})</option>
                      {companies.map((c) => (
                        <option key={c.company} value={c.company}>
                          {c.company} ({c.active_jobs})
                        </option>
                      ))}
                    </select>

                    {/* Job Type Filter */}
                    <select
                      value={selectedJobType}
                      onChange={(e) => { setSelectedJobType(e.target.value); setPage(1); }}
                      className="px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">All Job Types</option>
                      <option value="Full-Time">Full-Time</option>
                      <option value="Internship">Internship</option>
                      <option value="Contract">Contract</option>
                    </select>

                    {/* Remote Toggle */}
                    <label className="flex items-center gap-2 px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-700 cursor-pointer hover:bg-gray-100 transition">
                      <input
                        type="checkbox"
                        checked={isRemoteOnly}
                        onChange={(e) => { setIsRemoteOnly(e.target.checked); setPage(1); }}
                        className="rounded text-brand-600 focus:ring-brand-500"
                      />
                      <span>Remote Only</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Job Card Grid / Skeletons */}
              {loading ? (
                <div className="grid md:grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map((n) => (
                    <div key={n} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm animate-pulse space-y-4">
                      <div className="h-5 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-100 rounded w-1/2"></div>
                      <div className="h-12 bg-gray-100 rounded w-full"></div>
                      <div className="h-8 bg-gray-200 rounded w-full"></div>
                    </div>
                  ))}
                </div>
              ) : jobs.length === 0 ? (
                <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center">
                  <div className="w-12 h-12 rounded-full bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-3">
                    <Search size={24} />
                  </div>
                  <h3 className="font-semibold text-gray-900 text-lg">No active jobs found</h3>
                  <p className="text-sm text-gray-500 mt-1">Try clearing your filters or searching with different keywords.</p>
                  <button
                    onClick={() => {
                      setSearchQuery("");
                      setSelectedCompany("");
                      setSelectedJobType("");
                      setIsRemoteOnly(false);
                      setIsRecommendedMode(false);
                    }}
                    className="mt-4 px-4 py-2 bg-brand-600 text-white rounded-xl text-xs font-semibold hover:bg-brand-700 transition"
                  >
                    Reset All Filters
                  </button>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {jobs.map((job, i) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      index={i}
                      actionSlot={
                        appliedJobIds.has(job.id) ? (
                          <span className="w-full inline-flex items-center justify-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 py-2 rounded-xl">
                            ✓ Already Applied
                          </span>
                        ) : (
                          <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => handleApply(job.id)}
                            disabled={applyingId === job.id}
                            className="w-full inline-flex items-center justify-center gap-1.5 bg-gradient-to-r from-brand-600 to-indigo-600 text-white text-xs font-semibold py-2 rounded-xl shadow-sm hover:from-brand-700 hover:to-indigo-700 transition disabled:opacity-50"
                          >
                            {applyingId === job.id ? "Applying..." : "Apply on CareerPilot"}
                          </motion.button>
                        )
                      }
                    />
                  ))}
                </div>
              )}

              {/* Pagination Controls */}
              {!loading && totalPages > 1 && (
                <div className="flex items-center justify-between mt-8 bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
                  <span className="text-xs text-gray-500 font-medium">
                    Showing page <span className="font-semibold text-gray-900">{page}</span> of <span className="font-semibold text-gray-900">{totalPages}</span> ({totalJobs} total jobs)
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 disabled:opacity-40 text-gray-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                    >
                      <ChevronLeft size={16} /> Previous
                    </button>
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page >= totalPages}
                      className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
                    >
                      Next <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* APPLICATIONS TAB */}
          {tab === "applications" && (
            <div className="space-y-3">
              {applications.length === 0 ? (
                <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center">
                  <p className="text-gray-500 text-sm">You haven't submitted any job applications yet.</p>
                  <button onClick={() => setTab("jobs")} className="mt-3 px-4 py-2 bg-brand-600 text-white text-xs font-semibold rounded-xl">
                    Browse Active Opportunities
                  </button>
                </div>
              ) : (
                applications.map((app) => (
                  <motion.div
                    key={app.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                    className="bg-white border border-gray-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm"
                  >
                    <div>
                      <p className="font-bold text-gray-900">{app.job?.title}</p>
                      <p className="text-xs text-brand-600 font-semibold mt-0.5">{app.job?.company}</p>
                      {app.missing_skills?.length > 0 && (
                        <p className="text-xs text-amber-600 mt-1">Suggested skills to learn: {app.missing_skills.join(", ")}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-3 self-start sm:self-auto">
                      <MatchScoreBadge score={app.match_score} />
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                        {app.status}
                      </span>
                    </div>
                  </motion.div>
                ))
              )}
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
        className={`bg-gradient-to-br ${gradient} text-white rounded-2xl p-5 flex items-center justify-between shadow-sm cursor-pointer`}
      >
        <div className="flex items-center gap-4">
          <div className="bg-white/20 rounded-xl p-3">
            <Icon size={24} />
          </div>
          <div>
            <h3 className="font-semibold text-base">{title}</h3>
            <p className="text-xs text-white/80 mt-0.5">{desc}</p>
          </div>
        </div>
        <ArrowRight size={20} className="shrink-0" />
      </motion.div>
    </Link>
  );
}
