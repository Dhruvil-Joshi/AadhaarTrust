export interface UploadResponse {
  job_id: string
  status: string
  message: string
}

export interface StageDetails {
  stage_name: string
  stage_description: string
  current_attempt?: number
  total_attempts?: number
}

export interface StatusResponse {
  job_id: string
  status: 'processing' | 'completed' | 'failed'
  current_stage?: string
  progress_percentage: number
  stage_details?: StageDetails
  estimated_time_remaining?: number
}

export interface QRData {
  name?: string
  aadhaar_number?: string
  dob?: string
  gender?: string
  address?: string
}

export interface QRValidation {
  decoded: boolean
  attempt_number?: number
  method?: string
  data?: string[]
}

export interface OCRField {
  value?: string
  confidence: number
}

export interface OCRData {
  name?: OCRField
  aadhaar_number?: OCRField
  dob?: OCRField
  gender?: OCRField
  address?: OCRField
}

// export interface OCRExtraction {
//   success: boolean
//   data?: OCRData
// }

export interface OCRExtraction {
  success: boolean
  raw_text: string
}

// export interface FieldMatch {
//   match: boolean
//   similarity: number
// }

// export interface CrossValidation {
//   name_match?: FieldMatch
//   aadhaar_match?: FieldMatch
//   dob_match?: FieldMatch
//   gender_match?: FieldMatch
//   address_match?: FieldMatch
//   overall_match: number
// }
export interface MatchItem {
  qr_value?: string
  ocr_value?: string
  match: boolean
  similarity: number
}

export interface CrossValidation {
  items: MatchItem[]
  overall_match: number
}

export interface AadhaarValidation {
  format_valid: boolean
  checksum_valid: boolean
}

export interface ForgeryCheck {
  is_forged: boolean
  confidence: number
  splicing_map_url?: string
  annotated_image_url?: string
  forged_area_percentage?: number
  failure_reason?: string
}

// ── Image detection ──────────────────────────────────────────────────────────

/** What the detector decided this image is */
export type DetectedAs = 'front' | 'back' | 'unknown' | null

export interface ImageDetectionStatus {
  uploaded: boolean
  /** null  → image not provided
   *  "unknown" → image provided but not recognised as any Aadhaar side */
  detected_as: DetectedAs
  detection_confidence?: number
  failure_reason?: string
  /** True when this image was in the wrong slot but the pipeline auto-swapped it */
  was_auto_corrected: boolean
}

export interface ImageDetectionInfo {
  front: ImageDetectionStatus
  back: ImageDetectionStatus
  /** True when the pipeline stopped because of an image detection problem */
  pipeline_blocked: boolean
  block_reason?: string
  /** True when both images were valid Aadhaar sides but uploaded in the wrong slots */
  was_swapped: boolean
}

// ────────────────────────────────────────────────────────────────────────────

export interface ValidationResult {
  overall_status: 'VALID' | 'SUSPICIOUS' | 'INVALID' | 'MANUAL_REVIEW'
  overall_confidence: number
  forgery_check: ForgeryCheck
  qr_validation?: QRValidation
  ocr_extraction?: OCRExtraction
  cross_validation?: CrossValidation
  aadhaar_validation?: AadhaarValidation
  image_detection?: ImageDetectionInfo
}

export interface Reports {
  pdf_url?: string
  html_url?: string
  json_url?: string
}

export interface ResultsResponse {
  job_id: string
  status: string
  validation_result?: ValidationResult
  reports?: Reports
  timestamp: string
  processing_time?: number
}