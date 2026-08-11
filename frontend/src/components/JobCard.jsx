import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Briefcase, MapPin, ExternalLink, Sparkles, CheckCircle2, Globe, Building2, ChevronDown, ChevronUp } from "lucide-react";

export default function JobCard({ job, actionSlot, index = 0 }) {
  const [showReasons, setShowReasons] = useState(false);

  const getSourceBadge = () => {
    const src = (job.source || "manual").toLowerCase();
    if (src === "greenhouse") {
      return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200/60 flex items-center gap-1"><Globe size={11} /> Official Greenhouse</span>;
    }
    if (src === "lever") {
      return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/60 flex items-center gap-1"><Globe size={11} /> Official Lever</span>;
    }
    return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200/60 flex items-center gap-1"><Building2 size={11} /> Campus Drive</span>;
  };

  const getMatchScoreBadge = () => {
    if (job.match_score == null) return null;
    const score = Math.round(job.match_score);
    let colorClass = "bg-emerald-500 text-white shadow-emerald-200";
    if (score < 60) colorClass = "bg-amber-500 text-white shadow-amber-200";
    if (score < 45) colorClass = "bg-gray-500 text-white shadow-gray-200";

    return (
      <div className="relative">
        <button
          onClick={() => setShowReasons(!showReasons)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold shadow-sm transition-all hover:scale-105 ${colorClass}`}
          title="Click to view match analysis"
        >
          <Sparkles size={13} /> {score}% Match
          {job.match_reasons?.length > 0 && (
            showReasons ? <ChevronUp size={12} /> : <ChevronDown size={12} />
          )}
        </button>
      </div>
    );
  };

  const skillsList = job.skills?.length > 0 ? job.skills : (job.required_skills || []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      whileHover={{ y: -3 }}
      className="bg-white border border-gray-200/80 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between relative overflow-hidden"
    >
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-brand-500 to-indigo-600 text-white font-bold text-lg flex items-center justify-center shadow-sm shrink-0">
              {job.company?.[0]?.toUpperCase() || "C"}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-gray-900 text-[15px]">{job.company}</span>
                {getSourceBadge()}
              </div>
              <h3 className="font-bold text-gray-900 text-base mt-0.5 leading-snug">{job.title}</h3>
            </div>
          </div>
          {getMatchScoreBadge()}
        </div>

        {/* Expandable Match Reasons */}
        <AnimatePresence>
          {showReasons && job.match_reasons?.length > 0 && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-3 bg-brand-50/60 border border-brand-100 rounded-xl p-3 text-xs text-brand-900 overflow-hidden"
            >
              <div className="font-semibold flex items-center gap-1 text-brand-700 mb-1.5">
                <Sparkles size={13} /> Why you match this role:
              </div>
              <ul className="space-y-1">
                {job.match_reasons.map((reason, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <CheckCircle2 size={13} className="text-brand-600 mt-0.5 shrink-0" />
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Description */}
        <p className="text-sm text-gray-600 mt-3 line-clamp-3 leading-relaxed">{job.description}</p>

        {/* Skills Pills */}
        {skillsList.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3">
            {skillsList.slice(0, 6).map((skill) => (
              <span key={skill} className="text-[11px] font-medium bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full border border-gray-200/60">
                {skill}
              </span>
            ))}
            {skillsList.length > 6 && (
              <span className="text-[11px] font-medium text-gray-400 self-center">+{skillsList.length - 6} more</span>
            )}
          </div>
        )}
      </div>

      {/* Meta Info & Footer Action Buttons */}
      <div className="mt-4 pt-3 border-t border-gray-100">
        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 mb-3">
          <span className="flex items-center gap-1 font-medium text-gray-700">
            <Briefcase size={13} className="text-brand-500" /> {job.job_type || "Full-Time"}
          </span>
          <span className="flex items-center gap-1">
            <MapPin size={13} className="text-gray-400" /> {job.location || "Remote"}
          </span>
          {job.is_remote && (
            <span className="bg-emerald-50 text-emerald-700 font-semibold px-2 py-0.5 rounded text-[10px] uppercase">
              Remote
            </span>
          )}
          {job.ctc_or_stipend && (
            <span className="font-semibold text-brand-700 bg-brand-50 px-2 py-0.5 rounded">
              {job.ctc_or_stipend}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {job.application_url && (
            <a
              href={job.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
            >
              Apply on Official Site <ExternalLink size={13} />
            </a>
          )}
          {actionSlot && <div className="flex-1">{actionSlot}</div>}
        </div>
      </div>
    </motion.div>
  );
}
