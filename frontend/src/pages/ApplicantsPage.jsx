import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { ArrowLeft } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import MatchScoreBadge from "../components/MatchScoreBadge.jsx";
import PageTransition from "../components/PageTransition.jsx";

const STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"];

export default function ApplicantsPage() {
  const { jobId } = useParams();
  const [applicants, setApplicants] = useState([]);
  const [job, setJob] = useState(null);

  const load = async () => {
    const [appsRes, jobRes] = await Promise.all([
      api.get(`/applications/job/${jobId}`),
      api.get(`/jobs/${jobId}`),
    ]);
    setApplicants(appsRes.data);
    setJob(jobRes.data);
  };

  useEffect(() => { load(); }, [jobId]);

  const updateStatus = async (appId, status) => {
    try {
      await api.put(`/applications/${appId}/status`, { status });
      toast.success(`Marked as ${status}`);
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to update");
    }
  };

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-4xl mx-auto p-6">
          <Link to="/" className="flex items-center gap-1 text-sm text-gray-500 mb-4">
            <ArrowLeft size={16} /> Back to dashboard
          </Link>
          <h1 className="text-xl font-bold mb-1">Applicants {job && `— ${job.title} @ ${job.company}`}</h1>
          <p className="text-sm text-gray-500 mb-6">Sorted by AI match score (highest first).</p>

          <div className="space-y-3">
            {applicants.length === 0 && <p className="text-gray-400 text-sm">No applicants yet.</p>}
            {applicants.map((app, i) => (
              <motion.div
                key={app.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{app.student?.name}</p>
                    <p className="text-sm text-gray-500">{app.student?.email}</p>
                    {app.matched_skills?.length > 0 && (
                      <p className="text-xs text-green-600 mt-1">Matched: {app.matched_skills.join(", ")}</p>
                    )}
                    {app.missing_skills?.length > 0 && (
                      <p className="text-xs text-amber-600">Missing: {app.missing_skills.join(", ")}</p>
                    )}
                  </div>
                  <MatchScoreBadge score={app.match_score} />
                </div>
                <div className="flex gap-2 mt-3 flex-wrap">
                  {STATUSES.map((s) => (
                    <button
                      key={s} onClick={() => updateStatus(app.id, s)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition ${
                        app.status === s ? "bg-brand-600 text-white border-brand-600" : "bg-white text-gray-600 border-gray-200 hover:border-brand-400"
                      }`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </PageTransition>
    </div>
  );
}
