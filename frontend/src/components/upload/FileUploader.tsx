import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X } from 'lucide-react'
import { MAX_FILE_SIZE } from '../../config/constants'

interface FileUploaderProps {
  onFileSelect: (file: File) => void
  selectedFile?: File | null
  onRemove?: () => void
  label?: string
}

export default function FileUploader({ onFileSelect, selectedFile, onRemove, label }: FileUploaderProps) {
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError(null)

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0]
      if (rejection.errors[0]?.code === 'file-too-large') {
        setError(`File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)}MB limit`)
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError('Invalid file type. Please upload JPEG, PNG, TIFF, or BMP images.')
      } else {
        setError('File upload failed. Please try again.')
      }
      return
    }

    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0])
    }
  }, [onFileSelect])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
    },
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  })

  if (selectedFile) {
    return (
      <div className="border-2 border-purple-primary rounded-xl p-6 bg-purple-50">
        {label && (
          <p className="text-xs font-semibold text-purple-primary uppercase tracking-wide mb-3">{label}</p>
        )}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-purple-primary rounded-lg flex items-center justify-center">
              <Upload className="w-8 h-8 text-white" />
            </div>
            <div>
              <p className="font-medium text-gray-900">{selectedFile.name}</p>
              <p className="text-sm text-gray-500">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
          {onRemove && (
            <button
              onClick={onRemove}
              className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div>
      {label && (
        <p className="text-xs font-semibold text-purple-primary uppercase tracking-wide mb-2">{label}</p>
      )}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragActive
            ? 'border-purple-primary bg-purple-50'
            : 'border-purple-light hover:border-purple-primary hover:bg-purple-50'
          }
        `}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center space-y-4">
          <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center">
            <Upload className="w-10 h-10 text-purple-primary" />
          </div>
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop your Aadhaar image here' : 'Drop your Aadhaar image here or click to browse'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              JPEG, PNG, TIFF, BMP (Max 25 MB)
            </p>
          </div>
        </div>
      </div>
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

// import { useCallback, useState } from 'react'
// import { useDropzone } from 'react-dropzone'
// import { Upload, X } from 'lucide-react'
// import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from '../../config/constants'

// interface FileUploaderProps {
//   onFileSelect: (file: File) => void
//   selectedFile?: File | null
//   onRemove?: () => void
// }

// export default function FileUploader({ onFileSelect, selectedFile, onRemove }: FileUploaderProps) {
//   const [error, setError] = useState<string | null>(null)

//   const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
//     setError(null)
    
//     if (rejectedFiles.length > 0) {
//       const rejection = rejectedFiles[0]
//       if (rejection.errors[0]?.code === 'file-too-large') {
//         setError(`File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)}MB limit`)
//       } else if (rejection.errors[0]?.code === 'file-invalid-type') {
//         setError('Invalid file type. Please upload JPEG, PNG, TIFF, or BMP images.')
//       } else {
//         setError('File upload failed. Please try again.')
//       }
//       return
//     }
    
//     if (acceptedFiles.length > 0) {
//       onFileSelect(acceptedFiles[0])
//     }
//   }, [onFileSelect])

//   const { getRootProps, getInputProps, isDragActive } = useDropzone({
//     onDrop,
//     accept: {
//       'image/*': ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
//     },
//     maxSize: MAX_FILE_SIZE,
//     multiple: false,
//   })

//   if (selectedFile) {
//     return (
//       <div className="border-2 border-purple-primary rounded-xl p-6 bg-purple-50">
//         <div className="flex items-center justify-between">
//           <div className="flex items-center space-x-4">
//             <div className="w-16 h-16 bg-purple-primary rounded-lg flex items-center justify-center">
//               <Upload className="w-8 h-8 text-white" />
//             </div>
//             <div>
//               <p className="font-medium text-gray-900">{selectedFile.name}</p>
//               <p className="text-sm text-gray-500">
//                 {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
//               </p>
//             </div>
//           </div>
//           {onRemove && (
//             <button
//               onClick={onRemove}
//               className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
//             >
//               <X className="w-5 h-5" />
//             </button>
//           )}
//         </div>
//       </div>
//     )
//   }

//   return (
//     <div>
//       <div
//         {...getRootProps()}
//         className={`
//           border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
//           transition-all duration-200
//           ${isDragActive
//             ? 'border-purple-primary bg-purple-50'
//             : 'border-purple-light hover:border-purple-primary hover:bg-purple-50'
//           }
//         `}
//       >
//         <input {...getInputProps()} />
//         <div className="flex flex-col items-center space-y-4">
//           <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center">
//             <Upload className="w-10 h-10 text-purple-primary" />
//           </div>
//           <div>
//             <p className="text-lg font-medium text-gray-900">
//               {isDragActive ? 'Drop your Aadhaar image here' : 'Drop your Aadhaar image here or click to browse'}
//             </p>
//             <p className="text-sm text-gray-500 mt-2">
//               JPEG, PNG, TIFF, BMP (Max 25 MB)
//             </p>
//           </div>
//         </div>
//       </div>
//       {error && (
//         <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
//           {error}
//         </div>
//       )}
//     </div>
//   )
// }
