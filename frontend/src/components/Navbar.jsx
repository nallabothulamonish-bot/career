import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, LogOut, FileText, MessageSquareText, LayoutDashboard, BookOpen } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const studentLinks = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard },
    { to: "/resume-analyzer", label: "Resume Analyzer", icon: FileText },
    { to: "/mock-interview", label: "Mock Interview", icon: MessageSquareText },
    { to: "/assessments", label: "Placement Tests", icon: BookOpen },
  ];


  return (
    <nav className="glass border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-40">
      <Link to="/" className="flex items-center gap-2 font-extrabold text-lg">
        <motion.div
          animate={{ rotate: [0, 15, -15, 0] }}
          transition={{ duration: 3, repeat: Infinity, repeatDelay: 4 }}
        >
          <Sparkles className="text-brand-600" size={24} />
        </motion.div>
        <span className="gradient-text">CareerPilot AI</span>
      </Link>

      {user?.role === "student" && (
        <div className="hidden md:flex items-center gap-1">
          {studentLinks.map((l) => {
            const active = location.pathname === l.to;
            const Icon = l.icon;
            return (
              <Link
                key={l.to}
                to={l.to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  active ? "bg-brand-50 text-brand-700" : "text-gray-500 hover:text-brand-600"
                }`}
              >
                <Icon size={16} /> {l.label}
              </Link>
            );
          })}
        </div>
      )}

      {user && (
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600 hidden sm:inline">
            {user.name} <span className="text-xs text-gray-400">({user.role.replace("_", " ")})</span>
          </span>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-600 transition"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      )}
    </nav>
  );
}
