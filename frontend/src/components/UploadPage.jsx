import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  Image as ImageIcon, 
  Video as VideoIcon, 
  FileText, 
  AlertCircle, 
  FileCheck, 
  X, 
  Sparkles,
  Terminal,
  Crosshair,
  Loader2
} from 'lucide-react';
import { runAuthenticityCheck } from '../services/api';
import ScanBeam from './ScanBeam';

export default function UploadPage({ selectedModule = 'auto', onScanComplete }) {
  const [activeModule, setActiveModule] = useState(selectedModule || 'auto');
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [detectedType, setDetectedType] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  
  const fileInputRef = useRef(null);

  const detectFileType = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    if (['png', 'jpg', 'jpeg', 'webp', 'bmp'].includes(ext)) return 'image';
    if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext)) return 'video';
    if (['pdf', 'tiff'].includes(ext)) return 'document';
    return 'unknown';
  };

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    setErrorMsg(null);
    setFile(selectedFile);
    
    const type = detectFileType(selectedFile.name);
    setDetectedType(type);

    if (selectedFile.type.startsWith('image/')) {
      const url = URL.createObjectURL(selectedFile);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleRunDetection = async () => {
    if (!file) {
      setErrorMsg("Please select or drop a target media artifact first.");
      return;
    }

    setIsScanning(true);
    setUploadProgress(15);
    setErrorMsg(null);

    try {
      const moduleToUse = activeModule === 'auto' ? 'auto' : activeModule;
      
      const response = await runAuthenticityCheck(file, moduleToUse, (percent) => {
        setUploadProgress(percent);
      });

      onScanComplete({
        result: response,
        fileInfo: {
          name: file.name,
          size: file.size,
          type: detectedType || 'image',
          previewUrl: previewUrl,
        }
      });
    } catch (err) {
      console.error("Detection error:", err);
      const errMsg = err.response?.data?.error || err.message || "Forensic inference pipeline encountered an error.";
      setErrorMsg(errMsg);
    } finally {
      setIsScanning(false);
    }
  };

  const loadSampleFile = (sampleType) => {
    setErrorMsg(null);
    let sampleBlob;
    let fileName;

    if (sampleType === 'image') {
      fileName = 'sample_portrait_synthetic.png';
      sampleBlob = new Blob(['SAMPLE_IMAGE_DATA_BLOB'], { type: 'image/png' });
    } else if (sampleType === 'video') {
      fileName = 'sample_speech_interp.mp4';
      sampleBlob = new Blob(['SAMPLE_VIDEO_DATA_BLOB'], { type: 'video/mp4' });
    } else {
      fileName = 'sample_altered_invoice_300dpi.pdf';
      sampleBlob = new Blob(['%PDF-1.4 SAMPLE_PDF_BLOB'], { type: 'application/pdf' });
    }

    const sampleFile = new File([sampleBlob], fileName, { type: sampleBlob.type });
    setFile(sampleFile);
    setDetectedType(sampleType);
    setPreviewUrl(null);
  };

  const clearFile = () => {
    setFile(null);
    setPreviewUrl(null);
    setDetectedType(null);
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const getEffectiveModule = () => {
    if (activeModule !== 'auto') return activeModule;
    if (detectedType && detectedType !== 'unknown') return detectedType;
    return 'image';
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      
      {/* Title & Terminal Header */}
      <div className="mb-8 text-left border-b border-[#2A2F3A] pb-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#4FD6C4] mb-1">
          <Crosshair className="w-3.5 h-3.5" />
          <span>TERMINAL_02 // INGESTION_PIPELINE</span>
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-[#E7E9EC]">
          Forensic Artifact Ingestion
        </h1>
        <p className="text-xs font-mono text-[#8B93A3] mt-1">
          MOUNT PAYLOAD TO RUN SPECTRAL FREQUENCY, TEMPORAL, OR DOCUMENT LAYOUT FORENSICS
        </p>
      </div>

      {/* Module Selector Tabs */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <button
          onClick={() => setActiveModule('auto')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-mono transition-all ${
            activeModule === 'auto'
              ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4] font-semibold'
              : 'bg-[#14171C] text-[#8B93A3] hover:text-[#E7E9EC] border border-[#2A2F3A]'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-[#4FD6C4]" />
          <span>AUTO_DISPATCH</span>
        </button>

        <button
          onClick={() => setActiveModule('image')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-mono transition-all ${
            activeModule === 'image'
              ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4] font-semibold'
              : 'bg-[#14171C] text-[#8B93A3] hover:text-[#E7E9EC] border border-[#2A2F3A]'
          }`}
        >
          <ImageIcon className="w-3.5 h-3.5" />
          <span>01 // IMAGE</span>
        </button>

        <button
          onClick={() => setActiveModule('video')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-mono transition-all ${
            activeModule === 'video'
              ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4] font-semibold'
              : 'bg-[#14171C] text-[#8B93A3] hover:text-[#E7E9EC] border border-[#2A2F3A]'
          }`}
        >
          <VideoIcon className="w-3.5 h-3.5" />
          <span>02 // VIDEO</span>
        </button>

        <button
          onClick={() => setActiveModule('document')}
          className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-mono transition-all ${
            activeModule === 'document'
              ? 'bg-[#1C2029] text-[#4FD6C4] border border-[#4FD6C4] font-semibold'
              : 'bg-[#14171C] text-[#8B93A3] hover:text-[#E7E9EC] border border-[#2A2F3A]'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>03 // DOCUMENT</span>
        </button>
      </div>

      {/* Main Drag & Drop Zone */}
      <div className="lab-card rounded-xl p-6 sm:p-8 border border-[#2A2F3A] relative">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
          accept="image/*,video/*,.pdf,.tiff"
        />

        {!file ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && fileInputRef.current?.click()}
            className={`relative border-2 border-dashed rounded-lg p-10 sm:p-14 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center space-y-4 overflow-hidden ${
              isDragging
                ? 'border-[#4FD6C4] bg-[#14171C] scale-[1.005]'
                : 'border-[#2A2F3A] hover:border-[#4FD6C4]/60 bg-[#12151A]'
            }`}
          >
            {/* Subtle grid pattern overlay */}
            <div className="absolute inset-0 static-grid-overlay opacity-40" />

            <div className="w-12 h-12 rounded-lg bg-[#1C2029] border border-[#2A2F3A] flex items-center justify-center text-[#4FD6C4] relative z-10">
              <UploadCloud className="w-6 h-6" />
            </div>

            <div className="relative z-10 space-y-1">
              <p className="text-sm font-display font-bold text-[#E7E9EC]">
                DROP TARGET ARTIFACT HERE, OR <span className="text-[#4FD6C4] underline">SELECT FILE</span>
              </p>
              <p className="text-xs font-mono text-[#8B93A3]">
                SUPPORTS: PNG, JPG, WEBP, MP4, AVI, MOV, PDF, TIFF (UP TO 64MB)
              </p>
            </div>

            {/* Corner Crosshair Markings */}
            <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-[#4FD6C4]/40" />
            <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-[#4FD6C4]/40" />
            <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-[#4FD6C4]/40" />
            <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-[#4FD6C4]/40" />
          </div>
        ) : (
          /* File Ingested State & Ingestion Monitor */
          <div className="space-y-6">
            
            {/* File Info Bar */}
            <div className="p-4 rounded-lg bg-[#12151A] border border-[#2A2F3A] flex items-start justify-between">
              <div className="flex items-center space-x-3.5">
                <div className="w-10 h-10 rounded-lg bg-[#1C2029] border border-[#2A2F3A] flex items-center justify-center text-[#4FD6C4] shrink-0">
                  {detectedType === 'image' && <ImageIcon className="w-5 h-5" />}
                  {detectedType === 'video' && <VideoIcon className="w-5 h-5" />}
                  {detectedType === 'document' && <FileText className="w-5 h-5" />}
                  {(!detectedType || detectedType === 'unknown') && <FileCheck className="w-5 h-5" />}
                </div>

                <div>
                  <h4 className="text-xs font-mono font-bold text-[#E7E9EC] truncate max-w-sm sm:max-w-md">
                    {file.name}
                  </h4>
                  <div className="flex items-center space-x-3 text-[11px] font-mono text-[#8B93A3] mt-0.5">
                    <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                    <span>//</span>
                    <span className="text-[#4FD6C4] uppercase">
                      {detectedType ? `${detectedType}` : 'UNKNOWN'}
                    </span>
                    <span>//</span>
                    <span>PIPELINE: {getEffectiveModule().toUpperCase()}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={clearFile}
                disabled={isScanning}
                className="text-[#8B93A3] hover:text-[#E8603C] p-1.5 rounded hover:bg-[#1C2029] transition-colors focus-visible:outline-none"
                title="Unload file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Media Preview Container with Live Scan Beam Active during Ingestion / Processing */}
            <div className="relative rounded-lg bg-[#12151A] border border-[#2A2F3A] overflow-hidden min-h-[160px] flex items-center justify-center">
              {previewUrl ? (
                <img 
                  src={previewUrl} 
                  alt="Ingested artifact" 
                  className="max-h-60 rounded object-contain p-2" 
                />
              ) : (
                <div className="text-center p-8 space-y-2">
                  <FileCheck className="w-8 h-8 text-[#4FD6C4] mx-auto opacity-70" />
                  <p className="text-xs font-mono text-[#8B93A3]">
                    ARTIFACT BUFFERED IN MEMORY // READY FOR NEURAL INFERENCE
                  </p>
                </div>
              )}

              {/* SIGNATURE SCAN BEAM: ACTIVE WHEN IS SCANNING / PROCESSING */}
              <ScanBeam 
                isActive={isScanning} 
                showGrid={true}
                label={isScanning ? "INFERENCE_SWEEP_ACTIVE" : null}
              />
            </div>

            {/* Execution Trigger Button */}
            <button
              onClick={handleRunDetection}
              disabled={isScanning}
              className={`w-full py-3.5 rounded-lg font-mono font-semibold text-xs tracking-wider uppercase transition-all shadow-sm flex items-center justify-center space-x-2 focus-visible:ring-2 focus-visible:ring-[#4FD6C4] ${
                isScanning
                  ? 'bg-[#1C2029] text-[#8B93A3] cursor-not-allowed border border-[#2A2F3A]'
                  : 'bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C]'
              }`}
            >
              {isScanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#4FD6C4]" />
                  <span>RUNNING FORENSIC INFERENCE... ({uploadProgress}%)</span>
                </>
              ) : (
                <>
                  <Crosshair className="w-4 h-4" />
                  <span>EXECUTE FORENSIC ANALYSIS</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="mt-4 p-3.5 rounded-lg bg-[#14171C] border border-[#E8603C]/60 text-[#E8603C] text-xs font-mono flex items-start space-x-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>ERROR // {errorMsg}</span>
          </div>
        )}

        {/* Sample Artifact Test Matrix */}
        <div className="mt-8 pt-6 border-t border-[#2A2F3A]">
          <div className="text-[10px] font-mono text-[#8B93A3] uppercase tracking-wider mb-3">
            // SIMULATED TEST ARTIFACTS
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={() => loadSampleFile('image')}
              className="p-3 rounded-lg bg-[#14171C] hover:bg-[#1C2029] border border-[#2A2F3A] text-left text-xs transition-colors flex items-center space-x-3 group"
            >
              <ImageIcon className="w-4 h-4 text-[#4FD6C4] shrink-0" />
              <div>
                <div className="font-mono font-semibold text-[#E7E9EC] text-[11px]">DEEPFAKE_FACE</div>
                <div className="text-[10px] text-[#8B93A3] font-mono">portrait_synthetic.png</div>
              </div>
            </button>

            <button
              onClick={() => loadSampleFile('video')}
              className="p-3 rounded-lg bg-[#14171C] hover:bg-[#1C2029] border border-[#2A2F3A] text-left text-xs transition-colors flex items-center space-x-3 group"
            >
              <VideoIcon className="w-4 h-4 text-[#4FD6C4] shrink-0" />
              <div>
                <div className="font-mono font-semibold text-[#E7E9EC] text-[11px]">SYNTHETIC_SPEECH</div>
                <div className="text-[10px] text-[#8B93A3] font-mono">speech_interp.mp4</div>
              </div>
            </button>

            <button
              onClick={() => loadSampleFile('document')}
              className="p-3 rounded-lg bg-[#14171C] hover:bg-[#1C2029] border border-[#2A2F3A] text-left text-xs transition-colors flex items-center space-x-3 group"
            >
              <FileText className="w-4 h-4 text-[#4FD6C4] shrink-0" />
              <div>
                <div className="font-mono font-semibold text-[#E7E9EC] text-[11px]">ALTERED_INVOICE</div>
                <div className="text-[10px] text-[#8B93A3] font-mono">invoice_300dpi.pdf</div>
              </div>
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
