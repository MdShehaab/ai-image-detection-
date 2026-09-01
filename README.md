# AI-Powered Content Authenticity Detection System

A multi-modal AI system for detecting synthetic and manipulated media across three domains:
1. **Deepfake Image Detection** (GANs, Diffusion, Face Swap)
2. **AI-Generated Video Detection** (Temporal warping, AV lip-sync, blinking dynamics)
3. **Document Forgery Detection** (Font mismatch, copy-move stamp duplication, ELA, PDF metadata)

---

## 🏗️ Architecture Overview

```
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                     # Route handlers: /api/detect/image, /api/detect/video, /api/detect/document, /api/health
│   ├── models/
│   │   ├── __init__.py
│   │   ├── image_detector/
│   │   │   ├── __init__.py
│   │   │   └── model.py                  # DeepfakeImageDetector: model load & inference stubs
│   │   ├── video_detector/
│   │   │   ├── __init__.py
│   │   │   └── model.py                  # VideoDeepfakeDetector: 3D temporal aggregation stubs
│   │   └── document_detector/
│   │       ├── __init__.py
│   │       └── model.py                  # DocumentForgeryDetector: OCR, layout & font forensics
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── image_preprocessing.py        # 2D FFT, face crops, EXIF metadata
│   │   ├── video_preprocessing.py        # Frame sampling, temporal stride
│   │   └── document_preprocessing.py     # PDF rasterizer, OCR bounding boxes, SIFT clone checks
│   ├── utils/
│   │   ├── __init__.py
│   │   └── file_utils.py                 # Safe upload storage, MIME checks, cleanup
│   ├── app.py                            # Flask application factory with CORS & size limits
│   ├── config.py                         # Environment configs & extension whitelists
│   ├── requirements.txt                  # Python dependencies
│   ├── run.py                            # Backend server runner
│   └── test_api.py                       # Automated test suite
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx                # Brand navigation & API health indicator
│   │   │   ├── Footer.jsx                # Technical architecture footer
│   │   │   ├── LandingPage.jsx           # Module showcase & workflow timeline
│   │   │   ├── UploadPage.jsx            # Drag-and-drop with smart auto-routing & sample loaders
│   │   │   ├── ResultsPage.jsx           # Verdict report, confidence gauge, and forensic breakdown
│   │   │   ├── VisualGauge.jsx           # Circular SVG gauge meter with verdict glow
│   │   │   └── AnomalyChart.jsx          # Recharts metric bars and video temporal graphs
│   │   ├── services/
│   │   │   └── api.js                    # Axios client connecting to Flask backend
│   │   ├── App.jsx                       # View controller & state orchestration
│   │   ├── index.css                     # Tailwind styles & glassmorphism theme
│   │   └── main.jsx                      # React entrypoint
│   ├── index.html                        # Google fonts (Inter & JetBrains Mono)
│   ├── package.json                      # Dependencies (React, Recharts, Lucide, Tailwind)
│   ├── tailwind.config.js                # Custom cybersecurity palette
│   └── vite.config.js                    # Vite dev server with proxy to Flask
│
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Backend Setup (Flask REST API)

1. Open a terminal in the `backend/` directory:
```bash
cd backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

3. Run the backend server:
```bash
python run.py
```
> The API will be active at `http://127.0.0.1:5000` with health check at `http://127.0.0.1:5000/api/health`.

4. (Optional) Run tests:
```bash
python test_api.py
```

---

### 2. Frontend Setup (React + Vite + Tailwind)

1. Open a terminal in the `frontend/` directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the Vite development server:
```bash
npm run dev
```
> The frontend web UI will open on `http://localhost:3000`.

---

## 📡 API Endpoints Specification

| Method | Endpoint | Description | Payload |
|---|---|---|---|
| `GET` | `/api/health` | Health check & loaded model status | None |
| `GET` | `/api/modules` | Metadata & supported extensions for each module | None |
| `POST` | `/api/detect/image` | Image deepfake analysis | `multipart/form-data` with `file` |
| `POST` | `/api/detect/video` | Video temporal deepfake analysis | `multipart/form-data` with `file` |
| `POST` | `/api/detect/document` | Document forgery & layout tampering analysis | `multipart/form-data` with `file` |
| `POST` | `/api/detect/auto` | Smart auto-routing based on MIME & file format | `multipart/form-data` with `file` |

### Sample Response Schema
```json
{
  "module": "image_detector",
  "model_version": "Veritas-Image-EfficientNetV2-B3",
  "verdict": "FAKE",
  "confidence": 91.2,
  "probabilities": {
    "fake": 0.912,
    "real": 0.088
  },
  "breakdown": [
    {
      "metric": "Facial Boundary Blending",
      "score": 88,
      "status": "High Anomaly",
      "description": "Noticeable color boundary gradient discontinuity around facial perimeter."
    },
    {
      "metric": "Frequency Domain Artifacts (FFT)",
      "score": 93,
      "status": "High Anomaly",
      "description": "Checkerboard artifacts detected in the high-frequency spectrum."
    }
  ],
  "explanation": "The image displays characteristic synthetic generation artifacts...",
  "execution_time_ms": 145.2,
  "file_name": "sample_portrait.png"
}
```

---

## 🔌 Plugging in Real Model Weights

Each detector module contains dedicated `TODO` markers where you can plug in real neural network inference code:

- **Deepfake Images** (`backend/models/image_detector/model.py`):
  - Load EfficientNet, MesoNet, or ResNeXt weights via `tf.keras.models.load_model()` or `torch.load()`.
  - Pass the preprocessed tensor from `backend/preprocessing/image_preprocessing.py`.

- **Deepfake Videos** (`backend/models/video_detector/model.py`):
  - Use OpenCV `cv2.VideoCapture` in `backend/preprocessing/video_preprocessing.py` to extract 16/32-frame batches.
  - Run 3D-CNN / TimeSformer model to evaluate temporal feature continuity.

- **Document Forgeries** (`backend/models/document_detector/model.py`):
  - Plug in PyMuPDF (fitz) + Tesseract OCR in `backend/preprocessing/document_preprocessing.py` for layout bounding boxes.
  - Run SIFT/ORB keypoint matching for copy-move cloned regions and ELA for compression differences.
