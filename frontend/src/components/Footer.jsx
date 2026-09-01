import React from 'react';
import { Shield, Terminal, Cpu, Lock, CheckCircle2 } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-[#2A2F3A] bg-[#14171C] text-[#8B93A3] py-8 mt-auto font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Brand Col */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-[#4FD6C4]" />
              <span className="font-display font-bold text-[#E7E9EC] text-sm tracking-tight">
                VERITAS LAB
              </span>
            </div>
            <p className="text-xs text-[#8B93A3] leading-relaxed">
              Forensic intelligence and media integrity validation engine defending against deepfake synthesis and AI document manipulation.
            </p>
          </div>

          {/* Module Specs */}
          <div>
            <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#E7E9EC] mb-3">
              Forensic Engines
            </h4>
            <ul className="space-y-1.5 text-xs font-mono">
              <li className="text-[#8B93A3] hover:text-[#4FD6C4] transition-colors">
                MODULE_01 // Image Authenticity
              </li>
              <li className="text-[#8B93A3] hover:text-[#4FD6C4] transition-colors">
                MODULE_02 // Video Temporal
              </li>
              <li className="text-[#8B93A3] hover:text-[#4FD6C4] transition-colors">
                MODULE_03 // Document Forgery
              </li>
            </ul>
          </div>

          {/* Architecture */}
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

          {/* Telemetry Status */}
          <div>
            <h4 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#E7E9EC] mb-3">
              Service Registry
            </h4>
            <div className="p-3 rounded-lg bg-[#1C2029] border border-[#2A2F3A] space-y-1.5 font-mono text-[11px]">
              <div className="flex items-center justify-between">
                <span className="text-[#8B93A3]">IMAGE_DETECTOR</span>
                <span className="text-[#6FCF97] flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> READY
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#8B93A3]">VIDEO_ENGINE</span>
                <span className="text-[#6FCF97] flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> READY
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[#8B93A3]">DOCUMENT_OCR</span>
                <span className="text-[#6FCF97] flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> READY
                </span>
              </div>
            </div>
          </div>

        </div>

        <div className="pt-6 border-t border-[#2A2F3A] flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-[#8B93A3]">
          <p>© 2026 VERITAS FORENSIC RESEARCH LAB. ALL RIGHTS RESERVED.</p>
          <p className="mt-2 sm:mt-0 text-[#4FD6C4]">STANDARDIZED PROTOCOL // ISO_IEC_27037</p>
        </div>
      </div>
    </footer>
  );
}
