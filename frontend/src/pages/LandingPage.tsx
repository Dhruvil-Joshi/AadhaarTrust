import { Link } from 'react-router-dom'
import { Shield, Search, QrCode, CheckCircle } from 'lucide-react'
import Button from '../components/common/Button'
import Card from '../components/common/Card'
import AadhaarLogo from '../components/common/aadhaartrust.svg'
export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-white to-purple-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-transparent-primary rounded-full flex items-center justify-center">
                  <div className="flex justify-center mb-6">
  <div className="w-72 h-72  pt-10 flex items-center justify-center overflow-visible">
    <img
      src={AadhaarLogo}
      alt="Aadhaar Logo"
      className="w-70 h-70 object-contain"
    />
  </div>
</div>
              {/* <div className="w-20 h-20 bg-purple-primary rounded-full flex items-center justify-center"> */}
              {/* <Shield className="w-12 h-12 text-white" /> */}
              </div>
            </div>
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              AadhaarTrust
            </h1>
            <p className="text-2xl text-gray-600 mb-2">
              Your Trusted Aadhaar Verifier
            </p>
            <p className="text-lg text-gray-500 mb-8">
              AI-Powered Forgery Detection & Validation
            </p>
            <Link to="/upload">
              <Button size="lg">
                Start Verification
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Why Choose AadhaarTrust?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card hover>
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-purple-primary" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Forgery Detection
                </h3>
                <p className="text-gray-600">
                  Advanced noiseprint analysis detects manipulated images with high accuracy
                </p>
              </div>
            </Card>
            <Card hover>
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <QrCode className="w-8 h-8 text-purple-primary" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  QR Validation
                </h3>
                <p className="text-gray-600">
                  4-stage progressive decoding for accurate data extraction from QR codes
                </p>
              </div>
            </Card>
            <Card hover>
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-purple-primary" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Cross-Validation
                </h3>
                <p className="text-gray-600">
                  Compare QR and OCR data for complete verification and fraud prevention
                </p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-purple-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-purple-primary mb-2">&lt;60 sec</div>
              <div className="text-gray-600">Average Aadhaar validation time</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-purple-primary mb-2">Data Privacy</div>
              <div className="text-gray-600">Aadhaar details are securely masked</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-purple-primary mb-2">99.5%</div>
              <div className="text-gray-600">Accuracy Rate</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-gray-400">
              © 2026 AadhaarTrust. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
