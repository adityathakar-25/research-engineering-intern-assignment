"use client";

import React from "react";
import { Sparkles } from "lucide-react";

export default function AISummary({ text }: { text?: string }) {
  if (!text) return null;

  return (
    <div
      className="mt-5 p-4 rounded-xl border-l-[3px]"
      style={{
        background: "linear-gradient(135deg, #EFF6FF, #F0FDF4)",
        borderLeftColor: "#3B82F6",
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="w-3.5 h-3.5 text-blue-500" />
        <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
          AI Insight
        </span>
      </div>
      <p className="text-sm text-gray-700 italic leading-relaxed">{text}</p>
    </div>
  );
}
