import React, { useState, useEffect, useRef } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  RotateCcw,
  Download,
  Terminal,
  Crosshair,
  Clock,
  Cpu,
  FileCheck,
  Copy,
  Check,
} from 'lucide-react';
import VisualGauge from './VisualGauge';
import ScanBeam from './ScanBeam';
import InfoCapsule from './InfoCapsule';
import ReferenceCheckCard from './ReferenceCheckCard';

// ── Decision cutoffs (probabilities on a 0-1 scale) ─────────────────────────
// fake (AI-generated + AI-modified) >= FAKE_CUTOFF  -> fake verdict
// real >= REAL_CUTOFF                               -> LIKELY REAL
// anything else                                     -> INCONCLUSIVE
const FAKE_CUTOFF = 0.70;
const REAL_CUTOFF = 0.75;

const pctOf = (p, total) => Math.round((p / total) * 1000) / 10;

// Pure function: derives everything the page needs from the API result.
// All values are computed in a fixed order, so nothing is used before it exists.
function deriveView(result) {
  if (!result) return null;

  const refDriven = result.reference_driven === true;
  const rawVerdict = String(result.verdict || '').toUpperCase().replace(/-/g, '_');
  const refIsReal = rawVerdict === 'REAL';

  // 1) Probabilities (prefer the classifier estimate when the registry decided)
  const src =
    refDriven && result.classifier_estimate?.probabilities
      ? result.classifier_estimate.probabilities
      : result.probabilities;
  const hasProbs = !!src && src.ai_generated !== undefined;
  const pAiGen = hasProbs ? Number(src.ai_generated) || 0 : 0;
  const pAiMod = hasProbs ? Number(src.ai_modified) || 0 : 0;
  const pReal = hasProbs ? Number(src.real) || 0 : 0;
  const pFakeCombined = pAiGen + pAiMod;
  const total = pAiGen + pAiMod + pReal || 1;

  // 2) Verdict label and tone
  let label;
  let tone; // 'green' | 'amber' | 'red'
  if (refDriven) {
    tone = refIsReal ? 'green' : 'red';
    label = refIsReal ? 'REAL' : 'AI-MODIFIED';
  } else if (!hasProbs) {
    tone = 'amber';
    label = 'INCONCLUSIVE';
  } else if (pFakeCombined >= FAKE_CUTOFF) {
    tone = 'red';
    label = pAiMod >= pAiGen ? 'AI-MODIFIED' : 'AI-GENERATED';
  } else if (pReal >= REAL_CUTOFF) {
    tone = 'green';
    label = 'LIKELY REAL';
  } else {
    tone = 'amber';
    label = 'INCONCLUSIVE';
  }
  const isInconclusive = !refDriven && tone === 'amber';

  // 3) Gauge (number always matches its label)
  const refSim =
    result.reference_check?.best_match?.similarity ??
    result.reference_check?.similarity ??
    null;
  let gaugeLabel;
  let gaugeTooltip = null;
  let gaugeScore;
  if (refDriven) {
    gaugeLabel = 'SIMILARITY';
    gaugeTooltip = 'Similarity to the closest registered original';
    gaugeScore = refSim !== null ? Math.round(refSim * 100) : Math.round(Number(result.confidence) || 0);
  } else if (tone === 'red') {
    gaugeLabel = 'FAKE PROBABILITY';
    gaugeScore = Math.round(pFakeCombined * 100);
  } else {
    gaugeLabel = 'REAL PROBABILITY';
    gaugeScore = Math.round(pReal * 100);
  }
  const gaugeVerdict = tone === 'green' ? 'REAL' : tone === 'amber' ? 'SUSPICIOUS' : 'FAKE';

  return {
    refDriven,
    refIsReal,
    label,
    tone,
    isInconclusive,
    hasProbs,
    gaugeLabel,
    gaugeTooltip,
    gaugeScore,
    gaugeVerdict,
    pctGen: pctOf(pAiGen, total),
    pctMod: pctOf(pAiMod, total),
    pctReal: pctOf(pReal, total),
  };
}

