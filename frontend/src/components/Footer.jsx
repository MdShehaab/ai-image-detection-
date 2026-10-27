import React from 'react';
import { Shield, Terminal, Cpu, Lock } from 'lucide-react';

export default function Footer({ onNavigateToTransparency }) {
  return (
    <footer className="border-t border-[#2A2F3A] bg-[#14171C] text-[#8B93A3] py-8 mt-auto font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">

          {/* Brand */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-[#4FD6C4]" />
              <span className="font-display font-bold text-[#E7E9EC] text-sm tracking-tight">
                VERITAS LAB
              </span>
            </div>
            <p className="text-xs text-[#8B93A3] leading-relaxed">
              Image authenticity forensics — statistical detection of AI-generated and AI-modified images.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#E7E9EC] mb-3">
              Navigation
            </h4>
            <ul className="space-y-1.5 text-xs font-mono">
              <li>
                <button
                  onClick={onNavigateToTransparency}
                  className="text-[#8B93A3] hover:text-[#4FD6C4] transition-colors text-left"
                >
                  Model Insights
                </button>
              </li>
              <li>
                <button
                  onClick={onNavigateToTransparency}
                  className="text-[#4FD6C4] hover:underline transition-colors flex items-center gap-1 text-[11px]"
                >
                  → Accuracy & confusion matrix
                </button>
              </li>
            </ul>
          </div>

          {/* Infrastructure */}
          <div>
            <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#E7E9EC] mb-3">
              Infrastructure
            </h4>
            <ul className="space-y-1.5 text-xs font-mono text-[#8B93A3]">
              <li className="flex items-center space-x-1.5">
                <Terminal className="w-3 h-3 text-[#4FD6C4]" />
                <span>Flask REST Service (Python 3.11)</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <Cpu className="w-3 h-3 text-[#4FD6C4]" />
                <span>EfficientNetB0 + MediaPipe</span>
              </li>
              <li className="flex items-center space-x-1.5">
                <Lock className="w-3 h-3 text-[#4FD6C4]" />
                <span>Memory-Only Volatile Buffer</span>
              </li>
            </ul>
          </div>

        </div>

        <div className="pt-6 border-t border-[#2A2F3A] flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-[#8B93A3]">
          <p>© 2026 VERITAS FORENSIC RESEARCH LAB. ALL RIGHTS RESERVED.</p>
          <p className="mt-2 sm:mt-0 text-[#4FD6C4]">IMAGE AUTHENTICITY FORENSICS // EfficientNetB0</p>
        </div>
      </div>
    </footer>
  );
}
