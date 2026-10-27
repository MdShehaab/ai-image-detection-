import React from 'react';

/**
 * VisualGauge - Precision Forensic Instrument Readout
 * 
 * Props:
 *   score        — final confidence percentage (0-100), for geometry calculation
 *   displayScore — animated counter value passed from parent (0 → score over ~800ms)
 *   verdict      — 'FAKE' | 'AI_MODIFIED' | 'AI_GENERATED' | 'SUSPICIOUS' | 'REAL'
 *   size         — SVG width/height in px (default 180)
 *   animate      — when true, ring draws from 0 to target; when false, ring stays at 0
 */
export default function VisualGauge({ score = 0, displayScore, verdict = 'FAKE', size = 180, animate = true, label = 'CONFIDENCE' }) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;

  // When not yet animating, keep ring fully hidden (dashoffset = circumference = 0%)
  // When animating, transition to the real dashoffset over 800ms
  const strokeDashoffset = animate
    ? circumference - (score / 100) * circumference
    : circumference;

  const isFake = verdict === 'FAKE' || verdict === 'AI_MODIFIED' || verdict === 'AI_GENERATED';
  const isSuspicious = verdict === 'SUSPICIOUS';

  const strokeColor = isFake
    ? '#E8603C' // Flagged accent
    : isSuspicious
    ? '#F2C94C' // Warning amber
    : '#6FCF97'; // Verified real accent

  // Number shown in center: use displayScore (count-up) if provided, else static score
  const shownNumber = displayScore !== undefined ? displayScore : score;

  return (
    <div className="relative flex flex-col items-center justify-center select-none">
      <svg
        width={size}
        height={size}
        viewBox="0 0 160 160"
        className="transform -rotate-90"
      >
        {/* Instrument Ticks and Outer Ring */}
        <circle
          cx="80"
          cy="80"
          r={radius + 8}
          stroke="#2A2F3A"
          strokeWidth="1"
          strokeDasharray="2 6"
          fill="transparent"
        />

        {/* Background Track */}
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke="#2A2F3A"
          strokeWidth="8"
          fill="transparent"
        />

        {/* Dynamic Telemetry Arc — draws itself when animate flips true */}
        <circle
          cx="80"
          cy="80"
          r={radius}
          stroke={strokeColor}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0px 0px 6px ${strokeColor}66)`,
            transition: animate
              ? 'stroke-dashoffset 800ms cubic-bezier(0.22, 1, 0.36, 1)'
              : 'none',
          }}
        />
      </svg>

      {/* Center Instrument Monospace Readout */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-3xl font-mono font-bold tracking-tight text-[#E7E9EC] tabular-nums">
          {shownNumber}%
        </span>
        <span className="text-[9px] font-mono uppercase tracking-widest text-[#8B93A3] mt-0.5">
          {label}
        </span>
      </div>
    </div>
  );
}
