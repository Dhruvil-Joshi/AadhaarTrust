import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePolling } from '../hooks/usePolling'
import ProgressStepper from '../components/progress/ProgressStepper'
import ProgressBar from '../components/progress/ProgressBar'
import Card from '../components/common/Card'
import Spinner from '../components/common/Spinner'

export default function ValidationProgressPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const { status, error } = usePolling(jobId || null)

  useEffect(() => {
    if (status?.status === 'completed') {
      navigate(`/results/${jobId}`)
    } else if (status?.status === 'failed') {
      navigate(`/results/${jobId}`)
    }
  }, [status, jobId, navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 flex items-center justify-center">
        <Card>
          <div className="text-center">
            <p className="text-red-600 mb-4">Error loading validation status</p>
            <p className="text-gray-600 text-sm">{error.message}</p>
          </div>
        </Card>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Validation in Progress
            </h1>
            <p className="text-gray-600">Job ID: {jobId}</p>
          </div>

          <div className="mb-8">
            <ProgressStepper currentStage={status.current_stage || 'upload'} />
          </div>

          <div className="mb-6">
            <ProgressBar
              percentage={status.progress_percentage}
              label="Overall Progress"
            />
          </div>

          {status.stage_details && (
            <Card className="bg-purple-50">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {status.stage_details.stage_name}
              </h3>
              <p className="text-gray-700 mb-4">
                {status.stage_details.stage_description}
              </p>
              {status.stage_details.current_attempt && status.stage_details.total_attempts && (
                <p className="text-sm text-purple-primary font-medium">
                  Attempt {status.stage_details.current_attempt} of {status.stage_details.total_attempts}
                </p>
              )}
              {status.estimated_time_remaining && (
                <p className="text-sm text-gray-600 mt-2">
                  Estimated time remaining: ~{status.estimated_time_remaining} seconds
                </p>
              )}
            </Card>
          )}
        </Card>
      </div>
    </div>
  )
}