function ResultsPageInner({ scanData, onReset, scanFile }) {
  // Derive first, so every later line can safely use these values
  const view = deriveView(scanData?.result);

  // Staged reveal animation
  const [revealPhase, setRevealPhase] = useState(0);
  const [isRevealed, setIsRevealed] = useState(false);
  const [displayScore, setDisplayScore] = useState(0);
  const countRef = useRef(null);

  // Capsule accordion state (one open at a time)
  const [openCapsule, setOpenCapsule] = useState(null);
  const [copiedJson, setCopiedJson] = useState(false);

  const toggleCapsule = (key) => setOpenCapsule((prev) => (prev === key ? null : key));

  const startCountUp = (target) => {
    const steps = 60;
    let step = 0;
    if (countRef.current) clearInterval(countRef.current);
    countRef.current = setInterval(() => {
      step++;
      setDisplayScore(Math.min(Math.round((target / steps) * step), target));
      if (step >= steps) clearInterval(countRef.current);
    }, 800 / steps);
  };

  useEffect(() => {
    setRevealPhase(0);
    setIsRevealed(false);
    setDisplayScore(0);
    setOpenCapsule(null);

    const t1 = setTimeout(() => setRevealPhase(1), 600);
    const t2 = setTimeout(() => setRevealPhase(2), 1200);
    const t3 = setTimeout(() => {
      setRevealPhase(3);
      setIsRevealed(true);
    }, 1800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      if (countRef.current) clearInterval(countRef.current);
    };
  }, [scanData]);

  // Score count-up once the verdict is revealed
  useEffect(() => {
    if (!isRevealed || !view) return;
    startCountUp(view.gaugeScore);
    return () => clearInterval(countRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRevealed, scanData]);

  if (!view) {
    return (
      <div className="text-center py-20 font-mono">
        <p className="text-[#8B93A3]">NO FORENSIC RECORD AVAILABLE.</p>
        <button
          onClick={onReset}
          className="btn-tactile mt-4 px-4 py-2 bg-[#1C2029] border border-[#4FD6C4] text-[#4FD6C4] rounded-lg text-xs font-mono"
        >
          RETURN TO UPLOAD
        </button>
      </div>
    );
  }

  const { result, fileInfo } = scanData;
  const {
    refDriven,
    refIsReal,
    label: verdictLabel,
    tone,
    isInconclusive,
    hasProbs,
    gaugeLabel,
    gaugeTooltip,
    gaugeScore,
    gaugeVerdict,
    pctGen,
    pctMod,
    pctReal,
  } = view;

  const stampIsGreen = tone === 'green';
  const stampIsAmber = tone === 'amber';

  const downloadJson = () => {
    const a = document.createElement('a');
    a.href = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(result, null, 2));
    a.download = `forensic_result_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const skipToVerdict = () => {
    setIsRevealed(true);
    setRevealPhase(3);
    startCountUp(gaugeScore);
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6 font-sans">

      {/* ── HEADER ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2A2F3A] pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#4FD6C4] mb-1">
            <Terminal className="w-3.5 h-3.5" />
            <span>CASE_DOSSIER // {result.module?.toUpperCase() || 'IMAGE_SCAN'}</span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-[#E7E9EC]">
            Forensic Findings
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={downloadJson}
            className="btn-tactile px-3.5 py-2 rounded-lg bg-[#1C2029] hover:bg-[#252A35] border border-[#2A2F3A] text-[#E7E9EC] text-xs font-mono flex items-center space-x-2 transition-colors focus-visible:outline-none"
            aria-label="Export result as JSON"
          >
            <Download className="w-3.5 h-3.5 text-[#4FD6C4]" />
            <span>Export JSON</span>
          </button>
          <button
            onClick={onReset}
            className="btn-tactile btn-teal-glow px-4 py-2 rounded-lg bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C] text-xs font-mono font-semibold flex items-center space-x-1.5 focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>New scan</span>
          </button>
        </div>
      </div>

      {/* ── LIVE ANALYSIS PROGRESS BANNER ── */}
      {!isRevealed && (
        <div className="rounded-xl bg-[#1C2029] border border-[#4FD6C4]/40 p-6 space-y-4 shadow-xl relative overflow-hidden animate-fade-in">
          <div className="scan-beam-line animate-sweep" />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-[#4FD6C4] animate-ping" />
              <span className="font-mono text-xs text-[#4FD6C4] uppercase font-bold tracking-wider">
                RUNNING IMAGE CLASSIFIER
              </span>
            </div>
            <button
              onClick={skipToVerdict}
              className="text-[11px] font-mono text-[#8B93A3] hover:text-[#4FD6C4] underline transition-colors"
            >
              Skip to verdict &gt;&gt;
            </button>
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {[
              'Ingesting image tensor and running 3-class forward pass…',
              'Evaluating spatial boundary gradients and confidence calibration…',
              'Generating verdict and probability distribution…',
            ].map((step, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 transition-colors ${
                  revealPhase >= i ? 'text-[#E7E9EC]' : 'text-[#8B93A3]/40'
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    revealPhase > i
                      ? 'bg-[#6FCF97] text-[#14171C]'
                      : revealPhase === i
                      ? 'bg-[#4FD6C4] text-[#14171C] animate-pulse'
                      : 'bg-[#2A2F3A] text-[#8B93A3]'
                  }`}
                >
                  {revealPhase > i ? '✓' : i + 1}
                </span>
                <span>{step}</span>
              </div>
            ))}
          </div>

          <div className="w-full bg-[#14171C] h-1.5 rounded-full overflow-hidden border border-[#2A2F3A]">
            <div
              className="bg-[#4FD6C4] h-full transition-all duration-500 ease-out"
              style={{
                width:
                  revealPhase === 0 ? '30%' : revealPhase === 1 ? '65%' : revealPhase === 2 ? '90%' : '100%',
              }}
            />
          </div>
        </div>
      )}

      {/* ── VERDICT CARD ── */}
      <div
        className={`lab-card rounded-xl p-6 sm:p-8 border border-[#2A2F3A] relative overflow-hidden transition-all duration-700 ${
          isRevealed ? 'opacity-100 translate-y-0' : 'opacity-30 blur-sm translate-y-2'
        }`}
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">

          {/* Gauge */}
          <div className="lg:col-span-4 flex flex-col items-center justify-center p-2">
            <VisualGauge
              score={gaugeScore}
              displayScore={isRevealed ? displayScore : 0}
              verdict={gaugeVerdict}
              size={180}
              animate={isRevealed}
              label={gaugeLabel}
            />
            <div
              className="text-[11px] font-mono text-[#8B93A3] mt-3 uppercase tracking-wider"
              title={gaugeTooltip || undefined}
            >
              {gaugeLabel}
              {gaugeTooltip && (
                <span className="ml-1 text-[#4FD6C4] cursor-help" title={gaugeTooltip}>ⓘ</span>
              )}
            </div>
          </div>

          {/* Verdict stamp */}
          <div className="lg:col-span-8 space-y-5">
            <div className="flex flex-wrap items-center gap-4">
              <div
                className={`
                  px-4 py-2 rounded font-display font-bold text-lg sm:text-xl uppercase tracking-wider
                  inline-flex items-center space-x-2.5 select-none
                  ${
                    isRevealed
                      ? stampIsGreen
                        ? 'verdict-stamp-verified bg-[#6FCF97]/10 verdict-stamp-animate-verified'
                        : stampIsAmber
                        ? 'border-2 border-amber-400 text-amber-400 bg-amber-400/10 verdict-stamp-animate-verified'
                        : 'verdict-stamp-flagged bg-[#E8603C]/10 verdict-stamp-animate-flagged'
                      : 'opacity-0 scale-50'
                  }
                `}
              >
                {stampIsGreen ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                <span>{verdictLabel}</span>
              </div>
            </div>

            {/* One-line note for classifier-only results (not shown for registry results) */}
            {isRevealed && !refDriven && (
              <p
                className={`text-sm font-sans leading-relaxed ${
                  isInconclusive ? 'text-amber-400/90' : 'text-[#8B93A3]'
                }`}
              >
                {isInconclusive
                  ? 'The classifier is not confident. Register an original or get a second opinion.'
                  : 'Statistical prediction from a trained classifier. Not proof of authenticity.'}
              </p>
            )}

            {/* Slim metadata strip */}
            <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-[#8B93A3] pt-3 border-t border-[#2A2F3A]">
              <span className="flex items-center gap-1.5">
                <Crosshair className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {fileInfo?.name || result.file_name || 'artifact'}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {result.execution_time_ms ? `${result.execution_time_ms} ms` : '—'}
              </span>
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {refDriven ? 'Reference registry' : result.model_version || 'EfficientNetB0'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── HOW THIS WAS DECIDED capsule (always shown, collapsed by default) ── */}
      {isRevealed && (
        <div className="animate-fade-slide-up">
          <InfoCapsule
            label="How this was decided"
            isOpen={openCapsule === 'decision'}
            onToggle={() => toggleCapsule('decision')}
          >
            <p className="text-sm text-[#8B93A3] leading-relaxed font-sans">
              {refDriven ? (
                refIsReal ? (
                  <>
                    Compared against your registered originals: this image{' '}
                    <span className="font-semibold text-[#6FCF97]">matches</span> one, with no significant changes.
                  </>
                ) : (
                  <>
                    Compared against your registered originals: this image{' '}
                    <span className="font-semibold text-[#E8603C]">differs</span> from one. The system cannot tell
                    AI edits from manual edits.
                  </>
                )
              ) : hasProbs ? (
                <>
                  No registered original matched. The classifier gave:{' '}
                  <span className="text-[#E8603C] font-semibold font-mono">AI-generated {pctGen}%</span>,{' '}
                  <span className="text-amber-400 font-semibold font-mono">AI-modified {pctMod}%</span>,{' '}
                  <span className="text-[#6FCF97] font-semibold font-mono">Real {pctReal}%</span>. An image is flagged
                  as fake only when the combined fake probability is {Math.round(FAKE_CUTOFF * 100)}% or higher, and
                  called likely real only when the real probability is {Math.round(REAL_CUTOFF * 100)}% or higher.
                  Anything in between is inconclusive. This is a statistical prediction, not proof of authenticity.
                </>
              ) : (
                <>No registered original matched, and the classifier did not return probabilities for this image.</>
              )}
            </p>
          </InfoCapsule>
        </div>
      )}

      {/* ── IMAGE INSPECTION CANVAS ── */}
      {isRevealed && (
        <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4 animate-fade-slide-up">
          <div className="flex items-center justify-between pb-3 border-b border-[#2A2F3A]">
            <div className="flex items-center space-x-2">
              <Crosshair className="w-4 h-4 text-[#4FD6C4]" />
              <h3 className="font-display font-bold text-sm text-[#E7E9EC]">Visual Inspection Grid</h3>
            </div>
            <span className="text-[10px] font-mono text-[#8B93A3]">STATIC_SCAN_GRID</span>
          </div>

          <div className="relative rounded-lg bg-[#12151A] border border-[#2A2F3A] flex items-center justify-center p-4 overflow-hidden min-h-[240px]">
            {fileInfo?.previewUrl ? (
              <img
                src={fileInfo.previewUrl}
                alt="Analyzed image"
                className="max-h-80 object-contain rounded z-0"
              />
            ) : (
              <div className="text-center p-8 space-y-2 font-mono">
                <FileCheck className="w-10 h-10 text-[#4FD6C4] mx-auto opacity-70" />
                <p className="text-xs text-[#8B93A3]">IMAGE PROCESSED // NO PREVIEW AVAILABLE</p>
              </div>
            )}
            {/* Scan grid overlay only (the backend returns no regions) */}
            <ScanBeam isActive={false} showGrid={true} />
          </div>
        </div>
      )}

      {/* ── REFERENCE CHECK CARD ── */}
      {isRevealed && result.module !== 'video_detector' && result.module !== 'document_detector' && (
        <ReferenceCheckCard referenceCheck={result.reference_check} fileInfo={fileInfo} scanFile={scanFile} />
      )}

      {/* ── SECONDARY CAPSULE ROW ── */}
      {isRevealed && (
        <div className="animate-fade-slide-up flex flex-wrap gap-3 pt-2">

          {/* Technical details */}
          <InfoCapsule
            label="Technical details"
            isOpen={openCapsule === 'tech'}
            onToggle={() => toggleCapsule('tech')}
          >
            <div className="space-y-2 font-mono text-[11px]">
              <div className="flex justify-between">
                <span className="text-[#8B93A3]">Model:</span>
                <span className="text-[#E7E9EC]">{result.model_version || result.module || 'EfficientNetB0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8B93A3]">Inference time:</span>
                <span className="text-[#E7E9EC]">
                  {result.execution_time_ms ? `${result.execution_time_ms} ms` : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[#8B93A3]">Fake cutoff / real cutoff:</span>
                <span className="text-[#E7E9EC]">
                  {FAKE_CUTOFF} / {REAL_CUTOFF}
                </span>
              </div>
              <div className="border-t border-[#2A2F3A] pt-2 text-[10px] text-[#8B93A3]">
                Raw softmax (AI-gen, AI-mod, Real):{' '}
                {hasProbs ? `[${pctGen}%, ${pctMod}%, ${pctReal}%]` : '—'}
              </div>
              <button
                onClick={copyJson}
                className="btn-tactile flex items-center gap-1.5 text-[#8B93A3] hover:text-[#4FD6C4] transition-colors pt-1"
              >
                {copiedJson ? <Check className="w-3 h-3 text-[#6FCF97]" /> : <Copy className="w-3 h-3" />}
                <span>{copiedJson ? 'Copied!' : 'Copy raw JSON'}</span>
              </button>
            </div>
          </InfoCapsule>

          {/* How to read */}
          <InfoCapsule
            label="How to read this result"
            isOpen={openCapsule === 'howtoread'}
            onToggle={() => toggleCapsule('howtoread')}
          >
            <p>
              For classifier results, the gauge shows either the{' '}
              <span className="text-[#4FD6C4] font-mono">fake probability</span> (when the image is flagged) or the{' '}
              <span className="text-[#4FD6C4] font-mono">real probability</span> (otherwise). For registry results it
              shows similarity to the closest registered original.
            </p>
            <p>
              A high AI-generated score means the model found patterns consistent with synthetic generation. A high
              AI-modified score suggests manipulation of a real face (such as a face swap).
            </p>
          </InfoCapsule>

          {/* Limitations */}
          <InfoCapsule
            label="Limitations of this prediction"
            isOpen={openCapsule === 'limits'}
            onToggle={() => toggleCapsule('limits')}
          >
            <p>
              The classifier was trained on face-swap deepfakes and older image generators. Prompt-based edits from
              newer tools, webcam photos and heavily compressed phone images may be misclassified.
            </p>
            <p>
              When the classifier is not confident, the page shows INCONCLUSIVE. This result is a statistical estimate,
              not a legal or forensic determination.
            </p>
          </InfoCapsule>
        </div>
      )}

      {/* ── SECONDARY ACTION ── */}
      {isRevealed && (
        <div className="flex items-center gap-3 pt-2 animate-fade-slide-up">
          <button
            onClick={onReset}
            className="btn-tactile btn-teal-glow px-5 py-2.5 rounded-lg bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C] text-xs font-mono font-semibold flex items-center gap-2 focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            New scan
          </button>
          <button
            onClick={downloadJson}
            className="btn-tactile px-4 py-2.5 rounded-lg bg-[#1C2029] hover:bg-[#252A35] border border-[#2A2F3A] text-[#E7E9EC] text-xs font-mono flex items-center gap-2 transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[#4FD6C4]" />
            Export full report
          </button>
        </div>
      )}
    </div>
  );
}

// Error boundary: a rendering bug shows a message instead of a blank page
class ResultsErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error, info) {
    console.error('ResultsPage crashed:', error, info);
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="text-center py-20 font-mono space-y-4">
          <p className="text-[#E8603C]">Something went wrong displaying this result.</p>
          <button
            onClick={this.props.onReset}
            className="btn-tactile px-4 py-2 bg-[#1C2029] border border-[#4FD6C4] text-[#4FD6C4] rounded-lg text-xs font-mono"
          >
            NEW SCAN
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function ResultsPage(props) {
  return (
    <ResultsErrorBoundary onReset={props.onReset}>
      <ResultsPageInner {...props} />
    </ResultsErrorBoundary>
  );
}
