import React, { useId } from 'react';
import { ChevronDown } from 'lucide-react';

/**
 * InfoCapsule — reusable collapsible pill-shaped button.
 *
 * Props:
 *   label       — string shown on the button
 *   isOpen      — boolean (controlled)
 *   onToggle    — () => void
 *   children    — content revealed when open
 *   className   — extra classes on the wrapper
 */
export default function InfoCapsule({ label, isOpen, onToggle, children, className = '' }) {
  const id = useId();
  const contentId = `capsule-content-${id}`;
  const buttonId  = `capsule-btn-${id}`;

  return (
    <div className={`inline-flex flex-col items-start ${className}`}>
      {/* Pill button */}
      <button
        id={buttonId}
        aria-expanded={isOpen}
        aria-controls={contentId}
        onClick={onToggle}
        className={`
          btn-tactile
          inline-flex items-center gap-2
          px-3.5 py-1.5 rounded-full
          border text-xs font-mono tracking-wide
          transition-colors duration-150
          focus-visible:ring-2 focus-visible:ring-[#4FD6C4] focus-visible:outline-none
          ${isOpen
            ? 'bg-[#4FD6C4]/10 border-[#4FD6C4]/70 text-[#4FD6C4]'
            : 'bg-[#1C2029] border-[#2A2F3A] text-[#8B93A3] hover:border-[#4FD6C4]/50 hover:text-[#E7E9EC]'
          }
        `}
      >
        <span>{label}</span>
        <ChevronDown
          className={`w-3 h-3 shrink-0 transition-transform duration-200 capsule-chevron ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Expandable content panel */}
      <div
        id={contentId}
        role="region"
        aria-labelledby={buttonId}
        className={`capsule-body ${isOpen ? 'capsule-body--open' : ''}`}
      >
        <div className="capsule-inner pt-3 pb-1 px-0.5 text-xs text-[#8B93A3] font-sans leading-relaxed space-y-1.5 max-w-xs">
          {children}
        </div>
      </div>
    </div>
  );
}
