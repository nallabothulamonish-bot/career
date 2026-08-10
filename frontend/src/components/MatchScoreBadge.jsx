import React from "react";
import { motion } from "framer-motion";

export default function MatchScoreBadge({ score }) {
  let color = "bg-gray-100 text-gray-600";
  if (score >= 75) color = "bg-green-100 text-green-700";
  else if (score >= 50) color = "bg-amber-100 text-amber-700";
  else if (score > 0) color = "bg-red-100 text-red-700";

  return (
    <motion.span
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`px-2.5 py-1 rounded-full text-xs font-semibold ${color}`}
    >
      {score}% match
    </motion.span>
  );
}
