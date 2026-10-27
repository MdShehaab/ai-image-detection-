/**
 * ReferenceCheckCard.jsx
 * ─────────────────────
 * Displays the reference_check block returned by /api/detect/image.
 * - Shows verdict badge (MATCHES / MODIFIED / NO REGISTRY MATCH)
 * - If MODIFIED: overlays changed-region bounding boxes on the image preview
 * - "Register as original" button with confirmation dialog
 */
import React, { useRef, useEffect, useState } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  ShieldOff,
  BookMarked,
  X,
  AlertTriangle,
  CheckCircle2,
  Info,
  Loader2,
} from 'lucide-react';
import { registerOriginal } from '../services/api';

// ─── colour tokens ──────────────────────────────────────────
const C = {
  teal:   '#4FD6C4',
  green:  '#6FCF97',
  orange: '#E8603C',
  amber:  'rgb(251 191 36)',   // amber-400
  dim:    '#8B93A3',
  card:   '#1C2029',
  border: '#2A2F3A',
  bg:     '#14171C',
  text:   '#E7E9EC',
};

// ─── Helper: human-readable date ────────────────────────────
function fmtDate(epoch) {
  if (!epoch) return '—';
  return new Date(epoch * 1000).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

// ─── Confirmation dialog ─────────────────────────────────────
function ConfirmDialog({ onConfirm, onCancel, isLoading, done }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(20,23,28,0.85)', backdropFilter: 'blur(4px)' }}
    >
      <div
        className="w-full max-w-sm mx-4 rounded-2xl border p-6 shadow-2xl space-y-4 animate-fade-in"
        style={{ background: C.card, borderColor: C.border }}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <BookMarked className="w-4 h-4" style={{ color: C.teal }} />
            <span className="font-mono font-bold text-sm" style={{ color: C.text }}>
              Register as Original
            </span>
          </div>
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="p-1 rounded hover:bg-white/5 transition-colors"
            style={{ color: C.dim }}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {done ? (
          <div className="flex flex-col items-center gap-3 py-4">
            <CheckCircle2 className="w-10 h-10" style={{ color: C.green }} />
            <p className="text-sm font-mono text-center" style={{ color: C.text }}>
              Registered successfully.
            </p>
            <p className="text-xs font-mono text-center" style={{ color: C.dim }}>
              Future uploads of this image will be compared against this original.
            </p>
            <button
              onClick={onCancel}
              className="mt-2 px-4 py-1.5 rounded-lg text-xs font-mono font-semibold"
              style={{ background: C.teal, color: C.bg }}
            >
              Close
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm font-sans leading-relaxed" style={{ color: C.dim }}>
              You are confirming that this image is an{' '}
              <span style={{ color: C.text }} className="font-semibold">unedited original</span>.
              It will be stored in the reference registry and used to detect modifications in
              future uploads of the same photo.
            </p>

            <div
              className="p-3 rounded-lg border text-xs font-mono leading-relaxed"
              style={{ background: C.bg, borderColor: '#E8603C44', color: '#E8603C' }}
            >
              <Info className="w-3.5 h-3.5 inline mr-1.5 -mt-0.5" />
              Only register photos you own and confirm as authentic. Registering
              an edited photo as an original will produce misleading results.
            </div>

            <div className="flex gap-3 pt-1">
              <button
                onClick={onCancel}
                disabled={isLoading}
                className="flex-1 py-2.5 rounded-lg text-xs font-mono border transition-colors hover:bg-white/5"
                style={{ borderColor: C.border, color: C.dim }}
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                disabled={isLoading}
                className="flex-1 py-2.5 rounded-lg text-xs font-mono font-semibold flex items-center justify-center gap-2 transition-colors"
                style={{ background: C.teal, color: C.bg, opacity: isLoading ? 0.7 : 1 }}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Registering…
                  </>
                ) : (
                  <>
                    <BookMarked className="w-3.5 h-3.5" />
                    Confirm & Register
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── Bounding-box overlay canvas ─────────────────────────────
function RegionOverlay({ regions, imgRef }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const img    = imgRef.current;
    if (!canvas || !img || !regions?.length) return;

    const draw = () => {
      const rect = img.getBoundingClientRect();
      const parentRect = img.parentElement.getBoundingClientRect();
      canvas.width  = rect.width;
      canvas.height = rect.height;
      canvas.style.left = `${rect.left - parentRect.left}px`;
      canvas.style.top  = `${rect.top  - parentRect.top}px`;

      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      regions.forEach((r, i) => {
        const x = r.x * rect.width;
        const y = r.y * rect.height;
        const w = r.width  * rect.width;
        const h = r.height * rect.height;

        // Semi-transparent fill
        ctx.fillStyle = 'rgba(232,96,60,0.18)';
        ctx.fillRect(x, y, w, h);

        // Stroke
        ctx.strokeStyle = '#E8603C';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);

        // Label
        ctx.fillStyle = '#E8603C';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(`REGION ${i + 1}`, x + 4, y + 13);
      });
    };

    // Draw immediately and re-draw on resize
    if (img.complete) { draw(); } else { img.onload = draw; }
    const ro = new ResizeObserver(draw);
    ro.observe(img);
    return () => ro.disconnect();
  }, [regions, imgRef]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute pointer-events-none"
      style={{ zIndex: 10 }}
    />
  );
}


// ─── Main card ───────────────────────────────────────────────
export default function ReferenceCheckCard({ referenceCheck, fileInfo, scanFile }) {
  const imgRef = useRef(null);
  const [showConfirm, setShowConfirm]   = useState(false);
  const [registering, setRegistering]   = useState(false);
  const [registerDone, setRegisterDone] = useState(false);
  const [registerErr,  setRegisterErr]  = useState(null);

  if (!referenceCheck) return null;

  const { matched, verdict, sub_label, original_id, original_filename,
          changed_area_pct, largest_region_pct, regions = [] } = referenceCheck;

  // ── Derive display state ──────────────────────────────────
  const isMatches  = matched && verdict === 'REAL';
  const isModified = matched && verdict === 'AI-MODIFIED';
  const noMatch    = !matched;

  const VerdictIcon = isMatches ? ShieldCheck : isModified ? ShieldAlert : ShieldOff;
  const verdictColor = isMatches ? C.green : isModified ? C.orange : C.dim;
  const verdictBg    = isMatches ? '#6FCF9715' : isModified ? '#E8603C15' : '#8B93A315';
  const verdictBorder= isMatches ? '#6FCF9744' : isModified ? '#E8603C44' : '#2A2F3A';

  const verdictLabel = isMatches
    ? 'REAL — REGISTERED ORIGINAL'
    : isModified
    ? 'AI-MODIFIED — DIFFERS FROM REGISTERED ORIGINAL'
    : 'NO REGISTRY MATCH';

  // ── Register handler ──────────────────────────────────────
  const handleRegisterConfirm = async () => {
    if (!scanFile) { setRegisterErr('No file available to register.'); return; }
    setRegistering(true);
    setRegisterErr(null);
    try {
      await registerOriginal(scanFile);
      setRegisterDone(true);
    } catch (err) {
      setRegisterErr(err?.response?.data?.error || err.message || 'Registration failed.');
    } finally {
      setRegistering(false);
    }
  };

  return (
    <>
      {showConfirm && (
        <ConfirmDialog
          onConfirm={handleRegisterConfirm}
          onCancel={() => { setShowConfirm(false); setRegisterDone(false); setRegisterErr(null); }}
          isLoading={registering}
          done={registerDone}
        />
      )}

      <div
        className="lab-card rounded-xl p-6 border space-y-4 animate-fade-slide-up"
        style={{ borderColor: C.border }}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: C.border }}>
          <div className="flex items-center gap-2">
            <BookMarked className="w-4 h-4" style={{ color: C.teal }} />
            <h3 className="font-display font-bold text-sm" style={{ color: C.text }}>
              Reference Check
            </h3>
          </div>
          <span className="text-[10px] font-mono" style={{ color: C.dim }}>
            REGISTRY_COMPARE
          </span>
        </div>

        {/* ── Verdict badge ── */}
        <div
          className="flex items-center gap-3 px-4 py-3 rounded-lg border"
          style={{ background: verdictBg, borderColor: verdictBorder }}
        >
          <VerdictIcon className="w-5 h-5 shrink-0" style={{ color: verdictColor }} />
          <div className="min-w-0">
            <p className="font-mono font-bold text-sm" style={{ color: verdictColor }}>
              {verdictLabel}
            </p>
            {matched && original_filename && (
              <p className="text-[11px] font-mono mt-0.5 truncate" style={{ color: C.dim }}>
                vs. {original_filename}
              </p>
            )}
          </div>
          {matched && changed_area_pct !== null && (
            <div className="ml-auto text-right shrink-0 space-y-0.5">
              <div>
                <p className="font-mono font-bold text-base" style={{ color: isModified ? C.orange : C.green }}>
                  {changed_area_pct.toFixed(3)}%
                </p>
                <p className="text-[10px] font-mono" style={{ color: C.dim }}>changed area</p>
              </div>
              {largest_region_pct != null && largest_region_pct > 0 && (
                <div>
                  <p className="font-mono font-bold text-sm" style={{ color: isModified ? C.orange : C.green }}>
                    {largest_region_pct.toFixed(3)}%
                  </p>
                  <p className="text-[10px] font-mono" style={{ color: C.dim }}>largest region</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Human-readable explanation ── */}
        {isModified && (
          <div
            className="flex gap-2.5 p-3.5 rounded-lg border text-sm font-sans leading-relaxed"
            style={{ background: '#E8603C0D', borderColor: '#E8603C33', color: '#E7E9EC' }}
          >
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" style={{ color: C.orange }} />
            <p>
              {sub_label ||
                'This image differs from a registered original. The system cannot tell whether the edit was made with AI or manually.'}
            </p>
          </div>
        )}
        {isMatches && (
          <p className="text-sm font-sans leading-relaxed" style={{ color: C.dim }}>
            {sub_label || 'The uploaded image is consistent with the registered original. Minor JPEG recompression and resizing artefacts have been ignored.'}
          </p>
        )}
        {noMatch && (
          <p className="text-sm font-sans leading-relaxed" style={{ color: C.dim }}>
            No registered original found for this image. Register it below if you believe it is
            an authentic, unedited photo.
          </p>
        )}

        {/* ── Image with region overlay ── */}
        {isModified && fileInfo?.previewUrl && regions.length > 0 && (
          <div className="space-y-2">
            <p className="text-[11px] font-mono uppercase tracking-wider" style={{ color: C.dim }}>
              Changed Regions
            </p>
            <div
              className="relative rounded-lg overflow-hidden border flex items-center justify-center"
              style={{ background: C.bg, borderColor: C.border, minHeight: 160 }}
            >
              <img
                ref={imgRef}
                src={fileInfo.previewUrl}
                alt="Analyzed image with change regions"
                className="max-h-72 object-contain z-0"
                style={{ display: 'block' }}
              />
              <RegionOverlay regions={regions} imgRef={imgRef} />
            </div>

            {/* Region table */}
            <div className="space-y-1">
              {regions.map((r, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between px-3 py-1.5 rounded text-[11px] font-mono"
                  style={{ background: '#E8603C10', color: C.dim }}
                >
                  <span style={{ color: C.orange }}>REGION {i + 1}</span>
                  <span>
                    {Math.round(r.width * 100)}% × {Math.round(r.height * 100)}%
                    {' '}at ({Math.round(r.x * 100)}%, {Math.round(r.y * 100)}%)
                  </span>
                  <span style={{ color: C.text }}>{r.area_px?.toLocaleString() ?? '—'} px²</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Register as original button ── */}
        {!registerDone && (
          <div className="flex items-center gap-3 pt-1">
            <button
              id="btn-register-as-original"
              onClick={() => setShowConfirm(true)}
              className="btn-tactile flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-semibold border transition-colors hover:bg-white/5"
              style={{ borderColor: C.teal + '88', color: C.teal }}
            >
              <BookMarked className="w-3.5 h-3.5" />
              Register as original
            </button>
            {registerErr && (
              <p className="text-xs font-mono" style={{ color: C.orange }}>{registerErr}</p>
            )}
          </div>
        )}
        {registerDone && (
          <div className="flex items-center gap-2 text-xs font-mono" style={{ color: C.green }}>
            <CheckCircle2 className="w-3.5 h-3.5" />
            Registered in the reference registry.
          </div>
        )}
      </div>
    </>
  );
}
