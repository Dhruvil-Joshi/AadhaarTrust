import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import {
  ArrowLeft, Download,
  CheckCircle, XCircle, AlertCircle, HelpCircle, ArrowLeftRight,
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { getResults, downloadFile } from '../services/api'
import type { ResultsResponse, ImageDetectionStatus } from '../types/api.types'
import StatusBanner from '../components/results/StatusBanner'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'
import Spinner from '../components/common/Spinner'

// ── Detection helpers ─────────────────────────────────────────────────────────

type DetectionVariant = 'success' | 'warning' | 'error' | 'info'

function detectionVariant(
  status: ImageDetectionStatus,
  expectedSide: 'front' | 'back',
): DetectionVariant {
  if (!status.uploaded) return 'info'
  if (!status.detected_as || status.detected_as === 'unknown') return 'error'
  // Swapped but auto-corrected — treat as success
  if (status.was_auto_corrected) return 'success'
  if (status.detected_as !== expectedSide) return 'warning'
  return 'success'
}

function detectionLabel(
  status: ImageDetectionStatus,
  expectedSide: 'front' | 'back',
): string {
  if (!status.uploaded) return 'Not uploaded'
  if (!status.detected_as || status.detected_as === 'unknown')
    return 'Unrecognised image'
  if (status.was_auto_corrected)
    return `Detected as ${status.detected_as} → auto-corrected to ${expectedSide} slot ✓`
  if (status.detected_as !== expectedSide)
    return `Detected as ${status.detected_as} (expected ${expectedSide})`
  return `Detected as ${expectedSide} ✓`
}

const VARIANT_ICONS: Record<DetectionVariant, React.ReactNode> = {
  success: <CheckCircle  className="w-5 h-5 text-green-500"  />,
  warning: <AlertCircle  className="w-5 h-5 text-yellow-500" />,
  error:   <XCircle      className="w-5 h-5 text-red-500"    />,
  info:    <HelpCircle   className="w-5 h-5 text-gray-400"   />,
}

const VARIANT_CLASSES: Record<DetectionVariant, string> = {
  success: 'bg-green-50 border-green-200 text-green-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  error:   'bg-red-50 border-red-200 text-red-700',
  info:    'bg-gray-50 border-gray-200 text-gray-500',
}

// ── ImageCard component ───────────────────────────────────────────────────────

interface ImageCardProps {
  title: string
  imageUrl: string | null | undefined
  status: ImageDetectionStatus
  expectedSide: 'front' | 'back'
}


function ImageCard({ title, imageUrl, status, expectedSide }: ImageCardProps) {
  const variant = detectionVariant(status, expectedSide)
  const label   = detectionLabel(status, expectedSide)
  const icon    = VARIANT_ICONS[variant]

  return (
    <div className="flex flex-col gap-3">
      {/* Slot label */}
      <div className="flex items-center gap-2">
        <p className="text-xs font-semibold text-purple-primary uppercase tracking-wide">
          {title}
        </p>
        {status.was_auto_corrected && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
            <ArrowLeftRight className="w-3 h-3" />
            Auto-corrected
          </span>
        )}
      </div>

      {/* Detection status pill */}
      <div className={`flex items-start gap-2 rounded-lg px-3 py-2 text-sm border ${VARIANT_CLASSES[variant]}`}>
        <span className="mt-0.5 shrink-0">{icon}</span>
        <div>
          <p className="font-medium">{label}</p>
          {/* Only show failure_reason when not auto-corrected */}
          {status.failure_reason && !status.was_auto_corrected && (
            <p className="mt-0.5 text-xs opacity-80">{status.failure_reason}</p>
          )}
        </div>
      </div>

      {/* Image preview */}
      {imageUrl ? (
        <div className="border rounded-lg overflow-hidden bg-gray-100">
          <img src={imageUrl} alt={title} className="w-full h-auto" />
        </div>
      ) : (
        <div className="border-2 border-dashed border-gray-200 rounded-lg h-40 flex items-center justify-center text-gray-400 text-sm">
          {status.uploaded ? 'Preview unavailable' : 'No image uploaded'}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate  = useNavigate()
  const location  = useLocation()

  const [results,   setResults]   = useState<ResultsResponse | null>(null)
  const [loading,   setLoading]   = useState(true)
  const [activeTab, setActiveTab] = useState('summary')

  const frontImageUrl: string | null = location.state?.frontImageUrl ?? null
  const backImageUrl:  string | null = location.state?.backImageUrl  ?? null

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const data = await getResults(jobId!)
        setResults(data)
      } catch (error: any) {
        toast.error('Failed to load results')
        console.error(error)
      } finally {
        setLoading(false)
      }
    }
    if (jobId) fetchResults()
  }, [jobId])

  const handleDownload = async (fileType: string) => {
    if (!jobId) return
    try {
      const blob = await downloadFile(jobId, fileType)
      const url  = window.URL.createObjectURL(blob)
      const a    = document.createElement('a')
      a.href     = url
      a.download = fileType
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Download started')
    } catch {
      toast.error('Download failed')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!results || !results.validation_result) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 flex items-center justify-center">
        <Card>
          <div className="text-center">
            <p className="text-gray-600">No results found</p>
            <Button className="mt-4" onClick={() => navigate('/upload')}>
              Upload New Image
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  const { validation_result } = results
  const imgDet = validation_result.image_detection


  // ── TEMPORARY MOCK OVERRIDE — remove after backend is ready ──────────
// const mockOcr = {
//   success: true,
//   data: {
//     name:           { value: "Rahul Sharma",                                    confidence: 0.92 },
//     aadhaar_number: { value: "XXXX-XXXX-4321",                                  confidence: 0.97 },
//     dob:            { value: "15-08-1990",                                       confidence: 0.91 },
//     gender:         { value: "Male",                                             confidence: 0.99 },
//     address:        { value: "42, MG Road, Koramangala, Bengaluru, KA 560034",  confidence: 0.85 },
//   }
// }

// const mockCrossValidation = {
//   name_match:     { match: true,  similarity: 95.0  },
//   aadhaar_match:  { match: true,  similarity: 100.0 },
//   dob_match:      { match: true,  similarity: 100.0 },
//   gender_match:   { match: true,  similarity: 100.0 },
//   address_match:  { match: false, similarity: 72.0  },
//   overall_match:  93.4,
// }

// const mockAadhaarValidation = { format_valid: true, checksum_valid: true }

// validation_result.ocr_extraction    = mockOcr
// validation_result.cross_validation  = mockCrossValidation
// validation_result.aadhaar_validation = mockAadhaarValidation
// validation_result.overall_status    = "VALID"
// validation_result.overall_confidence = 0.94
// ── END MOCK OVERRIDE ─────────────────────────────────────────────────

  // Fallback status when backend didn't populate image_detection
  const defaultStatus = (uploaded: boolean): ImageDetectionStatus => ({
    uploaded,
    detected_as: null,
    failure_reason: undefined,
    was_auto_corrected: false,
  })

  const frontStatus: ImageDetectionStatus =
    imgDet?.front ?? defaultStatus(!!frontImageUrl)
  const backStatus: ImageDetectionStatus =
    imgDet?.back  ?? defaultStatus(!!backImageUrl)

  const tabs = ['summary', 'images', 'forgery', 'qr', 'ocr', 'validation']
  const isPipelineFailed = !!validation_result.forgery_check.failure_reason

  // Small image block reused only in the Summary tab
  const UploadedImagesMini = () =>
    frontImageUrl || backImageUrl ? (
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">Uploaded Images</h3>
        <div className={`grid gap-4 ${backImageUrl ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {frontImageUrl && (
            <div>
              <p className="text-xs font-semibold text-purple-primary uppercase tracking-wide mb-2">
                Front Side
              </p>
              <div className="border rounded-lg overflow-hidden bg-gray-100">
                <img src={frontImageUrl} alt="Front Side" className="w-full h-auto" />
              </div>
            </div>
          )}
          {backImageUrl && (
            <div>
              <p className="text-xs font-semibold text-purple-primary uppercase tracking-wide mb-2">
                Back Side
              </p>
              <div className="border rounded-lg overflow-hidden bg-gray-100">
                <img src={backImageUrl} alt="Back Side" className="w-full h-auto" />
              </div>
            </div>
          )}
        </div>
      </div>
    ) : null

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <Link
          to="/upload"
          className="inline-flex items-center text-purple-primary hover:text-purple-accent mb-8"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Upload
        </Link>

        <StatusBanner result={validation_result} />

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <Card>
              {/* Tab bar */}
              <div className="flex flex-wrap gap-x-1 mb-6 border-b">
                {tabs.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 font-medium capitalize transition-colors ${
                      activeTab === tab
                        ? 'text-purple-primary border-b-2 border-purple-primary'
                        : 'text-gray-600 hover:text-purple-primary'
                    }`}
                  >
                    {tab}
                    {/* Dot indicator on images tab when there was a swap or block */}
                    {tab === 'images' && (imgDet?.pipeline_blocked || imgDet?.was_swapped) && (
                      <span className={`ml-1.5 inline-block w-2 h-2 rounded-full align-middle
                        ${imgDet.pipeline_blocked ? 'bg-red-500' : 'bg-blue-500'}`}
                      />
                    )}
                  </button>
                ))}
              </div>

              {/* ── SUMMARY ── */}
              {activeTab === 'summary' && (
                <div className="space-y-6">
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Overall Status</h3>
                      <Badge
                        variant={
                          validation_result.overall_status === 'VALID'      ? 'success' :
                          validation_result.overall_status === 'SUSPICIOUS' ? 'warning' :
                          validation_result.overall_status === 'INVALID'    ? 'error'   : 'info'
                        }
                      >
                        {validation_result.overall_status}
                      </Badge>
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Confidence Score</h3>
                      <p className="text-2xl font-bold text-purple-primary">
                        {(validation_result.overall_confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    {results.processing_time && (
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-2">Processing Time</h3>
                        <p className="text-gray-700">{results.processing_time.toFixed(2)} seconds</p>
                      </div>
                    )}
                  </div>
                  <UploadedImagesMini />
                </div>
              )}

              {/* ── IMAGES ── */}
              {activeTab === 'images' && (
                <div className="space-y-6">

                  {/* ① Pipeline hard-stopped */}
                  {imgDet?.pipeline_blocked && (
                    <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                      <XCircle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="font-semibold text-red-800">Pipeline stopped — image detection failed</p>
                        <p className="text-sm text-red-700 mt-1">
                          {imgDet.block_reason ?? 'Image detection failed before processing could begin.'}
                        </p>
                        <p className="text-xs text-red-600 mt-2">
                          Processing was not attempted. Please re-upload correct images and try again.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ② Swap auto-corrected (non-blocking) */}
                  {!imgDet?.pipeline_blocked && imgDet?.was_swapped && (
                    <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <ArrowLeftRight className="w-5 h-5 text-blue-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="font-semibold text-blue-800">Images were uploaded in swapped slots</p>
                        <p className="text-sm text-blue-700 mt-1">
                          The front and back images appeared to be in the wrong slots.
                          They were automatically corrected and processing continued normally.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* ③ Image cards */}
                  <div className={`grid gap-6 ${backImageUrl ? 'sm:grid-cols-2' : 'grid-cols-1 max-w-sm'}`}>
                    <ImageCard
                      title="Front Side"
                      imageUrl={frontImageUrl}
                      status={frontStatus}
                      expectedSide="front"
                    />
                    <ImageCard
                      title="Back Side"
                      imageUrl={backImageUrl}
                      status={backStatus}
                      expectedSide="back"
                    />
                  </div>

                  {/* ④ Detection summary table */}
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Detection Summary</h3>
                    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Slot</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Uploaded</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Detected As</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Result</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {([
                            ['Front Side', frontStatus, 'front'],
                            ['Back Side',  backStatus,  'back'],
                          ] as [string, ImageDetectionStatus, 'front' | 'back'][]).map(([label, status, side]) => {
                            const v = detectionVariant(status, side)
                            let resultLabel = 'N/A'
                            if (v === 'success' && status.was_auto_corrected) resultLabel = 'Auto-corrected ✓'
                            else if (v === 'success')  resultLabel = 'OK ✓'
                            else if (v === 'warning')  resultLabel = 'Wrong slot'
                            else if (v === 'error')    resultLabel = status.uploaded ? 'Unrecognised' : 'Missing'

                            return (
                              <tr key={label}>
                                <td className="px-4 py-2 text-gray-700 font-medium">{label}</td>
                                <td className="px-4 py-2">
                                  <Badge variant={status.uploaded ? 'success' : 'info'}>
                                    {status.uploaded ? 'Yes' : 'No'}
                                  </Badge>
                                </td>
                                <td className="px-4 py-2 text-gray-700 capitalize">
                                  {status.detected_as ?? '—'}
                                </td>
                                <td className="px-4 py-2">
                                  <Badge variant={
                                    v === 'success' ? 'success' :
                                    v === 'warning' ? 'warning' :
                                    v === 'error'   ? 'error'   : 'info'
                                  }>
                                    {resultLabel}
                                  </Badge>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* ⑤ Per-image failure reasons (only when not auto-corrected) */}
                  {(
                    (frontStatus.failure_reason && !frontStatus.was_auto_corrected) ||
                    (backStatus.failure_reason  && !backStatus.was_auto_corrected)
                  ) && (
                    <div className="space-y-2">
                      <h3 className="font-semibold text-gray-900">Detection Issues</h3>
                      {frontStatus.failure_reason && !frontStatus.was_auto_corrected && (
                        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
                          <span className="font-medium">Front: </span>{frontStatus.failure_reason}
                        </div>
                      )}
                      {backStatus.failure_reason && !backStatus.was_auto_corrected && (
                        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm text-yellow-800">
                          <span className="font-medium">Back: </span>{backStatus.failure_reason}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ── FORGERY ── */}
              {activeTab === 'forgery' && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Forgery Detection Status</h3>
                    <div className="flex items-center space-x-4">
                      <Badge variant={validation_result.forgery_check.is_forged || isPipelineFailed ? 'error' : 'success'}>
                        {validation_result.forgery_check.is_forged || isPipelineFailed ? 'Forged' : 'Genuine'}
                      </Badge>
                      <span className="text-gray-700">
                        Confidence: {(validation_result.forgery_check.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {validation_result.forgery_check.annotated_image_url && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Forgery Analysis Result</h3>
                      <div className="border rounded-lg overflow-hidden bg-gray-100">
                        <img
                          src={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${validation_result.forgery_check.annotated_image_url}`}
                          alt="Forgery Analysis"
                          className="w-full h-auto"
                        />
                      </div>
                      <p className="text-sm text-gray-500 mt-2">
                        Red boxes indicate detected manipulated regions.
                      </p>
                    </div>
                  )}

                  {!validation_result.forgery_check.annotated_image_url &&
                    validation_result.forgery_check.is_forged && (
                      <div className="p-4 bg-yellow-50 rounded-md border border-yellow-200">
                        <p className="text-yellow-700 text-sm">Visual analysis not available.</p>
                      </div>
                    )}

                  {validation_result.forgery_check.failure_reason && (
                    <div className="p-4 bg-red-50 rounded-md border border-red-200">
                      <p className="font-medium text-red-800 text-sm mb-1">Pipeline error</p>
                      <p className="text-red-700 text-sm">{validation_result.forgery_check.failure_reason}</p>
                    </div>
                  )}
                </div>
              )}

              {/* ── QR ── */}
              {/* {activeTab === 'qr' && (
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">QR Code Status</h3>
                    {validation_result.qr_validation?.decoded ? (
                      <>
                        <Badge variant="success">Decoded</Badge>
                        <p className="text-gray-700 mt-2">
                          {validation_result.qr_validation.attempt_number && (
                            <span className="block">
                              Successful on attempt {validation_result.qr_validation.attempt_number}/4
                            </span>
                          )}
                          {validation_result.qr_validation.method && (
                            <span className="block text-sm text-gray-600">
                              Method: {validation_result.qr_validation.method}
                            </span>
                          )}
                        </p>
                      </>
                    ) : (
                      <>
                        <Badge variant="error">Not Decoded</Badge>
                        <p className="text-gray-700 mt-2 text-sm">
                          QR code could not be decoded. This case may be routed to manual review.
                        </p>
                      </>
                    )}
                  </div>

                  {validation_result.qr_validation?.decoded && validation_result.qr_validation?.data && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">QR Extracted Data</h3>
                      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                        <table className="min-w-full divide-y divide-gray-200 text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">Field</th>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">Value</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {[
                              ['Name',           validation_result.qr_validation.data.name],
                              ['Aadhaar Number', validation_result.qr_validation.data.aadhaar_number],
                              ['Date of Birth',  validation_result.qr_validation.data.dob],
                              ['Gender',         validation_result.qr_validation.data.gender],
                              ['Address',        validation_result.qr_validation.data.address],
                            ].map(([label, value]) => (
                              <tr key={label}>
                                <td className="px-4 py-2 text-gray-700">{label}</td>
                                <td className="px-4 py-2 text-gray-900 whitespace-pre-line">{value || '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )} */}
              {activeTab === 'qr' && (
              <div className="space-y-4">
                
                {/* ── QR STATUS ── */}
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">QR Code Status</h3>

                  {validation_result.qr_validation?.decoded ? (
                    <>
                      <Badge variant="success">Decoded</Badge>

                      <p className="text-gray-700 mt-2">
                        {validation_result.qr_validation.attempt_number && (
                          <span className="block">
                            Successful on attempt {validation_result.qr_validation.attempt_number}/4
                          </span>
                        )}

                        {validation_result.qr_validation.method && (
                          <span className="block text-sm text-gray-600">
                            Method: {validation_result.qr_validation.method}
                          </span>
                        )}
                      </p>
                    </>
                  ) : (
                    <>
                      <Badge variant="error">Not Decoded</Badge>
                      <p className="text-gray-700 mt-2 text-sm">
                        QR code could not be decoded. This case may be routed to manual review.
                      </p>
                    </>
                  )}
                </div>

                {/* ── QR DATA (LIST BASED) ── */}
                {validation_result.qr_validation?.decoded && validation_result.qr_validation?.data?.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">QR Extracted Data</h3>

                      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                        <table className="min-w-full divide-y divide-gray-200 text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">
                                Field
                              </th>
                              <th className="px-4 py-2 text-left font-medium text-gray-600">
                                Value
                              </th>
                            </tr>
                          </thead>

                          <tbody className="divide-y divide-gray-100">
                            {validation_result.qr_validation.data.map((value, index) => (
                              <tr key={index} className="hover:bg-gray-50">
                                
                                {/* Field Label */}
                                <td className="px-4 py-2 text-gray-500">
                                  Field {index + 1}
                                </td>

                                {/* Value */}
                                <td className="px-4 py-2 text-gray-900 whitespace-pre-line break-words">
                                  {value || '—'}
                                </td>

                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
              </div>
            )}

              {/* ── OCR ── */}
              {activeTab === 'ocr' && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-2">OCR Extraction</h3>

                  {validation_result.ocr_extraction?.success && validation_result.ocr_extraction.raw_text ? (
                    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white p-4">
                      <div className="text-sm text-gray-900 whitespace-pre-wrap font-mono">
                        {validation_result.ocr_extraction.raw_text}
                      </div>
                    </div>
                  ) : (
                    <div className="p-4 bg-yellow-50 rounded-md border border-yellow-200">
                      <p className="text-yellow-700 text-sm">OCR extraction not available.</p>
                    </div>
                  )}
                </div>
              )}
              {/* {activeTab === 'ocr' && (
                <div className="space-y-4">
                  <h3 className="font-semibold text-gray-900 mb-2">OCR Extraction</h3>
                  {validation_result.ocr_extraction?.success && validation_result.ocr_extraction.data ? (
                    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Field</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Value</th>
                            <th className="px-4 py-2 text-left font-medium text-gray-600">Confidence</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {([
                            ['Name',           validation_result.ocr_extraction.data.name],
                            ['Aadhaar Number', validation_result.ocr_extraction.data.aadhaar_number],
                            ['Date of Birth',  validation_result.ocr_extraction.data.dob],
                            ['Gender',         validation_result.ocr_extraction.data.gender],
                            ['Address',        validation_result.ocr_extraction.data.address],
                          ] as [string, { value?: string; confidence: number } | undefined][]).map(([label, field]) => (
                            <tr key={label}>
                              <td className="px-4 py-2 text-gray-700">{label}</td>
                              <td className="px-4 py-2 text-gray-900">{field?.value || '—'}</td>
                              <td className="px-4 py-2 text-gray-600">
                                {field ? `${(field.confidence * 100).toFixed(1)}%` : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="p-4 bg-yellow-50 rounded-md border border-yellow-200">
                      <p className="text-yellow-700 text-sm">OCR extraction not available.</p>
                    </div>
                  )}
                </div>
              )} */}

              {/* ── VALIDATION ── */}
              {activeTab === 'validation' && (
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900 mb-2">Cross-Validation</h3>

                {validation_result.cross_validation?.items ? (
                  <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
                    <table className="min-w-full divide-y divide-gray-200 text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-gray-600">QR Value</th>
                          <th className="px-4 py-2 text-left font-medium text-gray-600">OCR Value</th>
                          <th className="px-4 py-2 text-left font-medium text-gray-600">Match</th>
                          <th className="px-4 py-2 text-left font-medium text-gray-600">Similarity</th>
                        </tr>
                      </thead>

                      <tbody className="divide-y divide-gray-100">
                        {validation_result.cross_validation.items.map((item, index) => (
                          <tr key={index}>
                            {/* QR Value */}
                            <td className="px-4 py-2 text-gray-600">
                              {item.qr_value || '—'}
                            </td>

                            {/* OCR Value */}
                            <td className="px-4 py-2 text-gray-600">
                              {item.ocr_value || '—'}
                            </td>

                            {/* Match */}
                            <td className="px-4 py-2">
                              <Badge variant={item.match ? 'success' : 'error'}>
                                {item.match ? 'Match' : 'Mismatch'}
                              </Badge>
                            </td>

                            {/* Similarity */}
                            <td className="px-4 py-2 text-gray-600">
                              {item.similarity.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>

                    {/* Overall Score */}
                    <div className="px-4 py-3 border-t bg-gray-50 text-sm text-gray-700 flex justify-between">
                      <span className="font-medium">Overall Match</span>
                      <span className="font-semibold">
                        {validation_result.cross_validation.overall_match.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-yellow-50 rounded-md border border-yellow-200">
                    <p className="text-yellow-700 text-sm">
                      Cross-validation data not available.
                    </p>
                  </div>
                )}

                  {validation_result.aadhaar_validation && (
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Aadhaar Number Validation</h3>
                      <div className="flex gap-4">
                        <Badge variant={validation_result.aadhaar_validation.format_valid ? 'success' : 'error'}>
                          Format: {validation_result.aadhaar_validation.format_valid ? 'Valid' : 'Invalid'}
                        </Badge>
                        <Badge variant={validation_result.aadhaar_validation.checksum_valid ? 'success' : 'error'}>
                          Checksum: {validation_result.aadhaar_validation.checksum_valid ? 'Valid' : 'Invalid'}
                        </Badge>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div>
            <Card>
              <h3 className="font-semibold text-gray-900 mb-4">Download Reports</h3>
              <div className="space-y-3">
                <Button variant="outline" className="w-full" onClick={() => handleDownload('report.pdf')}>
                  <Download className="w-4 h-4 mr-2 inline" />
                  PDF Report
                </Button>
                <Button variant="outline" className="w-full" onClick={() => handleDownload('report.html')}>
                  <Download className="w-4 h-4 mr-2 inline" />
                  HTML Report
                </Button>
                <Button variant="outline" className="w-full" onClick={() => handleDownload('data.json')}>
                  <Download className="w-4 h-4 mr-2 inline" />
                  JSON Data
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}