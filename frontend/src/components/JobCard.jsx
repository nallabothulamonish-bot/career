import React from "react";
import { motion } from "framer-motion";
import { Briefcase, MapPin, Calendar } from "lucide-react";

export default function JobCard({ job, actionSlot, index = 0 }) {
  const deadlinePassed = new Date(job.application_deadline) < new Date();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
      whileHover={{ y: -4 }}
      className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg">{job.title}</h3>
          <p className="text-brand-600 text-sm font-medium">{job.company}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${job.status === "open" && !deadlinePassed ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
          {job.status === "open" && !deadlinePassed ? "Open" : "Closed"}
        </span>
      </div>

      <p className="text-sm text-gray-600 mt-3 line-clamp-3">{job.description}</p>

      <div className="flex flex-wrap gap-2 mt-3">
        {job.required_skills?.slice(0, 6).map((skill) => (
          <span key={skill} className="text-xs bg-brand-50 text-brand-700 px-2 py-1 rounded-md">
            {skill}
          </span>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-4 mt-4 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Briefcase size={14} /> {job.job_type}
        </span>
        <span className="flex items-center gap-1">
          <MapPin size={14} /> {job.location}
        </span>
        <span className="flex items-center gap-1">
          <Calendar size={14} /> Deadline: {new Date(job.application_deadline).toLocaleDateString()}
        </span>
        {job.ctc_or_stipend && <span className="font-medium text-gray-700">{job.ctc_or_stipend}</span>}
      </div>

      {actionSlot && <div className="mt-4">{actionSlot}</div>}
    </motion.div>
  );
}
