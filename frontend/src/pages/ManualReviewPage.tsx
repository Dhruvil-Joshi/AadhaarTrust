import Card from '../components/common/Card'
import Button from '../components/common/Button'

export default function ManualReviewPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card>
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Manual Review Dashboard
          </h1>
          <p className="text-gray-600">
            Administrator-only access. Manual review functionality coming soon.
          </p>
        </Card>
      </div>
    </div>
  )
}
