import { CheckCircle2, AlertTriangle, XCircle, Search } from 'lucide-react'
import { ValidationResult } from '../../types/api.types'

interface StatusBannerProps {
  result: ValidationResult
}

export default function StatusBanner({ result }: StatusBannerProps) {
  const { overall_status, overall_confidence } = result

  const config = {
    VALID: {
      icon: CheckCircle2,
      bgColor: 'bg-emerald-500',
      text: 'Aadhaar Verified Successfully',
      confidence: `${(overall_confidence * 100).toFixed(0)}% Overall Confidence`,
    },
    SUSPICIOUS: {
      icon: AlertTriangle,
      bgColor: 'bg-amber-500',
      text: 'Verification Completed with Warnings',
      confidence: `${(overall_confidence * 100).toFixed(0)}% Overall Confidence`,
    },
    INVALID: {
      icon: XCircle,
      bgColor: 'bg-red-500',
      text: 'Aadhaar Validation Failed',
      confidence: result.forgery_check.is_forged ? 'Forgery detected' : 'Validation failed',
    },
    MANUAL_REVIEW: {
      icon: Search,
      bgColor: 'bg-blue-500',
      text: 'Manual Review Required',
      confidence: 'QR code could not be decoded',
    },
  }

  const { icon: Icon, bgColor, text, confidence } = config[overall_status]

  return (
    <div className={`${bgColor} text-white rounded-xl p-6 mb-6`}>
      <div className="flex items-center space-x-4">
        <Icon className="w-12 h-12" />
        <div className="flex-1">
          <h2 className="text-2xl font-bold">{text}</h2>
          <p className="text-white/90 mt-1">{confidence}</p>
        </div>
      </div>
    </div>
  )
}
