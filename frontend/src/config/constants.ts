export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const ALLOWED_FILE_TYPES = ['image/jpeg', 'image/png', 'image/tiff', 'image/bmp']
export const MAX_FILE_SIZE = 25 * 1024 * 1024 // 25MB

export const STAGES = [
  { id: 'upload', label: 'Upload', order: 1 },
  { id: 'aadhaar_verhoeff_check', label: 'Checksum Validation', order: 2 },
  { id: 'qr_scanning', label: 'QR Scanning', order: 3 },
  { id: 'ocr_extraction', label: 'OCR Extraction', order: 4 },
  { id: 'forgery_detection', label: 'Forgery Detection', order: 5 },
  { id: 'validation', label: 'Validation', order: 6 },
] as const

export const STATUS_COLORS = {
  VALID: 'bg-emerald-500',
  SUSPICIOUS: 'bg-amber-500',
  INVALID: 'bg-red-500',
  MANUAL_REVIEW: 'bg-blue-500',
} as const
