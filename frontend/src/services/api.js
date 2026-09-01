import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

/**
 * Check backend service health status.
 */
export async function checkBackendHealth() {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.warn('[API] Health check failed, backend might be offline:', error.message);
    return {
      status: 'offline',
      service: 'AI Content Authenticity Detection API (Offline)',
      modules: {
        image_detector: { name: 'Image Detector (Local Mock)', ready: true },
        video_detector: { name: 'Video Detector (Local Mock)', ready: true },
        document_detector: { name: 'Document Detector (Local Mock)', ready: true },
      }
    };
  }
}

/**
 * Fetch capabilities metadata for all 3 detection modules.
 */
export async function getModules() {
  try {
    const response = await apiClient.get('/modules');
    return response.data.modules;
  } catch (error) {
    return [
      {
        id: 'image',
        title: 'Deepfake Image Detection',
        description: 'Analyzes pixel synthesis, GAN artifacts, frequency domain anomalies, and facial landmark inconsistencies.',
        supported_extensions: ['png', 'jpg', 'jpeg', 'webp', 'bmp'],
        endpoint: '/api/detect/image'
      },
      {
        id: 'video',
        title: 'AI-Generated Video Detection',
        description: 'Evaluates spatio-temporal dynamics, frame-to-frame warping, blink rates, and lip-sync audio correlation.',
        supported_extensions: ['mp4', 'avi', 'mov', 'mkv', 'webm'],
        endpoint: '/api/detect/video'
      },
      {
        id: 'document',
        title: 'Document Forgery Detection',
        description: 'Inspects PDF scans, invoices, and certificates for font mismatch, copy-move stamps, and metadata tampering.',
        supported_extensions: ['pdf', 'png', 'jpg', 'jpeg', 'tiff'],
        endpoint: '/api/detect/document'
      }
    ];
  }
}

/**
 * Upload and run detection on an Image file.
 */
export async function detectImage(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/detect/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Upload and run detection on a Video file.
 */
export async function detectVideo(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/detect/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Upload and run detection on a Document / PDF file.
 */
export async function detectDocument(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/detect/document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Smart Auto Detection: forwards file to /detect/auto
 */
export async function detectAuto(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/detect/auto', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Dispatcher to route file based on selected module mode ('auto' | 'image' | 'video' | 'document')
 */
export async function runAuthenticityCheck(file, moduleType = 'auto', onProgress) {
  if (moduleType === 'image') return detectImage(file, onProgress);
  if (moduleType === 'video') return detectVideo(file, onProgress);
  if (moduleType === 'document') return detectDocument(file, onProgress);
  return detectAuto(file, onProgress);
}
