import React, { useState, useEffect, useRef, useLayoutEffect } from 'react';
import { Shield, Terminal, BookMarked } from 'lucide-react';
import { checkBackendHealth } from '../services/api';

const NAV_TABS = [
  { key: 'landing',      label: '01 // LAB_OVERVIEW' },
  { key: 'upload',       label: '02 // SCAN_TERMINAL' },
  { key: 'transparency', label: '03 // MODEL_INSIGHTS' },
  { key: 'registry',    label: '04 // REF_REGISTRY' },
];

export default function Navbar({ activeTab, setActiveTab, onResetToHome }) {
  const [backendStatus, setBackendStatus] = useState('checking');

  // Sliding indicator
  const tabRefs = useRef({});
  const navRef  = useRef(null);
  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0, opacity: 0 });

  useEffect(() => {
    const check = async () => {
      try {
        const res = await checkBackendHealth();
        setBackendStatus(res.status === 'healthy' ? 'online' : 'mock');
      } catch {
        setBackendStatus('offline');
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  useLayoutEffect(() => {
    const resolvedTab = activeTab === 'results' ? 'upload' : activeTab;
    const el  = tabRefs.current[resolvedTab];
    const nav = navRef.current;
    if (!el || !nav) return;
    const navRect = nav.getBoundingClientRect();
    const elRect  = el.getBoundingClientRect();
    setIndicatorStyle({ left: elRect.left - navRect.left, width: elRect.width, opacity: 1 });
  }, [activeTab]);

  return (
    <header className="sticky top-0 z-50 bg-[#14171C]/95 backdrop-blur-md border-b border-[#2A2F3A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Logo */}
          <div
            onClick={onResetToHome}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onResetToHome()}
            className="flex items-center space-x-3 cursor-pointer group focus-visible:outline-none"
          >
            <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-[#1C2029] border border-[#2A2F3A] group-hover:border-[#4FD6C4]/60 transition-colors duration-150">
              <Shield className="w-5 h-5 text-[#4FD6C4] transition-transform duration-150 group-hover:scale-105" />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[#4FD6C4] animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-display font-bold text-base tracking-tight text-[#E7E9EC]">VERITAS</span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 rounded bg-[#1C2029] text-[#4FD6C4] border border-[#2A2F3A]">
                  LAB_v2.0
                </span>
              </div>
              <p className="text-[10px] font-mono text-[#8B93A3] hidden sm:block tracking-wide uppercase">
                Image Authenticity Forensics
              </p>
            </div>
          </div>

          {/* Nav tabs */}
          <nav ref={navRef} className="relative flex items-center space-x-1 sm:space-x-2">
            <span
              className="tab-indicator"
              style={{ left: indicatorStyle.left, width: indicatorStyle.width, opacity: indicatorStyle.opacity }}
            />
            {NAV_TABS.map(({ key, label }) => {
              const isActive = key === activeTab || (key === 'upload' && activeTab === 'results');
              return (
                <button
                  key={key}
                  ref={el => { tabRefs.current[key] = el; }}
                  onClick={() => setActiveTab(key)}
                  id={`nav-tab-${key}`}
                  className={`
                    relative px-3.5 py-1.5 rounded-lg text-xs font-mono
                    transition-colors duration-150
                    ${isActive
                      ? 'bg-[#1C2029] text-[#4FD6C4] font-semibold'
                      : 'text-[#8B93A3] hover:text-[#E7E9EC] hover:bg-[#1C2029]/60'
                    }
                  `}
                >
                  {key === 'registry' && <BookMarked className="w-3 h-3 inline mr-1.5 -mt-0.5" />}
                  {label}
                </button>
              );
            })}
          </nav>

          {/* Backend status */}
          <div className="flex items-center space-x-2 px-2.5 py-1 rounded-md bg-[#1C2029] border border-[#2A2F3A] text-xs">
            <span className={`w-2 h-2 rounded-full ${
              backendStatus === 'online' ? 'bg-[#6FCF97] animate-pulse' :
              backendStatus === 'mock'   ? 'bg-amber-400'               : 'bg-[#E8603C]'
            }`} />
            <span className="text-[#8B93A3] font-mono text-[10px] uppercase tracking-wider hidden md:inline">
              {backendStatus === 'online' ? 'INFERENCE: ONLINE' :
               backendStatus === 'mock'   ? 'INFERENCE: LOCAL_MOCK' : 'INFERENCE: DISCONNECTED'}
            </span>
          </div>

        </div>
      </div>
    </header>
  );
}
