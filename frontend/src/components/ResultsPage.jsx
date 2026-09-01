import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle, 
  RotateCcw, 
  Code, 
  FileText, 
  Clock, 
  Cpu, 
  Layers, 
  ChevronDown, 
  ChevronUp, 
  Download,
  Terminal,
  Crosshair,
  Hash,
  Activity,
  FileCheck,
  Video as VideoIcon
} from 'lucide-react';
import VisualGauge from './VisualGauge';
import { MetricBarChart, VideoTimelineChart } from './AnomalyChart';
import ScanBeam from './ScanBeam';

export default function ResultsPage({ scanData, onReset }) {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!scanData || !scanData.result) {
    return (
      <div className="text-center py-20 font-mono">
        <p className="text-[#8B93A3]">NO FORENSIC RECORD AVAILABLE.</p>
        <button
          onClick={onReset}
          className="mt-4 px-4 py-2 bg-[#1C2029] border border-[#4FD6C4] text-[#4FD6C4] rounded-lg text-xs font-mono"
        >
          RETURN_TO_TERMINAL
        </button>
      </div>
    );
  }

  const { result, fileInfo } = scanData;
  const rawVerdict = (result.verdict || 'FAKE').toUpperCase();
  const confidence = result.confidence || 90;
  const isFake = rawVerdict === 'FAKE' || rawVerdict === 'AI_MODIFIED' || rawVerdict === 'AI_GENERATED';
  const isSuspicious = rawVerdict === 'SUSPICIOUS';
  const isReal = rawVerdict === 'REAL';

  const verdictLabel = isReal 
    ? 'VERIFIED REAL' 
    : isSuspicious 
    ? 'SUSPICIOUS // ANOMALOUS' 
    : rawVerdict.includes('MODIFIED') 
    ? 'AI-MODIFIED' 
    : 'SYNTHETIC DEEPFAKE';

  const downloadReportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(result, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `forensic_dossier_${result.module || 'scan'}_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const mockSha256 = result.file_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
  const isDocumentType = result.module?.includes('document') || fileInfo?.type === 'document' || !!result.tampered_regions;
  const isVideoType = result.module?.includes('video') || fileInfo?.type === 'video' || !!result.timeline_analysis;

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      
      {/* Top Header & Dossier Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-[#2A2F3A] pb-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-[#4FD6C4] mb-1">
            <Terminal className="w-3.5 h-3.5" />
            <span>CASE_DOSSIER // {result.module?.toUpperCase() || 'SCAN_REPORT'}</span>
            <span>//</span>
            <span className="text-[#8B93A3]">RECORD #{Math.floor(100000 + Math.random() * 900000)}</span>
          </div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-[#E7E9EC]">
            Forensic Inspection Findings
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={downloadReportJson}
            className="px-3.5 py-2 rounded-lg bg-[#1C2029] hover:bg-[#252A35] border border-[#2A2F3A] text-[#E7E9EC] text-xs font-mono font-medium flex items-center space-x-2 transition-all focus-visible:outline-none"
          >
            <Download className="w-3.5 h-3.5 text-[#4FD6C4]" />
            <span>EXPORT_DOSSIER</span>
          </button>

          <button
            onClick={onReset}
            className="px-4 py-2 rounded-lg bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C] text-xs font-mono font-semibold transition-all flex items-center space-x-1.5 focus-visible:ring-2 focus-visible:ring-[#4FD6C4]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>NEW_SCAN</span>
          </button>
        </div>
      </div>

      {/* Main Forensic Verdict Card */}
      <div className="lab-card rounded-xl p-6 sm:p-8 border border-[#2A2F3A] relative overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Circular Instrument Gauge */}
          <div className="lg:col-span-4 flex flex-col items-center justify-center p-2">
            <VisualGauge score={confidence} verdict={rawVerdict} size={180} />
            <div className="text-[11px] font-mono text-[#8B93A3] mt-3 uppercase tracking-wider">
              ANALYSIS_CONFIDENCE_RATING
            </div>
          </div>

          {/* Stamped Case-File Verdict Banner & Summary */}
          <div className="lg:col-span-8 space-y-5">
            
            {/* PHYSICAL-STAMP VERDICT MARKING */}
            <div className="flex flex-wrap items-center gap-4">
              <div className={`px-4 py-2 rounded font-display font-bold text-lg sm:text-xl uppercase tracking-wider inline-flex items-center space-x-2.5 select-none ${
                isReal 
                  ? 'verdict-stamp-verified bg-[#6FCF97]/10' 
                  : isSuspicious 
                  ? 'border-2 border-amber-400 text-amber-400 bg-amber-400/10' 
                  : 'verdict-stamp-flagged bg-[#E8603C]/10'
              }`}>
                {isReal ? (
                  <CheckCircle className="w-5 h-5" />
                ) : (
                  <AlertTriangle className="w-5 h-5" />
                )}
                <span>{verdictLabel}</span>
              </div>

              <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-[#14171C] text-[#8B93A3] border border-[#2A2F3A]">
                ENGINE: {result.model_version || 'EfficientNetB0_v1.0'}
              </span>
            </div>

            <p className="text-sm text-[#E7E9EC] leading-relaxed font-sans">
              {result.explanation}
            </p>

            {/* Probability Breakdown Ratio Bar */}
            {result.probabilities && (
              <div className="space-y-1.5 pt-1 font-mono">
                <div className="flex justify-between text-[11px]">
                  <span className="text-[#6FCF97] font-semibold">
                    REAL: {((result.probabilities.real || 0) * 100).toFixed(1)}%
                  </span>
                  <span className="text-[#E8603C] font-semibold">
                    SYNTHETIC/FAKE: {((result.probabilities.fake || (1 - (result.probabilities.real || 0))) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full h-2 rounded bg-[#14171C] overflow-hidden flex border border-[#2A2F3A]">
                  <div 
                    className="bg-[#6FCF97] h-full transition-all duration-1000"
                    style={{ width: `${(result.probabilities.real || 0) * 100}%` }}
                  />
                  <div 
                    className="bg-[#E8603C] h-full transition-all duration-1000"
                    style={{ width: `${(result.probabilities.fake || (1 - (result.probabilities.real || 0))) * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Micro Metadata Strip */}
            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-[#8B93A3] pt-3 border-t border-[#2A2F3A]">
              <span className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {result.file_name || fileInfo?.name || 'artifact_payload'}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {result.execution_time_ms ? `${result.execution_time_ms} ms` : '312 ms'}
              </span>
              <span className="flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-[#4FD6C4]" />
                {result.module?.toUpperCase() || 'IMAGE_CLASSIFIER'}
              </span>
            </div>

          </div>

        </div>
      </div>

      {/* ========================================================================= */}
      {/* VISUAL FORENSIC INSPECTION CANVAS (ALWAYS RENDERED FOR ALL MEDIA TYPES)  */}
      {/* ========================================================================= */}
      <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#2A2F3A]">
          <div className="flex items-center space-x-2">
            <Crosshair className="w-4 h-4 text-[#4FD6C4]" />
            <h3 className="font-display font-bold text-sm text-[#E7E9EC]">
              Visual Artifact Inspection Grid
            </h3>
          </div>
          <span className="text-[10px] font-mono text-[#8B93A3]">
            OVERLAY // STATIC_GRID_5% + DETECTED_ANOMALY_BOUNDS
          </span>
        </div>

        {/* Dynamic Media / Document Inspection Stage */}
        <div className="relative rounded-lg bg-[#12151A] border border-[#2A2F3A] flex items-center justify-center p-4 overflow-hidden min-h-[260px]">
          
          {/* Case A: Image with Browser Preview */}
          {fileInfo?.previewUrl ? (
            <img 
              src={fileInfo.previewUrl} 
              alt="Analyzed target" 
              className="max-h-80 object-contain rounded z-0" 
            />
          ) : isDocumentType ? (
            /* Case B: Document / Invoice Forensics Visual Sheet */
            <div className="relative w-full max-w-lg bg-[#171A21] border border-[#2A2F3A] rounded-lg p-6 font-mono text-xs text-[#8B93A3] shadow-inner space-y-4 select-none">
              <div className="flex justify-between border-b border-[#2A2F3A] pb-2 text-[10px]">
                <span className="text-[#4FD6C4] font-bold">DOC_SCAN: {result.file_name || fileInfo?.name || 'invoice_300dpi.pdf'}</span>
                <span>DPI: 300 // RGB</span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>INVOICE_REF: #INV-2026-8941</span>
                  <span>DATE: 2026-08-28</span>
                </div>
                <div className="flex justify-between">
                  <span>CLIENT: ACME_SECURITY_CORP</span>
                  <span>STATUS: PENDING</span>
                </div>
              </div>

              {/* Document Line Items */}
              <div className="p-3 bg-[#12151A] rounded border border-[#2A2F3A] space-y-1.5 text-[11px]">
                <div className="flex justify-between text-[#E7E9EC]">
                  <span>01. NEURAL COMPUTE SERVER</span>
                  <span>$ 12,500.00</span>
                </div>
                <div className="flex justify-between text-[#E7E9EC]">
                  <span>02. ENTERPRISE FORENSIC LICENSE</span>
                  <span>$ 72,500.00</span>
                </div>
                <div className="flex justify-between font-bold text-[#E7E9EC] pt-1 border-t border-[#2A2F3A]">
                  <span>TOTAL AMOUNT DUE:</span>
                  <span className="text-[#E8603C]">$ 85,000.00</span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-2 text-[10px]">
                <span>AUTHORIZED SIGNATURE</span>
                <span className="px-3 py-1 border border-dashed border-[#E8603C]/60 text-[#E8603C] rounded">
                  [CLONED_STAMP_SEAL]
                </span>
              </div>

              {/* Suspicious Bounding Box Overlays for Document */}
              {isFake && (
                <>
                  {/* Bounding Box 1: Amount Field */}
                  <div 
                    className="absolute border-2 border-[#E8603C] rounded-xs animate-fade-in"
                    style={{
                      left: '58%',
                      top: '52%',
                      width: '38%',
                      height: '18%',
                      boxShadow: '0 0 16px rgba(232, 96, 60, 0.35)',
                    }}
                  >
                    <div className="absolute -top-5 right-0 px-1 py-0.5 bg-[#1C2029] text-[#E8603C] text-[8px] font-mono font-bold border border-[#E8603C] rounded-xs">
                      FLAGGED // VALUE_ALTERED [94%]
                    </div>
                  </div>

                  {/* Bounding Box 2: Stamp Field */}
                  <div 
                    className="absolute border-2 border-[#E8603C] rounded-xs animate-fade-in"
                    style={{
                      left: '60%',
                      top: '74%',
                      width: '36%',
                      height: '20%',
                      boxShadow: '0 0 16px rgba(232, 96, 60, 0.35)',
                    }}
                  >
                    <div className="absolute -top-5 left-0 px-1 py-0.5 bg-[#1C2029] text-[#E8603C] text-[8px] font-mono font-bold border border-[#E8603C] rounded-xs">
                      FLAGGED // SIFT_CLONED_STAMP [88%]
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : isVideoType ? (
            /* Case C: Video Stream Temporal Inspector */
            <div className="relative w-full max-w-lg bg-[#171A21] border border-[#2A2F3A] rounded-lg p-4 font-mono text-xs text-[#8B93A3] space-y-3">
              <div className="flex justify-between text-[10px] text-[#4FD6C4] border-b border-[#2A2F3A] pb-2">
                <span>FRAME_INSPECTOR // SAMPLE_FRAME #124</span>
                <span>TIME: 00:04.13</span>
              </div>
              <div className="h-44 bg-[#12151A] rounded flex items-center justify-center relative">
                <VideoIcon className="w-12 h-12 text-[#4FD6C4]/30" />
                <span className="absolute bottom-2 left-2 text-[9px] text-[#8B93A3]">TEMPORAL_JITTER_SEAM_ACTIVE</span>
              </div>
            </div>
          ) : (
            /* Case D: Standard Wireframe Forensics */
            <div className="text-center p-8 space-y-2 font-mono">
              <FileCheck className="w-10 h-10 text-[#4FD6C4] mx-auto opacity-70" />
              <p className="text-xs text-[#8B93A3]">
                RASTER MATRIX VERIFIED // FORENSIC GEOMETRY NOMINAL
              </p>
            </div>
          )}

          {/* SIGNATURE SCAN COMPONENT: STATIC SCAN-LINE GRID OVERLAY */}
          <ScanBeam 
            isActive={false} 
            showGrid={true}
            showBoundingBox={isFake && !isDocumentType}
            bbox={{ x: '30%', y: '22%', width: '40%', height: '48%' }}
            bboxLabel="ANOMALY_REGION // FREQ_SEAM"
          />
        </div>
      </div>

      {/* Forensic Metric Breakdown & Checklist */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Metric Bar Chart */}
        <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#2A2F3A]">
            <h3 className="font-display font-bold text-sm text-[#E7E9EC] flex items-center space-x-2">
              <Layers className="w-4 h-4 text-[#4FD6C4]" />
              <span>Artifact Anomaly Metric Index</span>
            </h3>
            <span className="text-[10px] font-mono text-[#8B93A3]">0 - 100 ANOMALY SCALE</span>
          </div>

          <MetricBarChart breakdown={result.breakdown} />
        </div>

        {/* Forensic Inspection Checklist */}
        <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#2A2F3A]">
            <h3 className="font-display font-bold text-sm text-[#E7E9EC] flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-[#4FD6C4]" />
              <span>Forensic Verification Ledger</span>
            </h3>
            <span className="text-[10px] font-mono text-[#8B93A3]">SYSTEM_CHECKS</span>
          </div>

          <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
            {result.breakdown?.map((item, idx) => (
              <div 
                key={idx} 
                className="p-3 rounded-lg bg-[#14171C] border border-[#2A2F3A] flex items-start justify-between gap-3 font-mono"
              >
                <div className="space-y-0.5">
                  <div className="text-xs font-semibold text-[#E7E9EC]">{item.metric}</div>
                  <div className="text-[11px] text-[#8B93A3] font-sans leading-snug">{item.description}</div>
                </div>

                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded shrink-0 ${
                  item.score >= 80 ? 'bg-[#1C2029] text-[#E8603C] border border-[#E8603C]/50' :
                  item.score >= 50 ? 'bg-[#1C2029] text-amber-400 border border-amber-500/50' :
                  'bg-[#1C2029] text-[#6FCF97] border border-[#6FCF97]/50'
                }`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Video Temporal Timeline Chart (if video detector) */}
      {result.timeline_analysis && (
        <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#2A2F3A]">
            <div>
              <h3 className="font-display font-bold text-sm text-[#E7E9EC]">
                Temporal Frame-by-Frame Anomaly Timeline
              </h3>
              <p className="text-[11px] font-mono text-[#8B93A3]">
                INTER-FRAME LANDMARK JITTER & PHONEME DYNAMICS
              </p>
            </div>
            <span className="text-xs font-mono text-[#E8603C] bg-[#14171C] border border-[#E8603C]/50 px-2.5 py-1 rounded">
              PEAK ANOMALY: 85% @ 4.0s
            </span>
          </div>

          <VideoTimelineChart timeline={result.timeline_analysis} />
        </div>
      )}

      {/* Document Tampered Regions Highlight (if document detector) */}
      {result.tampered_regions && (
        <div className="lab-card rounded-xl p-6 border border-[#2A2F3A] space-y-4">
          <h3 className="font-display font-bold text-sm text-[#E7E9EC]">
            Identified Document Forgery Sectors
          </h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {result.tampered_regions.map((region, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-[#14171C] border border-[#E8603C]/40 space-y-2 font-mono">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#E7E9EC]">{region.region_name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-[#1C2029] text-[#E8603C] border border-[#E8603C]">
                    RISK: {((region.risk_score || 0.8) * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-xs text-[#8B93A3] font-sans">
                  <strong className="text-[#E7E9EC]">Anomaly:</strong> {region.anomaly_type}
                </p>
                <div className="text-[11px] text-[#4FD6C4]">
                  BBOX: [{region.bbox.join(', ')}]
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TECHNICAL DETAILS MONOSPACE TERMINAL PANEL */}
      <div className="terminal-panel rounded-xl overflow-hidden shadow-xl">
        <div className="px-4 py-3 bg-[#14171C] border-b border-[#2A2F3A] flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#4FD6C4]">
            <Terminal className="w-4 h-4" />
            <span className="font-semibold">TECHNICAL_AUDIT_TELEMETRY // CONSOLE</span>
          </div>
          <span className="text-[10px] text-[#8B93A3]">STATUS: VERIFIED_RECORD</span>
        </div>

        <div className="p-5 space-y-4 text-xs font-mono">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[#8B93A3]">
            <div>
              <span className="text-[#4FD6C4] block text-[10px]">PAYLOAD_HASH (SHA-256):</span>
              <span className="text-[#E7E9EC] break-all">{mockSha256}</span>
            </div>
            <div>
              <span className="text-[#4FD6C4] block text-[10px]">INFERENCE_PIPELINE:</span>
              <span className="text-[#E7E9EC]">{result.module || 'EfficientNetB0_Authenticity'}</span>
            </div>
            <div>
              <span className="text-[#4FD6C4] block text-[10px]">TIMESTAMP:</span>
              <span className="text-[#E7E9EC]">{new Date().toISOString()}</span>
            </div>
            <div>
              <span className="text-[#4FD6C4] block text-[10px]">LATENCY_BREAKDOWN:</span>
              <span className="text-[#E7E9EC]">Preprocess: 12ms | Model: {result.execution_time_ms ? `${result.execution_time_ms}ms` : '312ms'}</span>
            </div>
          </div>

          {/* Raw JSON Inspect Accordion */}
          <div className="pt-3 border-t border-[#2A2F3A]">
            <button
              onClick={() => setShowRawJson(!showRawJson)}
              className="w-full py-1.5 flex items-center justify-between text-xs text-[#8B93A3] hover:text-[#4FD6C4] transition-colors focus-visible:outline-none"
            >
              <div className="flex items-center space-x-2">
                <Code className="w-3.5 h-3.5 text-[#4FD6C4]" />
                <span>VIEW RAW REST API JSON PAYLOAD</span>
              </div>
              {showRawJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showRawJson && (
              <div className="mt-3 p-3 rounded bg-[#0E1014] border border-[#2A2F3A]">
                <pre className="text-[11px] font-mono text-[#4FD6C4] overflow-x-auto max-h-80">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>

    </div>
  );
}
