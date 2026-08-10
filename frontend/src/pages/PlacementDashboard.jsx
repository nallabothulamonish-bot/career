import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { Plus, Users, TrendingUp, Briefcase, Trash2, Target } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import JobForm from "../components/JobForm.jsx";
import PageTransition from "../components/PageTransition.jsx";

export default function PlacementDashboard() {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    const [jobsRes, statsRes] = await Promise.all([
      api.get("/jobs"),
      api.get("/applications/analytics"),
    ]);
    setJobs(jobsRes.data.jobs || (Array.isArray(jobsRes.data) ? jobsRes.data : []));
    setStats(statsRes.data);
  };


  useEffect(() => { load(); }, []);

  const handleDelete = async (id) => {
    if (!confirm("Delete this job drive?")) return;
    try {
      await api.delete(`/jobs/${id}`);
      toast.success("Job deleted");
      load();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to delete");
    }
  };

  const chartData = stats?.status_breakdown?.map((s) => ({ name: s.status, count: s.count })) || [];

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-6xl mx-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-xl font-bold">Placement Officer Dashboard</h1>
            <motion.button
              whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              onClick={() => setShowForm(true)}
              className="flex items-center gap-1.5 bg-gradient-to-r from-brand-600 to-accent-500 text-white text-sm px-4 py-2.5 rounded-xl font-medium"
            >
              <Plus size={16} /> New Drive
            </motion.button>
          </div>

          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <StatCard icon={<Users size={18} />} label="Total Students" value={stats.total_students} delay={0} />
              <StatCard icon={<TrendingUp size={18} />} label="Placement Rate" value={`${stats.placement_rate}%`} delay={0.05} />
              <StatCard icon={<Briefcase size={18} />} label="Open Drives" value={stats.open_jobs} delay={0.1} />
              <StatCard icon={<Target size={18} />} label="Avg AI Match Score" value={`${stats.avg_match_score}%`} delay={0.15} />
            </div>
          )}

          {chartData.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-2xl p-5 mb-8 shadow-sm">
              <h2 className="font-semibold text-sm text-gray-700 mb-4">Applications by Status</h2>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis allowDecimals={false} fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <h2 className="font-semibold mb-3">Job Drives</h2>
          <div className="space-y-3">
            {jobs.map((job, i) => (
              <motion.div
                key={job.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between shadow-sm"
              >
                <div>
                  <p className="font-semibold text-gray-900">{job.title} — <span className="text-brand-600">{job.company}</span></p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {job.status === "open" ? "Open" : "Closed"} · Deadline {new Date(job.application_deadline).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Link to={`/jobs/${job.id}/applicants`} className="text-sm text-brand-600 font-medium">
                    View Applicants
                  </Link>
                  <button onClick={() => handleDelete(job.id)} className="text-gray-400 hover:text-red-600">
                    <Trash2 size={16} />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </PageTransition>

      {showForm && (
        <JobForm onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); load(); }} />
      )}
    </div>
  );
}

function StatCard({ icon, label, value, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay }}
      className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm"
    >
      <div className="flex items-center gap-2 text-brand-600 mb-2">{icon}</div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </motion.div>
  );
}
