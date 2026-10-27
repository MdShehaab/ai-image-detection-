import React, { useState, useEffect } from 'react';
import { Shield, ArrowRight, Terminal } from 'lucide-react';
import ScanBeam from './ScanBeam';
import InfoCapsule from './InfoCapsule';

export default function LandingPage({ onStartScan, onNavigateToTransparency }) {
  // Phase-stagger boot animation
  const [phase, setPhase] = useState(0);
  // Capsule accordion — only one open at a time
  const [openCapsule, setOpenCapsule] = useState(null);

  // Cycling telemetry log (image-only)
  const [logIdx, setLogIdx] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 50);
    const t2 = setTimeout(() => setPhase(2), 220);
    const t3 = setTimeout(() => setPhase(3), 400);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setLogIdx(p => (p + 1) % 2), 4500);
    return () => clearInterval(timer);
  }, []);

  const logs = [
    [
      '> [0.04s] STREAM_INIT // TENSOR_SHAPE: [1, 224, 224, 3]',
      '> [0.12s] SPATIAL_BOUNDARY: Gradient inspection — PASS',
      '> [0.24s] CLASS_INFERENCE: 3-class softmax forward pass',
      '> [0.38s] CALIBRATION: Decision threshold 0.70 applied',
      '> [0.49s] VERDICT: 96.8% CONFIDENCE // VERIFIED_REAL'
    ],
    [
      '> [0.03s] STREAM_INIT // TENSOR_SHAPE: [1, 224, 224, 3]',
      '> [0.11s] SPATIAL_BOUNDARY: Mask blending anomaly detected',
      '> [0.23s] CLASS_INFERENCE: ai_generated=0.884 dominant',
      '> [0.36s] CALIBRATION: Decision threshold 0.70 applied',
      '> [0.44s] VERDICT: 88.4% CONFIDENCE // AI_GENERATED'
    ]
  ][logIdx];

  const toggle = (key) => setOpenCapsule(prev => (prev === key ? null : key));

  const capsules = [
    {
      key: 'how',
      label: 'How it works',
      content: (
        <>
          <p>Upload any JPG, PNG, or WEBP image. The classifier runs a forward pass through a fine-tuned EfficientNetB0 backbone and returns a 3-class probability score in under 350 ms.</p>
          <p>No data is stored. Inference is stateless and memory-only.</p>
        </>
      )
    },
    {
      key: 'detects',
      label: 'What it detects',
      content: (
        <>
          <p className="text-[#E7E9EC]">Three output classes:</p>
          <p>• <span className="text-[#E8603C] font-mono">AI-Generated</span> — fully synthetic images (GAN, diffusion)</p>
          <p>• <span className="text-amber-400 font-mono">AI-Modified</span> — real faces swapped or manipulated</p>
          <p>• <span className="text-[#6FCF97] font-mono">Real</span> — authentic camera-captured images</p>
        </>
      )
    },
    {
      key: 'limits',
      label: 'Known limitations',
      content: (
        <>
          <p>Trained primarily on FaceForensics++, StyleGAN, and older diffusion models. Prompt-based edits from newer tools (e.g. DALL-E 3, Firefly) and heavily compressed phone photos may produce lower-confidence results.</p>
          <p>This is a statistical prediction — not a legal determination.</p>
        </>
      )
    },
    {
      key: 'model',
      label: 'Model details',
      content: (
        <>
          <p>EfficientNetB0 backbone, fine-tuned on 71,252 samples across 3 balanced classes. Test-set accuracy: 94.12% (9,000-image holdout). Inference threshold: 0.70.</p>
          <button
            onClick={onNavigateToTransparency}
            className="inline-flex items-center gap-1 text-[#4FD6C4] hover:underline mt-0.5 font-mono text-[11px]"
          >
            Full metrics → Model Insights
          </button>
        </>
      )
    }
  ];

  const stagger = (minPhase) => ({
    className: `transition-all duration-300 ${minPhase <= phase ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      {/* ── HERO ── */}
      <section className="pt-4 pb-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

          {/* Left: headline + CTA */}
          <div
            style={{ transitionDelay: '0ms' }}
            {...stagger(1)}
            className={`lg:col-span-5 space-y-6 text-left transition-all duration-300 ${1 <= phase ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
          >
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-[#1C2029] border border-[#2A2F3A] text-xs font-mono text-[#4FD6C4]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4FD6C4] animate-ping" />
              <span>FORENSIC SCAN LAB // STANDBY</span>
            </div>

            <h1 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-[#E7E9EC] leading-tight">
              Image Authenticity<br />
              <span className="text-[#4FD6C4]">Forensics.</span>
            </h1>

            <p className="text-sm text-[#8B93A3] leading-relaxed max-w-lg font-sans">
              Detect AI-generated and AI-modified images with a single upload.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                onClick={() => onStartScan('image')}
                className="btn-tactile btn-teal-glow px-6 py-3 rounded-lg bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C] font-mono font-semibold text-xs tracking-wider uppercase shadow-sm flex items-center justify-center space-x-2 group focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
              >
                <span>Analyze an image</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-150" />
              </button>

              <button
                onClick={onNavigateToTransparency}
                className="btn-tactile px-4 py-3 rounded-lg bg-[#14171C] hover:bg-[#1C2029] border border-[#2A2F3A] hover:border-[#4FD6C4]/50 text-[#8B93A3] hover:text-[#4FD6C4] font-mono text-xs tracking-wider uppercase flex items-center justify-center space-x-1.5"
              >
                <Terminal className="w-3.5 h-3.5 text-[#4FD6C4]" />
                <span>Model Insights</span>
              </button>
            </div>

            {/* Mini stat strip — image-only */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-[#2A2F3A] text-[11px] font-mono text-[#8B93A3]">
              <div>
                <span className="block text-[#4FD6C4] font-bold text-sm">94.1%</span>
                <span>ACCURACY</span>
              </div>
              <div>
                <span className="block text-[#4FD6C4] font-bold text-sm">&lt; 350ms</span>
                <span>INFERENCE</span>
              </div>
              <div>
                <span className="block text-[#6FCF97] font-bold text-sm">3-CLASS</span>
                <span>OUTPUT</span>
              </div>
            </div>
          </div>

          {/* Right: scan-beam demo panel */}
          <div
            style={{ transitionDelay: '60ms' }}
            className={`lg:col-span-7 transition-all duration-300 ${2 <= phase ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
          >
            <div className="lab-card rounded-xl border border-[#2A2F3A] overflow-hidden shadow-2xl">

              {/* Terminal header */}
              <div className="px-4 py-2.5 bg-[#14171C] border-b border-[#2A2F3A] flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[#E8603C]/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                  <div className="w-2.5 h-2.5 rounded-full bg-[#6FCF97]/80" />
                  <span className="text-[10px] font-mono text-[#8B93A3] ml-2">
                    MONITOR_01 // LIVE_INFERENCE_STREAM
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-[10px] font-mono text-[#4FD6C4]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#4FD6C4] animate-pulse" />
                  <span>SWEEP_ACTIVE</span>
                </div>
              </div>

              {/* Scan canvas */}
              <div className="relative h-64 sm:h-72 bg-[#12151A] flex items-center justify-center overflow-hidden">
                <div className="relative w-full h-full flex items-center justify-center p-6">
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
                <ScanBeam isActive={true} showGrid={true} label="SCAN_BEAM // IMAGE_CLASSIFIER" />
              </div>

              {/* Telemetry readout */}
              <div className="p-4 bg-[#14171C] border-t border-[#2A2F3A] font-mono text-xs space-y-1.5 min-h-[116px]">
                <div className="text-[10px] text-[#8B93A3] uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>INFERENCE TELEMETRY</span>
                  <span className="text-[#4FD6C4]">CYCLE: 0{logIdx + 1}/02</span>
                </div>
                {logs.map((line, i) => (
                  <div
                    key={i}
                    className={`transition-opacity duration-300 ${
                      i === logs.length - 1
                        ? line.includes('VERIFIED_REAL')
                          ? 'text-[#6FCF97] font-semibold'
                          : 'text-[#E8603C] font-semibold'
                        : 'text-[#8B93A3]'
                    }`}
                  >
                    {line}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── INFO CAPSULE ROW ── */}
      <section
        style={{ transitionDelay: '80ms' }}
        className={`pb-12 transition-all duration-300 ${3 <= phase ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
      >
        <div className="border-t border-[#2A2F3A] pt-8">
          <div className="flex flex-wrap gap-3">
            {capsules.map(({ key, label, content }) => (
              <InfoCapsule
                key={key}
                label={label}
                isOpen={openCapsule === key}
                onToggle={() => toggle(key)}
              >
                {content}
              </InfoCapsule>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
}
