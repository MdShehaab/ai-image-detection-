import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  AlertCircle,
  X,
  Crosshair,
  Loader2
} from 'lucide-react';
import { detectImage } from '../services/api';
import ScanBeam from './ScanBeam';
import InfoCapsule from './InfoCapsule';

const ACCEPTED_TYPES = ['jpg', 'jpeg', 'png', 'webp'];
const ACCEPTED_MIME  = ['image/jpeg', 'image/png', 'image/webp'];

export default function UploadPage({ onScanComplete }) {
  const [file, setFile]             = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errorMsg, setErrorMsg]     = useState(null);
  const [fileAnimated, setFileAnimated] = useState(false);
  const [tipsOpen, setTipsOpen]     = useState(false);

  const fileInputRef = useRef(null);

  const isValidType = (f) => {
    const ext  = (f.name || '').split('.').pop().toLowerCase();
    const mime = f.type || '';
    return ACCEPTED_TYPES.includes(ext) || ACCEPTED_MIME.includes(mime);
  };

  const handleFileSelect = (selectedFile) => {
    if (!selectedFile) return;
    setErrorMsg(null);
    setFileAnimated(false);

    if (!isValidType(selectedFile)) {
      setErrorMsg(`Unsupported file type "${selectedFile.name}". Please upload a JPG, JPEG, PNG, or WEBP image.`);
      return;
    }

    setFile(selectedFile);
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
    setTimeout(() => setFileAnimated(true), 30);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.[0]) handleFileSelect(e.dataTransfer.files[0]);
  };

  const clearFile = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(null);
    setPreviewUrl(null);
    setUploadProgress(0);
    setFileAnimated(false);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleRunDetection = async () => {
    if (!file) {
      setErrorMsg('Please select or drop an image first.');
      return;
    }
    setIsScanning(true);
    setUploadProgress(15);
    setErrorMsg(null);

    try {
      const response = await detectImage(file, (pct) => setUploadProgress(pct));
      onScanComplete(
        {
          result: response,
          fileInfo: {
            name: file.name,
            size: file.size,
            type: 'image',
            previewUrl,
          }
        },
        file  // pass raw File so ResultsPage can re-register it
      );
    } catch (err) {
      console.error('Detection error:', err);
      setErrorMsg(err.response?.data?.error || err.message || 'Inference pipeline error. Please try again.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6">

      {/* Page header */}
      <div className="mb-8 border-b border-[#2A2F3A] pb-4">
        <div className="flex items-center space-x-2 text-xs font-mono text-[#4FD6C4] mb-1">
          <Crosshair className="w-3.5 h-3.5" />
          <span>TERMINAL_02 // IMAGE_INGESTION</span>
        </div>
        <h1 className="font-display text-2xl sm:text-3xl font-bold text-[#E7E9EC]">
          Analyze an Image
        </h1>
        <p className="text-xs font-mono text-[#8B93A3] mt-1">
          DROP OR SELECT A JPG, PNG, OR WEBP — RESULTS IN UNDER 350 MS
        </p>
      </div>

      {/* Main card */}
      <div className="lab-card rounded-xl p-6 sm:p-8 border border-[#2A2F3A] relative space-y-6">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
          onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
        />

        {!file ? (
          /* ── Drop zone ── */
          <div
            onDrop={handleDrop}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && fileInputRef.current?.click()}
            aria-label="Upload an image for analysis"
            className={`
              relative border-2 border-dashed rounded-xl p-12 sm:p-16
              text-center cursor-pointer flex flex-col items-center justify-center space-y-4
              overflow-hidden transition-all duration-200
              ${isDragging
                ? 'border-[#4FD6C4] bg-[#14171C] scale-[1.01] animate-drag-pulse'
                : 'border-[#2A2F3A] hover:border-[#4FD6C4]/60 bg-[#12151A]'
              }
            `}
          >
            {/* grid texture */}
            <div className="absolute inset-0 static-grid-overlay opacity-40" />

            {/* Icon */}
            <div className={`
              w-14 h-14 rounded-xl bg-[#1C2029] border flex items-center justify-center text-[#4FD6C4] relative z-10
              transition-all duration-200
              ${isDragging ? 'border-[#4FD6C4] shadow-[0_0_20px_rgba(79,214,196,0.4)]' : 'border-[#2A2F3A]'}
            `}>
              <UploadCloud className={`w-7 h-7 transition-transform duration-200 ${isDragging ? 'scale-110' : ''}`} />
            </div>

            <div className="relative z-10 space-y-1">
              <p className="text-sm font-display font-bold text-[#E7E9EC]">
                Drop image here, or{' '}
                <span className="text-[#4FD6C4] underline underline-offset-2">select file</span>
              </p>
              <p className="text-xs font-mono text-[#8B93A3]">JPG · JPEG · PNG · WEBP</p>
            </div>

            {/* Corner crosshairs */}
            <div className={`absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 transition-all duration-200 ${isDragging ? 'border-[#4FD6C4]' : 'border-[#4FD6C4]/40'}`} />
            <div className={`absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 transition-all duration-200 ${isDragging ? 'border-[#4FD6C4]' : 'border-[#4FD6C4]/40'}`} />
            <div className={`absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 transition-all duration-200 ${isDragging ? 'border-[#4FD6C4]' : 'border-[#4FD6C4]/40'}`} />
            <div className={`absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 transition-all duration-200 ${isDragging ? 'border-[#4FD6C4]' : 'border-[#4FD6C4]/40'}`} />
          </div>
        ) : (
          /* ── File loaded state ── */
          <div className={`space-y-5 ${fileAnimated ? 'animate-fade-slide-up' : 'opacity-0'}`}>

            {/* File info bar */}
            <div className="p-4 rounded-lg bg-[#12151A] border border-[#2A2F3A] flex items-start justify-between">
              <div className="flex items-center space-x-3.5">
                <div className="w-10 h-10 rounded-lg bg-[#1C2029] border border-[#2A2F3A] flex items-center justify-center text-[#4FD6C4] shrink-0">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-mono font-bold text-[#E7E9EC] truncate max-w-xs sm:max-w-md">
                    {file.name}
                  </h4>
                  <div className="flex items-center gap-3 text-[11px] font-mono text-[#8B93A3] mt-0.5">
                    <span>{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                    <span className="text-[#4FD6C4] uppercase">IMAGE</span>
                  </div>
                </div>
              </div>
              <button
                onClick={clearFile}
                disabled={isScanning}
                className="btn-tactile text-[#8B93A3] hover:text-[#E8603C] p-1.5 rounded hover:bg-[#1C2029] transition-colors focus-visible:outline-none"
                title="Remove file"
                aria-label="Remove selected file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Image preview with scan beam during analysis */}
            <div className="relative rounded-lg bg-[#12151A] border border-[#2A2F3A] overflow-hidden min-h-[180px] flex items-center justify-center">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Selected image preview"
                  className="max-h-64 rounded object-contain p-2"
                />
              )}
              {isScanning && <div className="absolute inset-0 skeleton-shimmer rounded-lg" />}
              <ScanBeam
                isActive={isScanning}
                showGrid={true}
                label={isScanning ? 'INFERENCE_SWEEP_ACTIVE' : null}
              />
            </div>

            {/* Analyze button */}
            <button
              onClick={handleRunDetection}
              disabled={isScanning}
              className={`
                btn-tactile btn-teal-glow
                w-full py-3.5 rounded-lg font-mono font-semibold text-xs tracking-wider uppercase
                flex items-center justify-center space-x-2
                focus-visible:ring-2 focus-visible:ring-[#4FD6C4]
                ${isScanning
                  ? 'bg-[#1C2029] text-[#8B93A3] cursor-not-allowed border border-[#2A2F3A]'
                  : 'bg-[#4FD6C4] hover:bg-[#3ec4b2] text-[#14171C]'
                }
              `}
            >
              {isScanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#4FD6C4]" />
                  <span>Running analysis… ({uploadProgress}%)</span>
                </>
              ) : (
                <>
                  <Crosshair className="w-4 h-4" />
                  <span>Analyze image</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Error alert */}
        {errorMsg && (
          <div className="mt-2 p-3.5 rounded-lg bg-[#14171C] border border-[#E8603C]/60 text-[#E8603C] text-xs font-mono flex items-start space-x-2.5 animate-fade-in">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Supported formats capsule */}
      <div className="mt-5 flex">
        <InfoCapsule
          label="Supported formats & tips"
          isOpen={tipsOpen}
          onToggle={() => setTipsOpen(p => !p)}
        >
          <p className="text-[#E7E9EC] font-mono text-[11px] mb-1">Accepted: JPG · JPEG · PNG · WEBP (up to 32 MB)</p>
          <p>For best results, use the original file before any social-media compression. Heavily re-compressed images (Q &lt; 60) may produce lower-confidence scores. Crop the subject close to fill the frame.</p>
          <p>All files are processed in-memory only and never stored on disk.</p>
        </InfoCapsule>
      </div>
    </div>
  );
}
