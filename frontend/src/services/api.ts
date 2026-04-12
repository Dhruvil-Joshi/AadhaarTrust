import axios from 'axios'
import { API_BASE_URL } from '../config/constants'
import type {
  UploadResponse,
  StatusResponse,
  ResultsResponse,
} from '../types/api.types'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const uploadImage = async (frontFile: File, backFile?: File): Promise<UploadResponse> => {
  const formData = new FormData()
  formData.append('front_file', frontFile)
  if (backFile) {
    formData.append('back_file', backFile)
  }

  const { data } = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return data
}

export const getStatus = async (jobId: string): Promise<StatusResponse> => {
  const { data } = await api.get<StatusResponse>(`/status/${jobId}`)
  return data
}

export const getResults = async (jobId: string): Promise<ResultsResponse> => {
  const { data } = await api.get<ResultsResponse>(`/results/${jobId}`)
  return data
}

export const downloadFile = async (jobId: string, fileType: string): Promise<Blob> => {
  const { data } = await api.get(`/download/${jobId}/${fileType}`, {
    responseType: 'blob',
  })
  return data
}

export default api
// import axios from 'axios'
// import { API_BASE_URL } from '../config/constants'
// import type {
//   UploadResponse,
//   StatusResponse,
//   ResultsResponse,
// } from '../types/api.types'

// const api = axios.create({
//   baseURL: API_BASE_URL,
//   headers: {
//     'Content-Type': 'application/json',
//   },
// })

// export const uploadImage = async (file: File): Promise<UploadResponse> => {
//   const formData = new FormData()
//   formData.append('file', file)
  
//   const { data } = await api.post<UploadResponse>('/upload', formData, {
//     headers: {
//       'Content-Type': 'multipart/form-data',
//     },
//   })
  
//   return data
// }

// export const getStatus = async (jobId: string): Promise<StatusResponse> => {
//   const { data } = await api.get<StatusResponse>(`/status/${jobId}`)
//   return data
// }

// export const getResults = async (jobId: string): Promise<ResultsResponse> => {
//   const { data } = await api.get<ResultsResponse>(`/results/${jobId}`)
//   return data
// }

// export const downloadFile = async (jobId: string, fileType: string): Promise<Blob> => {
//   const { data } = await api.get(`/download/${jobId}/${fileType}`, {
//     responseType: 'blob',
//   })
//   return data
// }

// export default api
