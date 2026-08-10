import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Save } from "lucide-react";
import api from "../api/axios.js";
import Navbar from "../components/Navbar.jsx";
import PageTransition from "../components/PageTransition.jsx";

export default function Profile() {
  const [form, setForm] = useState({
    roll_number: "", branch: "", cgpa: "", graduation_year: "", phone: "", skills: "", resume_text: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/students/me").then((res) => {
      const p = res.data;
      setForm({
        roll_number: p.roll_number || "",
        branch: p.branch || "",
        cgpa: p.cgpa || "",
        graduation_year: p.graduation_year || "",
        phone: p.phone || "",
        skills: (p.skills || []).join(", "),
        resume_text: p.resume_text || "",
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put("/students/me", {
        ...form,
        cgpa: Number(form.cgpa) || 0,
        graduation_year: Number(form.graduation_year) || undefined,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      });
      toast.success("Profile updated! Your match scores will now be more accurate.");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-10 text-center text-gray-400">Loading profile...</div>;

  return (
    <div>
      <Navbar />
      <PageTransition>
        <div className="max-w-2xl mx-auto p-6">
          <h1 className="text-xl font-bold mb-1">My Profile</h1>
          <p className="text-sm text-gray-500 mb-6">
            This information (especially Skills and Resume text) powers the AI job-matching, resume analyzer, and mock interview engines.
          </p>
          <form onSubmit={handleSave} className="bg-white border border-gray-200 rounded-2xl p-6 space-y-4 shadow-sm">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Roll Number" value={form.roll_number} onChange={(v) => setForm({ ...form, roll_number: v })} />
              <Field label="Branch" value={form.branch} onChange={(v) => setForm({ ...form, branch: v })} placeholder="e.g. Computer Science" />
              <Field label="CGPA" type="number" value={form.cgpa} onChange={(v) => setForm({ ...form, cgpa: v })} />
              <Field label="Graduation Year" type="number" value={form.graduation_year} onChange={(v) => setForm({ ...form, graduation_year: v })} />
              <div className="col-span-2">
                <Field label="Phone" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
              </div>
            </div>

            <div>
              <label className="text-xs text-gray-500">Skills (comma separated)</label>
              <input
                className="w-full border rounded-xl px-3 py-2 mt-1"
                placeholder="javascript, react, node.js, sql"
                value={form.skills}
                onChange={(e) => setForm({ ...form, skills: e.target.value })}
              />
            </div>

            <div>
              <label className="text-xs text-gray-500">Resume Text (paste your resume content)</label>
              <textarea
                rows={8}
                className="w-full border rounded-xl px-3 py-2 mt-1"
                placeholder="Paste the text content of your resume here — used by the AI matcher, resume analyzer, and interview engine."
                value={form.resume_text}
                onChange={(e) => setForm({ ...form, resume_text: e.target.value })}
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
              disabled={saving}
              className="flex items-center gap-2 bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl px-4 py-2.5 font-medium transition disabled:opacity-50"
            >
              <Save size={16} /> {saving ? "Saving..." : "Save Profile"}
            </motion.button>
          </form>
        </div>
      </PageTransition>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", placeholder = "" }) {
  return (
    <div>
      <label className="text-xs text-gray-500">{label}</label>
      <input
        type={type}
        className="w-full border rounded-xl px-3 py-2 mt-1"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
