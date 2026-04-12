import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import LandingPage from './pages/LandingPage'
import UploadPage from './pages/UploadPage'
import ValidationProgressPage from './pages/ValidationProgressPage'
import ResultsPage from './pages/ResultsPage'
import ManualReviewPage from './pages/ManualReviewPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/validation/:jobId" element={<ValidationProgressPage />} />
          <Route path="/results/:jobId" element={<ResultsPage />} />
          <Route path="/admin/manual-review" element={<ManualReviewPage />} />
        </Routes>
        <Toaster position="top-right" />
      </div>
    </BrowserRouter>
  )
}

export default App
