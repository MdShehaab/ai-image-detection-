import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Image as ImageIcon, 
  Video as VideoIcon, 
  FileText, 
  ArrowRight, 
  Terminal, 
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Fingerprint,
  Layers,
  Crosshair
} from 'lucide-react';
import ScanBeam from './ScanBeam';

export default function LandingPage({ onStartScan, onSelectModule }) {
  const [activeLogIndex, setActiveLogIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveLogIndex((prev) => (prev + 1) % 3);
    }, 4500);

    return () => clearInterval(timer);
  }, []);

  const currentSequence = [
    [
      "> [0.04s] STREAM_INIT // TENSOR_SHAPE: [1, 224, 224, 3]",
      "> [0.12s] FFT_FREQ_DOMAIN: Azimuthal frequency decay: NOMINAL",
      "> [0.24s] FACIAL_GEOMETRY: Corneal specular symmetry: 98.6% MATCH",
      "> [0.38s] ERROR_LEVEL_ANALYSIS: Quantization delta: PASS",
      "> [0.49s] VERDICT: 96.8% PROBABILITY // VERIFIED_REAL"
    ],
    [
      "> [0.03s] STREAM_INIT // VIDEO_FPS: 29.97 | DURATION: 12.4s",
      "> [0.15s] BLINK_ANALYSIS: Inter-blink cadence irregularity detected",
      "> [0.29s] PHONEME_VISEME: Lip-audio temporal lag delta: 64ms ANOMALY",
      "> [0.42s] WARPING_SEAM: Edge blending inconsistency at chin boundary",
      "> [0.55s] VERDICT: 91.4% PROBABILITY // AI_MODIFIED (DEEPFAKE)"
    ],
    [
      "> [0.02s] STREAM_INIT // OCR_LAYOUT_PARSER [PDF_300DPI]",
      "> [0.11s] GLYPH_KERNING: Font rendering kerning mismatch @ Line 14",
      "> [0.22s] SIFT_CLONE_DETECTION: Duplicate stamp signature identified",
      "> [0.35s] METADATA_TRACE: PDF modified via non-original toolstream",
      "> [0.44s] VERDICT: 88.7% PROBABILITY // FORGERY_FLAGGED"
    ]
  ][activeLogIndex];

  const modules = [
    {
      id: 'image',
      caseNumber: 'MODULE_01',
      title: 'IMAGE AUTHENTICITY',
      subtitle: 'PIXEL & FREQUENCY FORENSICS',
      icon: ImageIcon,
      description: 'Detects synthetic AI generation, face swaps, and pixel manipulation.',
      features: [
        'Facial boundary & blending seam detection',
        '2D frequency spectrum analysis',
        'Corneal specular reflection symmetry'
      ],
      formats: 'PNG, JPG, WEBP, BMP'
    },
    {
      id: 'video',
      caseNumber: 'MODULE_02',
      title: 'VIDEO TEMPORAL STREAM',
      subtitle: 'SPATIO-TEMPORAL DYNAMICS',
      icon: VideoIcon,
      description: 'Identifies synthetic face manipulation, temporal flickers, and lip-sync anomalies.',
      features: [
        'Audio-Visual lip-sync correlation',
        'Blink frequency & facial dynamics',
        'Inter-frame jitter & temporal seams'
      ],
      formats: 'MP4, AVI, MOV, WEBM'
    },
    {
      id: 'document',
      caseNumber: 'MODULE_03',
      title: 'DOCUMENT FORGERY',
      subtitle: 'LAYOUT & TYPOGRAPHY OCR',
      icon: FileText,
      description: 'Uncovers altered text, forged stamps, and tampered document layouts.',
      features: [
        'Cloned stamp & seal detection (SIFT)',
        'Font kerning & altered text detection',
        'Document metadata modification trace'
      ],
      formats: 'PDF, PNG, JPG, TIFF'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-16">
      
      {/* ========================================================================= */}
      {/* SIGNATURE HERO: LIVE FORENSIC SCAN LAB MINI-DEMO                          */}
      {/* ========================================================================= */}
      <section className="pt-4 pb-2">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Left Column: Context & Primary Trigger */}
          <div className="lg:col-span-5 space-y-6 text-left">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-[#1C2029] border border-[#2A2F3A] text-xs font-mono text-[#4FD6C4]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4FD6C4] animate-ping" />
              <span>FORENSIC SCAN LAB // STANDBY</span>
            </div>

            <h1 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-[#E7E9EC] leading-tight">
              Media Authenticity <br />
              <span className="text-[#4FD6C4]">Forensic Engine.</span>
            </h1>

            <p className="text-sm text-[#8B93A3] leading-relaxed max-w-lg font-sans">
              Detects AI-generated images, deepfakes, and document forgery in real time.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={() => onStartScan('auto')}
                className="px-6 py-3 rounded-lg bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C] font-mono font-semibold text-xs tracking-wider uppercase transition-all shadow-sm flex items-center justify-center space-x-2 group focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
              >
                <span>INITIALIZE SCAN</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <a
                href="#case-modules"
                className="px-5 py-3 rounded-lg bg-[#1C2029] hover:bg-[#252A35] border border-[#2A2F3A] text-[#E7E9EC] font-mono text-xs tracking-wider uppercase transition-all flex items-center justify-center space-x-2"
              >
                <Crosshair className="w-3.5 h-3.5 text-[#4FD6C4]" />
                <span>CASE MODULES</span>
              </a>
            </div>

            {/* Micro Spec Readout */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-[#2A2F3A] text-[11px] font-mono text-[#8B93A3]">
              <div>
                <span className="block text-[#E7E9EC] font-bold text-sm">3</span>
                <span>PIPELINES</span>
              </div>
              <div>
                <span className="block text-[#4FD6C4] font-bold text-sm">&lt; 350ms</span>
                <span>INFERENCE</span>
              </div>
              <div>
                <span className="block text-[#6FCF97] font-bold text-sm">REST API</span>
                <span>MODULAR</span>
              </div>
            </div>
          </div>

          {/* Right Column: THE HERO MINI DEMO (Scan Beam + Live Telemetry) */}
          <div className="lg:col-span-7">
            <div className="lab-card rounded-xl border border-[#2A2F3A] overflow-hidden shadow-2xl">
              
              {/* Terminal Frame Header */}
              <div className="px-4 py-2.5 bg-[#14171C] border-b border-[#2A2F3A] flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#E8603C]/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#6FCF97]/80" />
                  <span className="text-[10px] font-mono text-[#8B93A3] ml-2">
                    MONITOR_01 // LIVE_TELEMETRY_STREAM
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-[10px] font-mono text-[#4FD6C4]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4FD6C4] animate-pulse" />
                  <span>SWEEP_ACTIVE</span>
                </div>
              </div>

              {/* Forensic Media Canvas with Sweeping Scan Beam */}
              <div className="relative h-64 sm:h-72 bg-[#12151A] flex items-center justify-center overflow-hidden">
                
                {/* Simulated Target Media Subject (Clean - no filler coordinate text) */}
                <div className="relative w-full h-full flex items-center justify-center p-6">
                  {/* Subtle Wireframe Target SVG Face/Media Visual */}
                  <svg className="w-48 h-48 opacity-30 text-[#4FD6C4]" viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="1">
                    <circle cx="50" cy="45" r="30" strokeDasharray="3 3" />
                    <ellipse cx="50" cy="45" rx="20" ry="26" />
                    <circle cx="42" cy="40" r="3" fill="currentColor" />
                    <circle cx="58" cy="40" r="3" fill="currentColor" />
                    <path d="M42 58 Q50 64 58 58" />
                    <path d="M50 43 L50 51 L47 52" />
                    <line x1="20" y1="45" x2="80" y2="45" strokeDasharray="2 2" />
                    <line x1="50" y1="15" x2="50" y2="75" strokeDasharray="2 2" />
                  </svg>
                </div>

                {/* SIGNATURE SCAN BEAM COMPONENT (Active Sweeping Beam) */}
                <ScanBeam 
                  isActive={true} 
                  showGrid={true} 
                  showBoundingBox={activeLogIndex === 1}
                  bbox={{ x: '35%', y: '28%', width: '30%', height: '38%' }}
                  bboxLabel="ANOMALY_SEAM // DELTA_91%"
                  label="SCAN_BEAM // SWEEP_FREQ_2.0s"
                />
              </div>

              {/* Monospace Live Telemetry Readout */}
              <div className="p-4 bg-[#14171C] border-t border-[#2A2F3A] font-mono text-xs space-y-1.5 min-h-[120px]">
                <div className="text-[10px] text-[#8B93A3] uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>REAL-TIME INFERENCE TELEMETRY LOGS</span>
                  <span className="text-[#4FD6C4]">CYCLE: 0{activeLogIndex + 1}/03</span>
                </div>
                {currentSequence.map((logLine, idx) => (
                  <div 
                    key={idx} 
                    className={`transition-opacity duration-300 ${
                      idx === currentSequence.length - 1 
                        ? logLine.includes('VERIFIED_REAL') 
                          ? 'text-[#6FCF97] font-semibold' 
                          : 'text-[#E8603C] font-semibold'
                        : 'text-[#8B93A3]'
                    }`}
                  >
                    {logLine}
                  </div>
                ))}
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* THREE MODULE CASE-FILE TABS                                               */}
      {/* ========================================================================= */}
      <section id="case-modules" className="pt-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-[#2A2F3A] gap-2">
          <div>
            <span className="text-xs font-mono text-[#4FD6C4] tracking-widest uppercase">
              CASE_CATALOG // DETECTORS
            </span>
            <h2 className="font-display text-2xl font-bold text-[#E7E9EC] mt-1">
              Modular Forensic Engines
            </h2>
          </div>
          <p className="text-xs font-mono text-[#8B93A3]">
            SELECT TARGET PIPELINE TO BEGIN ISOLATED INSPECTION
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {modules.map((mod) => {
            const Icon = mod.icon;
            return (
              <div
                key={mod.id}
                className="lab-card rounded-xl p-6 flex flex-col justify-between border border-[#2A2F3A] hover:border-[#4FD6C4]/50 transition-colors relative group"
              >
                {/* Case Header Tab */}
                <div>
                  <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#2A2F3A]">
                    <span className="text-[11px] font-mono font-bold text-[#4FD6C4] tracking-wider">
                      {mod.caseNumber}
                    </span>
                    <span className="text-[10px] font-mono text-[#8B93A3]">
                      FORMATS: {mod.formats}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 mb-3">
                    <div className="w-8 h-8 rounded-lg bg-[#14171C] border border-[#2A2F3A] flex items-center justify-center text-[#4FD6C4]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-sm text-[#E7E9EC] tracking-tight">
                        {mod.title}
                      </h3>
                      <p className="text-[10px] font-mono text-[#8B93A3]">
                        {mod.subtitle}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-[#8B93A3] leading-relaxed mb-5 font-sans">
                    {mod.description}
                  </p>

                  {/* Checklist (Trimmed to 3 clear items) */}
                  <div className="space-y-2 mb-6">
                    <div className="text-[10px] font-mono uppercase tracking-wider text-[#8B93A3]">
                      // FORENSIC CHECKS
                    </div>
                    {mod.features.map((feat, idx) => (
                      <div key={idx} className="flex items-start space-x-2 text-xs text-[#E7E9EC]">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#4FD6C4] shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action CTA */}
                <div className="pt-4 border-t border-[#2A2F3A]">
                  <button
                    onClick={() => onSelectModule(mod.id)}
                    className="w-full py-2.5 rounded-lg text-xs font-mono font-semibold bg-[#14171C] hover:bg-[#4FD6C4] text-[#E7E9EC] hover:text-[#14171C] border border-[#2A2F3A] hover:border-[#4FD6C4] transition-all flex items-center justify-center space-x-2"
                  >
                    <span>OPEN {mod.caseNumber}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* FORENSIC METHODOLOGY PIPELINE                                            */}
      {/* ========================================================================= */}
      <section className="pt-4">
        <div className="lab-card rounded-xl p-8 border border-[#2A2F3A]">
          <div className="flex items-center justify-between mb-8 pb-4 border-b border-[#2A2F3A]">
            <div>
              <span className="text-xs font-mono text-[#4FD6C4] uppercase">SYSTEM_WORKFLOW</span>
              <h3 className="font-display text-xl font-bold text-[#E7E9EC]">Four-Stage Authenticity Validation</h3>
            </div>
            <span className="text-xs font-mono text-[#8B93A3] hidden sm:inline">STANDARDIZED PROTOCOL</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="text-xs font-mono font-bold text-[#4FD6C4]">01 // DISPATCH</div>
              <h4 className="text-xs font-semibold text-[#E7E9EC]">MIME Header Auto-Route</h4>
              <p className="text-xs text-[#8B93A3]">MIME validation inspects magic bytes and routes payload to the isolated worker pool.</p>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-mono font-bold text-[#4FD6C4]">02 // EXTRACT</div>
              <h4 className="text-xs font-semibold text-[#E7E9EC]">Spectral Preprocessing</h4>
              <p className="text-xs text-[#8B93A3]">Executes 2D-FFT frequency spectrum analysis, face alignment, or OCR bounding segmenting.</p>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-mono font-bold text-[#4FD6C4]">03 // INFERENCE</div>
              <h4 className="text-xs font-semibold text-[#E7E9EC]">Neural Model Ensemble</h4>
              <p className="text-xs text-[#8B93A3]">Evaluates 3-class probability distributions via EfficientNet and temporal transformers.</p>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-mono font-bold text-[#6FCF97]">04 // VERDICT</div>
              <h4 className="text-xs font-semibold text-[#E7E9EC]">Case Marking & Report</h4>
              <p className="text-xs text-[#8B93A3]">Generates stamped verdict, confidence rating, artifact breakdown, and audit metadata.</p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
}
