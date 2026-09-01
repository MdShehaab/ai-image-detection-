import React, { useState, useEffect } from 'react';
import { Shield, Activity, Terminal, Sparkles, Cpu } from 'lucide-react';
import { checkBackendHealth } from '../services/api';

export default function Navbar({ activeTab, setActiveTab, onResetToHome }) {
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await checkBackendHealth();
        setBackendStatus(res.status === 'healthy' ? 'online' : 'mock');
      } catch {
        setBackendStatus('offline');
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#14171C]/95 backdrop-blur-md border-b border-[#2A2F3A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Forensic Lab Identity */}
          <div 
            onClick={onResetToHome}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onResetToHome()}
            className="flex items-center space-x-3 cursor-pointer group focus-visible:outline-none"
          >
            <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-[#1C2029] border border-[#2A2F3A] group-hover:border-[#4FD6C4]/60 transition-colors">
              <Shield className="w-5 h-5 text-[#4FD6C4] transition-transform group-hover:scale-105" />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#4FD6C4] animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-display font-bold text-base tracking-tight text-[#E7E9EC]">
                  VERITAS
                </span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-[#1C2029] text-[#4FD6C4] border border-[#2A2F3A]">
                  LAB_v2.0
                </span>
              </div>
              <p className="text-[10px] font-mono text-[#8B93A3] hidden sm:block tracking-wide uppercase">
                Digital Forensic Verification Lab
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('landing')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
                activeTab === 'landing'
                  ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4]/40 font-semibold shadow-xs'
                  : 'text-[#8B93A3] hover:text-[#E7E9EC] hover:bg-[#1C2029]/60'
              }`}
            >
              01 // LAB_OVERVIEW
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
                activeTab === 'upload' || activeTab === 'results'
                  ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4] font-semibold shadow-xs'
                  : 'text-[#8B93A3] hover:text-[#E7E9EC] hover:bg-[#1C2029]/60'
              }`}
            >
              02 // SCAN_TERMINAL
            </button>
          </nav>

          {/* Engine Telemetry Status */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-[#1C2029] border border-[#2A2F3A] text-xs">
              <span className={`w-2 h-2 rounded-full ${
                backendStatus === 'online' ? 'bg-[#6FCF97] animate-pulse' :
                backendStatus === 'mock' ? 'bg-amber-400' : 'bg-[#E8603C]'
              }`} />
              <span className="text-[#8B93A3] font-mono text-[10px] uppercase tracking-wider hidden md:inline">
                {backendStatus === 'online' ? 'INFERENCE: ONLINE' :
                 backendStatus === 'mock' ? 'INFERENCE: LOCAL_MOCK' : 'INFERENCE: DISCONNECTED'}
              </span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
}
