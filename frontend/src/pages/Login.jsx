import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import toast from "react-hot-toast";
import { Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(form.email, form.password);
      toast.success(`Welcome back, ${user.name}!`);
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed");
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
          <motion.div animate={{ y: [0, -6, 0] }} transition={{ duration: 2.5, repeat: Infinity }}>
            <Sparkles className="text-brand-600" size={40} />
          </motion.div>
          <h1 className="text-xl font-bold mt-2 gradient-text">CareerPilot AI</h1>
          <p className="text-sm text-gray-500">Sign in to continue</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email" required placeholder="Email address"
            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <input
            type="password" required placeholder="Password"
            className="w-full border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
          <motion.button
            whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
            disabled={loading}
            className="w-full bg-gradient-to-r from-brand-600 to-accent-500 text-white rounded-xl py-2.5 font-medium transition disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </motion.button>
        </form>
        <p className="text-sm text-gray-500 text-center mt-5">
          Don't have an account? <Link to="/register" className="text-brand-600 font-medium">Register</Link>
        </p>
        <div className="mt-6 text-xs text-gray-400 border-t pt-4">
          Demo logins (after running the seed script): <br />
          officer@college.edu / arjun@college.edu — password: password123
        </div>
      </motion.div>
    </div>
  );
}
