import React from 'react';

/**
 * ScanBeam - Forensic Lab Signature Animation Element
 * 
 * Renders a high-precision glowing horizontal beam (2-3px, #4FD6C4)
 * that sweeps across the target container.
 * 
 * Features:
 * - Sweeping beam over ~2s loop
 * - Soft blur/glow shadow: box-shadow: 0 0 12px #4FD6C4, 0 0 24px rgba(79, 214, 196, 0.6)
 * - Static scan-line grid overlay (~5% opacity)
 * - Suspicious region bounding box in flagged-accent #E8603C
 * - Full prefers-reduced-motion compatibility
 */
export default function ScanBeam({
  isActive = true,
  showGrid = false,
  showBoundingBox = false,
  bbox = { x: '24%', y: '18%', width: '52%', height: '48%' },
  bboxLabel = 'REGION_FLAGGED // ARTIFACT_SEAM',
  label = null,
  className = '',
}) {
  return (
    <div className={`absolute inset-0 pointer-events-none overflow-hidden select-none z-10 ${className}`}>
      {/* Optional Static Scan-Line Grid Overlay (5% opacity) */}
      {showGrid && (
        <div className="absolute inset-0 static-grid-overlay opacity-60" />
      )}

      {/* Subtle CRT Scanline overlay texture */}
      <div className="absolute inset-0 scanline-overlay opacity-25" />

      {/* Sweeping Beam Line */}
      {isActive && (
        <div className="scan-beam-line animate-sweep">
          {label && (
            <div className="absolute right-3 -top-5 px-1.5 py-0.5 rounded text-[9px] font-mono font-medium tracking-wider bg-[#14171C]/90 text-[#4FD6C4] border border-[#4FD6C4]/40 shadow-sm">
              {label}
            </div>
          )}
        </div>
      )}

      {/* Forensic Flagged Bounding Box Overlay */}
      {showBoundingBox && (
        <div
          className="absolute border-2 border-[#E8603C] rounded-sm transition-all duration-700 animate-fade-in"
          style={{
            left: bbox.x || '25%',
            top: bbox.y || '20%',
            width: bbox.width || '50%',
            height: bbox.height || '45%',
            boxShadow: '0 0 16px rgba(232, 96, 60, 0.3), inset 0 0 12px rgba(232, 96, 60, 0.15)',
          }}
        >
          {/* Corner crosshair notches */}
          <span className="absolute -top-1 -left-1 w-2.5 h-2.5 border-t-2 border-l-2 border-[#E8603C]" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 border-t-2 border-r-2 border-[#E8603C]" />
          <span className="absolute -bottom-1 -left-1 w-2.5 h-2.5 border-b-2 border-l-2 border-[#E8603C]" />
          <span className="absolute -bottom-1 -right-1 w-2.5 h-2.5 border-b-2 border-r-2 border-[#E8603C]" />

          {/* Bounding box label tag */}
          <div className="absolute -top-6 left-0 px-1.5 py-0.5 bg-[#1C2029] text-[#E8603C] text-[9px] font-mono font-semibold uppercase tracking-wider border border-[#E8603C]/50 rounded-xs flex items-center space-x-1 whitespace-nowrap">
            <span className="w-1.5 h-1.5 rounded-full bg-[#E8603C] animate-ping" />
            <span>{bboxLabel}</span>
          </div>
        </div>
      )}

      {/* Corner Forensic Crosshairs */}
      <div className="absolute top-2 left-2 w-3 h-3 border-t border-l border-[#4FD6C4]/30" />
      <div className="absolute top-2 right-2 w-3 h-3 border-t border-r border-[#4FD6C4]/30" />
      <div className="absolute bottom-2 left-2 w-3 h-3 border-b border-l border-[#4FD6C4]/30" />
      <div className="absolute bottom-2 right-2 w-3 h-3 border-b border-r border-[#4FD6C4]/30" />
    </div>
  );
}
