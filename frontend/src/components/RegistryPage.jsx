/**
 * RegistryPage.jsx
 * ───────────────────────────────────────────────────────────────
 * Full-page view for managing the reference-check registry.
 *
 * Features:
 *  - Lists all registered originals with name, date, phash
 *  - Delete individual entries with confirmation
 *  - Upload a new original directly from this page
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  BookMarked,
  Trash2,
  UploadCloud,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Hash,
  Calendar,
  Image as ImageIcon,
  ShieldCheck,
  X,
} from 'lucide-react';
import { listRegistry, deleteRegistryEntry, registerOriginal } from '../services/api';

const C = {
  teal:   '#4FD6C4',
  green:  '#6FCF97',
  orange: '#E8603C',
  dim:    '#8B93A3',
  card:   '#1C2029',
  border: '#2A2F3A',
  bg:     '#14171C',
  text:   '#E7E9EC',
};

function fmtDate(epoch) {
  if (!epoch) return '—';
  return new Date(epoch * 1000).toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Inline upload zone ────────────────────────────────────────
function UploadZone({ onRegistered }) {
  const inputRef = useRef(null);
  const [file, setFile]       = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr]         = useState(null);
  const [done, setDone]       = useState(false);
  const [dragging, setDragging] = useState(false);

  const pick = (f) => {
    if (!f) return;
    const ext = (f.name || '').split('.').pop().toLowerCase();
    if (!['jpg', 'jpeg', 'png', 'webp', 'bmp'].includes(ext)) {
      setErr('Unsupported format. Use JPG, PNG, WEBP, or BMP.');
      return;
    }
    setErr(null); setDone(false);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const clear = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null); setPreview(null); setErr(null); setDone(false);
    if (inputRef.current) inputRef.current.value = '';
  };

  const submit = async () => {
    if (!file) return;
    setLoading(true); setErr(null);
    try {
      await registerOriginal(file);
      setDone(true);
      onRegistered?.();
      setTimeout(clear, 2500);
    } catch (e) {
      setErr(e?.response?.data?.error || e.message || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="rounded-xl border p-5 space-y-4"
      style={{ background: C.card, borderColor: C.border }}
    >
      <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider" style={{ color: C.teal }}>
        <UploadCloud className="w-3.5 h-3.5" />
        Register New Original
      </div>

      <input
        ref={inputRef}
        type="file"
        className="hidden"
        accept=".jpg,.jpeg,.png,.webp,.bmp,image/*"
        onChange={(e) => e.target.files && pick(e.target.files[0])}
      />

      {!file ? (
        <div
          onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files?.[0]); }}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer flex flex-col items-center gap-3 transition-all duration-200"
          style={{
            borderColor: dragging ? C.teal : C.border,
            background: dragging ? '#4FD6C40A' : C.bg,
          }}
        >
          <ImageIcon className="w-8 h-8" style={{ color: dragging ? C.teal : C.dim }} />
          <div>
            <p className="text-sm font-display font-bold" style={{ color: C.text }}>
              Drop image here, or{' '}
              <span style={{ color: C.teal }} className="underline underline-offset-2">browse</span>
            </p>
            <p className="text-xs font-mono mt-1" style={{ color: C.dim }}>JPG · PNG · WEBP · BMP</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 rounded-lg" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
            {preview && (
              <img src={preview} alt="preview" className="w-14 h-14 object-cover rounded-md" />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono font-bold truncate" style={{ color: C.text }}>{file.name}</p>
              <p className="text-[11px] font-mono mt-0.5" style={{ color: C.dim }}>{(file.size / 1024).toFixed(0)} KB</p>
            </div>
            <button onClick={clear} className="p-1.5 rounded hover:bg-white/5" style={{ color: C.dim }}>
              <X className="w-4 h-4" />
            </button>
          </div>

          {done ? (
            <div className="flex items-center gap-2 text-xs font-mono p-3 rounded-lg" style={{ background: '#6FCF9715', color: C.green }}>
              <CheckCircle2 className="w-4 h-4" />
              Registered successfully!
            </div>
          ) : (
            <button
              onClick={submit}
              disabled={loading}
              className="w-full py-2.5 rounded-lg text-xs font-mono font-semibold flex items-center justify-center gap-2 transition-colors"
              style={{ background: C.teal, color: C.bg, opacity: loading ? 0.75 : 1 }}
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
              {loading ? 'Registering…' : 'Confirm — This is an unedited original'}
            </button>
          )}
        </div>
      )}

      {err && (
        <div className="flex items-start gap-2 text-xs font-mono p-3 rounded-lg" style={{ background: '#E8603C12', color: C.orange, border: `1px solid #E8603C44` }}>
          <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
          {err}
        </div>
      )}
    </div>
  );
}

// ── Entry row ─────────────────────────────────────────────────
function EntryRow({ entry, onDeleted }) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting]     = useState(false);
  const [err, setErr]               = useState(null);

  const doDelete = async () => {
    setDeleting(true); setErr(null);
    try {
      await deleteRegistryEntry(entry.id);
      onDeleted(entry.id);
    } catch (e) {
      setErr(e?.response?.data?.error || 'Delete failed.');
      setDeleting(false);
      setConfirming(false);
    }
  };

  return (
    <div
      className="flex items-center gap-4 px-4 py-3 rounded-lg border transition-all"
      style={{ background: C.bg, borderColor: confirming ? '#E8603C55' : C.border }}
    >
      <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ background: C.card, border: `1px solid ${C.border}` }}>
        <ImageIcon className="w-4 h-4" style={{ color: C.teal }} />
      </div>

      <div className="flex-1 min-w-0 space-y-0.5">
        <p className="text-xs font-mono font-bold truncate" style={{ color: C.text }}>{entry.filename}</p>
        <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono" style={{ color: C.dim }}>
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {fmtDate(entry.registered_at)}
          </span>
          {entry.phash && (
            <span className="flex items-center gap-1">
              <Hash className="w-3 h-3" />
              {entry.phash.slice(0, 12)}…
            </span>
          )}
        </div>
      </div>

      <div className="shrink-0">
        {confirming ? (
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono" style={{ color: C.orange }}>Delete?</span>
            <button
              onClick={doDelete}
              disabled={deleting}
              className="px-3 py-1 rounded text-[11px] font-mono font-bold transition-colors"
              style={{ background: '#E8603C22', color: C.orange, border: '1px solid #E8603C66' }}
            >
              {deleting ? <Loader2 className="w-3 h-3 animate-spin inline" /> : 'Yes'}
            </button>
            <button
              onClick={() => setConfirming(false)}
              className="px-3 py-1 rounded text-[11px] font-mono transition-colors hover:bg-white/5"
              style={{ color: C.dim, border: `1px solid ${C.border}` }}
            >
              No
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            className="p-1.5 rounded hover:bg-white/5 transition-colors"
            style={{ color: C.dim }}
            title="Delete this entry"
            aria-label={`Delete registry entry ${entry.filename}`}
          >
            <Trash2 className="w-4 h-4" />
          </button>
        )}
      </div>

      {err && (
        <p className="w-full text-[11px] font-mono mt-1" style={{ color: C.orange }}>{err}</p>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────
export default function RegistryPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fetchErr, setFetchErr] = useState(null);

  const load = async () => {
    setLoading(true); setFetchErr(null);
    try {
      const data = await listRegistry();
      setEntries(data.entries || []);
    } catch (e) {
      setFetchErr(e?.response?.data?.error || e.message || 'Failed to load registry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDeleted = (id) => setEntries(prev => prev.filter(e => e.id !== id));

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 sm:px-6 space-y-6 font-sans">

      {/* Header */}
      <div className="border-b pb-4" style={{ borderColor: C.border }}>
        <div className="flex items-center gap-2 text-xs font-mono mb-1" style={{ color: C.teal }}>
          <BookMarked className="w-3.5 h-3.5" />
          <span>REFERENCE_REGISTRY</span>
        </div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="font-display text-2xl sm:text-3xl font-bold" style={{ color: C.text }}>
              Reference Registry
            </h1>
            <p className="text-xs font-mono mt-1" style={{ color: C.dim }}>
              Registered originals are compared against every image upload for tampering detection.
            </p>
          </div>
          <button
            onClick={load}
            disabled={loading}
            className="btn-tactile flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-mono transition-colors hover:bg-white/5 shrink-0"
            style={{ borderColor: C.border, color: C.dim }}
            aria-label="Refresh registry list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Upload zone */}
      <UploadZone onRegistered={load} />

      {/* List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider" style={{ color: C.dim }}>
            Registered Originals
          </h2>
          {!loading && (
            <span className="text-[11px] font-mono" style={{ color: C.dim }}>
              {entries.length} {entries.length === 1 ? 'entry' : 'entries'}
            </span>
          )}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12" style={{ color: C.dim }}>
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        )}

        {fetchErr && (
          <div
            className="flex items-start gap-2.5 p-4 rounded-lg border text-sm font-mono"
            style={{ background: '#E8603C10', borderColor: '#E8603C44', color: C.orange }}
          >
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            {fetchErr}
          </div>
        )}

        {!loading && !fetchErr && entries.length === 0 && (
          <div
            className="rounded-xl border p-10 text-center space-y-3"
            style={{ background: C.card, borderColor: C.border }}
          >
            <BookMarked className="w-10 h-10 mx-auto opacity-30" style={{ color: C.teal }} />
            <p className="text-sm font-mono" style={{ color: C.dim }}>
              No originals registered yet.
            </p>
            <p className="text-xs font-mono" style={{ color: C.dim }}>
              Upload a photo above and confirm it is an unedited original.
            </p>
          </div>
        )}

        {!loading && !fetchErr && entries.map(entry => (
          <EntryRow key={entry.id} entry={entry} onDeleted={handleDeleted} />
        ))}
      </div>
    </div>
  );
}
