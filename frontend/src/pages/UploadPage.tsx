import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-hot-toast'
import { Link } from 'react-router-dom'
import { ArrowLeft, Upload as UploadIcon } from 'lucide-react'
import FileUploader from '../components/upload/FileUploader'
import Button from '../components/common/Button'
import { uploadImage } from '../services/api'

export default function UploadPage() {
  const [frontFile, setFrontFile] = useState<File | null>(null)
  const [backFile, setBackFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const navigate = useNavigate()

  const handleUpload = async () => {
    if (!frontFile) {
      toast.error('Please select the front side of your Aadhaar card')
      return
    }

    setUploading(true)
    try {
      const response = await uploadImage(frontFile, backFile ?? undefined)
      toast.success('Image uploaded successfully!')
      // navigate(`/validation/${response.job_id}`)
      navigate(`/validation/${response.job_id}`, {
        state: {
          frontImageUrl: URL.createObjectURL(frontFile),
          backImageUrl: backFile ? URL.createObjectURL(backFile) : null,
        }
      })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <Link
          to="/"
          className="inline-flex items-center text-purple-primary hover:text-purple-accent mb-8"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Back to Home
        </Link>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <UploadIcon className="w-8 h-8 text-purple-primary" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Upload Aadhaar Image
            </h1>
            <p className="text-gray-600">
              Upload front side and back side of your Aadhaar card
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <FileUploader
              label="Front Side"
              selectedFile={frontFile}
              onFileSelect={setFrontFile}
              onRemove={() => setFrontFile(null)}
            />
            <FileUploader
              label="Back Side"
              selectedFile={backFile}
              onFileSelect={setBackFile}
              onRemove={() => setBackFile(null)}
            />
          </div>

          <div className="bg-purple-50 rounded-lg p-6 mb-8">
            <h3 className="font-semibold text-gray-900 mb-3">Instructions:</h3>
            <ul className="space-y-2 text-sm text-gray-700">
              <li>• Ensure image is clear and well-lit</li>
              <li>• QR code should be visible</li>
              <li>• Minimum resolution: 800×600 pixels</li>
              <li>• Supported formats: JPEG, PNG, TIFF, BMP</li>
              <li>• Maximum file size: 25 MB</li>
            </ul>
          </div>

          <div className="flex justify-center">
            <Button
              size="lg"
              onClick={handleUpload}
              disabled={!frontFile || !backFile || uploading}
              className="w-full md:w-auto"
            >
              {uploading ? 'Uploading...' : 'Start Verification'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}


// import { useState } from 'react'
// import { useNavigate } from 'react-router-dom'
// import { toast } from 'react-hot-toast'
// import { Link } from 'react-router-dom'
// import { ArrowLeft, Upload as UploadIcon } from 'lucide-react'
// import FileUploader from '../components/upload/FileUploader'
// import Button from '../components/common/Button'
// import { uploadImage } from '../services/api'

// export default function UploadPage() {
//   const [selectedFile, setSelectedFile] = useState<File | null>(null)
//   const [uploading, setUploading] = useState(false)
//   const navigate = useNavigate()

//   const handleFileSelect = (file: File) => {
//     setSelectedFile(file)
//   }

//   const handleRemove = () => {
//     setSelectedFile(null)
//   }

//   const handleUpload = async () => {
//     if (!selectedFile) {
//       toast.error('Please select a file first')
//       return
//     }

//     setUploading(true)
//     try {
//       const response = await uploadImage(selectedFile)
//       toast.success('Image uploaded successfully!')
//       navigate(`/validation/${response.job_id}`)
//     } catch (error: any) {
//       toast.error(error.response?.data?.detail || 'Upload failed. Please try again.')
//     } finally {
//       setUploading(false)
//     }
//   }

//   return (
//     <div className="min-h-screen bg-gradient-to-b from-white to-purple-50 py-12">
//       <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
//         <Link
//           to="/"
//           className="inline-flex items-center text-purple-primary hover:text-purple-accent mb-8"
//         >
//           <ArrowLeft className="w-5 h-5 mr-2" />
//           Back to Home
//         </Link>

//         <div className="bg-white rounded-xl shadow-lg p-8">
//           <div className="text-center mb-8">
//             <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
//               <UploadIcon className="w-8 h-8 text-purple-primary" />
//             </div>
//             <h1 className="text-3xl font-bold text-gray-900 mb-2">
//               Upload Aadhaar Image
//             </h1>
//             <p className="text-gray-600">
//               Upload a clear image of your Aadhaar card for verification
//             </p>
//           </div>

//           <div className="mb-8">
//             <FileUploader
//               onFileSelect={handleFileSelect}
//               selectedFile={selectedFile}
//               onRemove={handleRemove}
//             />
//           </div>

//           <div className="bg-purple-50 rounded-lg p-6 mb-8">
//             <h3 className="font-semibold text-gray-900 mb-3">Instructions:</h3>
//             <ul className="space-y-2 text-sm text-gray-700">
//               <li>• Ensure image is clear and well-lit</li>
//               <li>• QR code should be visible</li>
//               <li>• Minimum resolution: 800×600 pixels</li>
//               <li>• Supported formats: JPEG, PNG, TIFF, BMP</li>
//               <li>• Maximum file size: 25 MB</li>
//             </ul>
//           </div>

//           <div className="flex justify-center">
//             <Button
//               size="lg"
//               onClick={handleUpload}
//               disabled={!selectedFile || uploading}
//               className="w-full md:w-auto"
//             >
//               {uploading ? 'Uploading...' : 'Start Verification'}
//             </Button>
//           </div>
//         </div>
//       </div>
//     </div>
//   )
// }
