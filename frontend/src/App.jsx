import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import StudentDashboard from "./pages/StudentDashboard.jsx";
import PlacementDashboard from "./pages/PlacementDashboard.jsx";
import Profile from "./pages/Profile.jsx";
import ApplicantsPage from "./pages/ApplicantsPage.jsx";
import ResumeAnalyzer from "./pages/ResumeAnalyzer.jsx";
import MockInterview from "./pages/MockInterview.jsx";
import Assessments from "./pages/Assessments.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { useAuth } from "./context/AuthContext.jsx";

function Home() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return user.role === "student" ? <StudentDashboard /> : <PlacementDashboard />;
}

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute allowedRoles={["student"]}><Profile /></ProtectedRoute>} />
        <Route path="/resume-analyzer" element={<ProtectedRoute allowedRoles={["student"]}><ResumeAnalyzer /></ProtectedRoute>} />
        <Route path="/mock-interview" element={<ProtectedRoute allowedRoles={["student"]}><MockInterview /></ProtectedRoute>} />
        <Route path="/assessments" element={<ProtectedRoute allowedRoles={["student"]}><Assessments /></ProtectedRoute>} />
        <Route path="/jobs/:jobId/applicants" element={<ProtectedRoute allowedRoles={["placement_officer"]}><ApplicantsPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}

