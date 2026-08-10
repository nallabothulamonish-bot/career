import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import toast from "react-hot-toast";
import { X } from "lucide-react";
import api from "../api/axios.js";

export default function JobForm({ onClose, onCreated }) {
  const [form, setForm] = useState({
    title: "", company: "", description: "", required_skills: "", job_type: "Full-Time",
    location: "On-Campus", ctc_or_stipend: "", min_cgpa: "", eligible_branches: "", application_deadline: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/jobs", {
        ...form,
        min_cgpa: Number(form.min_cgpa) || 0,
        required_skills: form.required_skills.split(",").map((s) => s.trim()).filter(Boolean),
        eligible_branches: form.eligible_branches.split(",").map((s) => s.trim()).filter(Boolean),
        application_deadline: new Date(form.application_deadline).toISOString(),
      });
      toast.success("Job drive created");
      onCreated();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create job");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 relative"
        >
          <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-700">
            <X size={20} />
          </button>
          <h2 className="font-bold text-lg mb-4">Create New Job Drive</h2>
          <form onSubmit={handleSubmit} className="space-y-3">
            <input required placeholder="Job title" className="w-full border rounded-xl px-3 py-2"
              value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            <input required placeholder="Company name" className="w-full border rounded-xl px-3 py-2"
              value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <textarea required rows={4} placeholder="Job description (used for AI matching)" className="w-full border rounded-xl px-3 py-2"
              value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <input placeholder="Required skills (comma separated)" className="w-full border rounded-xl px-3 py-2"
              value={form.required_skills} onChange={(e) => setForm({ ...form, required_skills: e.target.value })} />
            <div className="grid grid-cols-2 gap-3">
              <select className="border rounded-xl px-3 py-2" value={form.job_type}
                onChange={(e) => setForm({ ...form, job_type: e.target.value })}>
                <option>Full-Time</option>
                <option>Internship</option>
                <option>Internship+PPO</option>
              </select>
              <input placeholder="CTC / Stipend" className="border rounded-xl px-3 py-2"
                value={form.ctc_or_stipend} onChange={(e) => setForm({ ...form, ctc_or_stipend: e.target.value })} />
              <input type="number" step="0.1" placeholder="Min CGPA" className="border rounded-xl px-3 py-2"
                value={form.min_cgpa} onChange={(e) => setForm({ ...form, min_cgpa: e.target.value })} />
              <input type="date" required className="border rounded-xl px-3 py-2"
                value={form.application_deadline} onChange={(e) => setForm({ ...form, application_deadline: e.target.value })} />
            </div>
            <input placeholder="Eligible branches (comma separated, blank = all)" className="w-full border rounded-xl px-3 py-2"
              value={form.eligible_branches} onChange={(e) => setForm({ ...form, eligible_branches: e.target.value })} />
            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              disabled={saving}
              className="w-full bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl py-2.5 font-medium disabled:opacity-50"
            >
              {saving ? "Creating..." : "Create Drive"}
            </motion.button>
          </form>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
