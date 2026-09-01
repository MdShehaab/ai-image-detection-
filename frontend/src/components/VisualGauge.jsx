import React from 'react';

/**
 * VisualGauge - Precision Forensic Instrument Readout
 * Restyled with JetBrains Mono numbers, disciplined colors (#6FCF97 / #E8603C),
 * and clean telemetry markers.
 */
export default function VisualGauge({ score = 0, verdict = 'FAKE', size = 180 }) {
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const isFake = verdict === 'FAKE' || verdict === 'AI_MODIFIED' || verdict === 'AI_GENERATED';
  const isSuspicious = verdict === 'SUSPICIOUS';

  const strokeColor = isFake
    ? '#E8603C' // Flagged accent
    : isSuspicious
    ? '#F2C94C' // Warning amber
    : '#6FCF97'; // Verified real accent

  return (
    <div className="relative flex flex-col items-center justify-center select-none">
      <svg
        width={size}
        height={size}
        viewBox="0 0 160 160"
        className="transform -rotate-90 transition-all duration-1000 ease-out"
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

        {/* Dynamic Telemetry Arc */}
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
            transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
      </svg>

      {/* Center Instrument Monospace Readout */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-3xl font-mono font-bold tracking-tight text-[#E7E9EC]">
          {score}%
        </span>
        <span className="text-[9px] font-mono uppercase tracking-widest text-[#8B93A3] mt-0.5">
          CONFIDENCE
        </span>
      </div>
    </div>
  );
}
