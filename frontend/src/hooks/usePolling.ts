import { useEffect, useState } from 'react'
import { getStatus } from '../services/api'
import type { StatusResponse } from '../types/api.types'

export const usePolling = (jobId: string | null, interval = 2000) => {
  const [status, setStatus] = useState<StatusResponse | null>(null)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!jobId) return

    const poll = async () => {
      try {
        const data = await getStatus(jobId)
        setStatus(data)
        setError(null)

        // Stop polling if job is completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          return
        }
      } catch (err) {
        setError(err as Error)
      }
    }

    // Initial poll
    poll()

    // Set up interval
    const pollInterval = setInterval(poll, interval)

    return () => clearInterval(pollInterval)
  }, [jobId, interval])

  return { status, error }
}
