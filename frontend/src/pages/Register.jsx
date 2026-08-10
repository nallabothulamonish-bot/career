import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "student" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await register(form);
      toast.success(`Account created! Welcome, ${user.name}`);
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 via-white to-accent-400/10 bg-200 animate-gradient px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-white/90 glass shadow-2xl rounded-3xl p-8 w-full max-w-md border border-gray-100"
      >
        <div className="flex flex-col items-center mb-6">
          <Sparkles className="text-brand-600" size={40} />
          <h1 className="text-xl font-bold mt-2">Create your account</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input required placeholder="Full name" className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input type="email" required placeholder="Email address" className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input type="password" required minLength={6} placeholder="Password (min 6 chars)" className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <div className="flex gap-3">
            {["student", "placement_officer"].map((r) => (
              <button
                type="button" key={r} onClick={() => setForm({ ...form, role: r })}
                className={`flex-1 py-2.5 rounded-xl text-sm font-medium border transition ${
                  form.role === r ? "bg-brand-600 text-white border-brand-600" : "bg-white text-gray-600 border-gray-200"
                }`}
              >
                {r === "student" ? "Student" : "Placement Officer"}
              </button>
            ))}
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            disabled={loading}
            className="w-full bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl py-2.5 font-medium transition disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create account"}
          </motion.button>
        </form>
        <p className="text-sm text-gray-500 text-center mt-5">
          Already have an account? <Link to="/login" className="text-brand-600 font-medium">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}
