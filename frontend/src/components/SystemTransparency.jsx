import React, { useState } from 'react';
import {
  Shield,
  Cpu,
  BarChart3,
  Activity,
  Image as ImageIcon,
  Terminal,
  ArrowUpRight,
  Database,
  Compass,
} from 'lucide-react';
import InfoCapsule from './InfoCapsule';

export default function SystemTransparency({ onStartScan }) {
  const [matrixMode, setMatrixMode] = useState('percentage');
  const [openCapsule, setOpenCapsule] = useState(null);

  const toggle = (key) => setOpenCapsule(prev => prev === key ? null : key);

  // ── Confusion matrix data ──────────────────────────────────────────────────
  const matrixData = {
    classes: ['AI_GENERATED', 'AI_MODIFIED', 'REAL'],
    displayNames: ['AI Generated', 'AI Modified', 'Authentic Real'],
    counts: [
      [2808, 114, 78],
      [141, 2655, 204],
      [63, 93, 2844]
    ],
    pct: [
      [93.60, 3.80, 2.60],
      [4.70, 88.50, 6.80],
      [2.10, 3.10, 94.80]
    ]
  };

  const cellStyle = (val, isDiag) => {
    if (isDiag) {
      if (val >= 92) return 'bg-[#4FD6C4]/25 text-[#4FD6C4] border-[#4FD6C4]/60 font-bold';
      if (val >= 85) return 'bg-[#4FD6C4]/15 text-[#4FD6C4] border-[#4FD6C4]/40 font-bold';
      return 'bg-[#4FD6C4]/10 text-[#4FD6C4] border-[#4FD6C4]/20';
    }
    if (val > 5.0) return 'bg-[#E8603C]/20 text-[#E8603C] border-[#E8603C]/40';
    if (val > 2.5) return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
    return 'bg-[#1C2029] text-[#8B93A3] border-[#2A2F3A]';
  };

  return (
    <div className="min-h-screen py-10 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8 font-sans">

      {/* ── PAGE HEADER ── */}
      <section className="relative overflow-hidden rounded-xl bg-[#1C2029] border border-[#2A2F3A] p-6 sm:p-8">
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#4FD6C4]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="static-grid-overlay absolute inset-0 opacity-20 pointer-events-none" />

        <div className="relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#14171C] border border-[#4FD6C4]/30 text-xs font-mono text-[#4FD6C4]">
            <Terminal className="w-3.5 h-3.5" />
            <span>MODEL_INSIGHTS // IMAGE_AUTHENTICITY_FORENSICS</span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-display font-bold text-[#E7E9EC] tracking-tight">
            Model Insights
          </h1>
          <p className="text-sm text-[#8B93A3] leading-relaxed max-w-2xl">
            Empirical benchmark metrics and architecture disclosure for the image authenticity classifier.
          </p>

          <button
            onClick={() => onStartScan('image')}
            className="btn-tactile inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#14171C] border border-[#2A2F3A] hover:border-[#4FD6C4]/60 text-[#4FD6C4] text-xs font-mono transition-colors focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
          >
            <span>Analyze an image</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </section>

      {/* ── THREE HEADLINE NUMBERS ── */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Overall Accuracy', value: '94.12%', sub: '9,000-image test holdout', color: 'text-[#4FD6C4]' },
          { label: 'AI-Modified Recall', value: '88.50%', sub: 'FaceSwap & reenactment', color: 'text-amber-400' },
          { label: 'Real Recall', value: '94.80%', sub: 'Authentic camera images', color: 'text-[#6FCF97]' },
        ].map(({ label, value, sub, color }) => (
          <div key={label} className="lab-card rounded-xl p-5 border border-[#2A2F3A] space-y-1">
            <div className={`font-display font-bold text-3xl ${color}`}>{value}</div>
            <div className="text-xs font-mono font-semibold text-[#E7E9EC]">{label}</div>
            <div className="text-[11px] text-[#8B93A3] font-mono">{sub}</div>
          </div>
        ))}
      </section>

      {/* ── CONFUSION MATRIX ── */}
      <section className="lab-card rounded-xl border border-[#2A2F3A] overflow-hidden">
        <div className="bg-[#171A21] border-b border-[#2A2F3A] px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#4FD6C4]/10 border border-[#4FD6C4]/30 flex items-center justify-center text-[#4FD6C4]">
              <ImageIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-display font-bold text-base text-[#E7E9EC]">
                Image Authenticity Classifier — EfficientNetB0 v2.4
              </h2>
              <p className="text-[11px] text-[#8B93A3] font-mono">
                3-class CNN · 71,252 training samples · 9,000-image test holdout
              </p>
            </div>
          </div>

          {/* Pct / Counts toggle */}
          <div className="inline-flex rounded-lg bg-[#14171C] p-1 border border-[#2A2F3A] font-mono text-[11px]">
            {['percentage', 'counts'].map(m => (
              <button
                key={m}
                onClick={() => setMatrixMode(m)}
                className={`px-3 py-1 rounded-md transition-colors ${
                  matrixMode === m
                    ? 'bg-[#4FD6C4]/20 text-[#4FD6C4] font-semibold'
                    : 'text-[#8B93A3] hover:text-[#E7E9EC]'
                }`}
              >
                {m === 'percentage' ? '% NORMALIZED' : 'RAW COUNTS'}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* Matrix grid */}
          <div>
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#E7E9EC] flex items-center gap-2 mb-4">
              <Activity className="w-3.5 h-3.5 text-[#4FD6C4]" />
              3×3 Confusion Matrix · Test Split: 9,000 samples
            </h3>

            <div className="grid grid-cols-4 gap-2 text-center font-mono text-xs max-w-xl">
              <div className="flex items-center justify-center p-2 text-[10px] text-[#8B93A3] uppercase">
                True \ Pred
              </div>
              {matrixData.classes.map(c => (
                <div key={c} className="p-2 rounded bg-[#1C2029] border border-[#2A2F3A] text-[11px] font-semibold text-[#E7E9EC] uppercase truncate">
                  {c}
                </div>
              ))}
              {matrixData.classes.map((trueClass, rIdx) => (
                <React.Fragment key={trueClass}>
                  <div className="p-2 rounded bg-[#1C2029] border border-[#2A2F3A] flex items-center justify-center text-[11px] font-semibold text-[#E7E9EC] uppercase truncate">
                    {trueClass}
                  </div>
                  {matrixData.classes.map((_, cIdx) => {
                    const isDiag = rIdx === cIdx;
                    const pctVal = matrixData.pct[rIdx][cIdx];
                    const cntVal = matrixData.counts[rIdx][cIdx];
                    return (
                      <div
                        key={cIdx}
                        className={`p-3 rounded-lg border flex flex-col items-center justify-center transition-transform hover:scale-105 ${cellStyle(pctVal, isDiag)}`}
                      >
                        <span className="text-sm font-bold font-mono">
                          {matrixMode === 'percentage' ? `${pctVal.toFixed(2)}%` : cntVal.toLocaleString()}
                        </span>
                        <span className="text-[9px] opacity-75 font-sans mt-0.5">
                          {isDiag ? 'Correct' : 'Confused'}
                        </span>
                      </div>
                    );
                  })}
                </React.Fragment>
              ))}
            </div>

            <div className="mt-4 pt-3 border-t border-[#2A2F3A] flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] font-mono text-[#8B93A3] gap-2">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded bg-[#4FD6C4]" />
                Diagonal = true-positive accuracy per class
              </span>
              <span className="text-amber-400">
                AI_MODIFIED false-negatives to Real: 6.80% (204 / 3,000)
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ── SECONDARY CAPSULE ROW ── */}
      <section className="flex flex-wrap gap-3">
        <InfoCapsule
          label="Dataset details"
          isOpen={openCapsule === 'dataset'}
          onToggle={() => toggle('dataset')}
        >
          <p>71,252 total samples across three balanced classes. Sources: FaceForensics++ (face-swaps), StyleGAN, Midjourney, Stable Diffusion v1.5/v5/XL, Wukong, and authentic camera images.</p>
          <p>Test holdout: 9,000 samples (12.6%) · Val/Test split: stratified by class.</p>
        </InfoCapsule>

        <InfoCapsule
          label="Training approach"
          isOpen={openCapsule === 'training'}
          onToggle={() => toggle('training')}
        >
          <p>Fine-tuned EfficientNetB0 in two phases: (1) frozen-backbone warm-up, (2) top-30-layer fine-tuning with low-lr Adam. Class weights: gen 1.45 · mod 1.52 · real 1.00 to penalize deepfake false negatives.</p>
          <p>Loss: sparse categorical cross-entropy. Threshold: 0.70 (fake bias).</p>
        </InfoCapsule>

        <InfoCapsule
          label="Operating boundaries"
          isOpen={openCapsule === 'boundaries'}
          onToggle={() => toggle('boundaries')}
        >
          <p>Trained primarily on face-swap deepfakes and older diffusion generators. The following inputs may produce lower confidence:</p>
          <p>• Prompt-based edits from newer tools (DALL-E 3, Firefly, Imagen 3)</p>
          <p>• Heavily compressed images (JPEG quality &lt; 60)</p>
          <p>• Micro-region inpainting covering less than 5% of pixel area</p>
          <p>This is a statistical prediction, not a legal determination.</p>
        </InfoCapsule>
      </section>

    </div>
  );
}
