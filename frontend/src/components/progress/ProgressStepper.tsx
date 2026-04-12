import { Check, Loader2 } from 'lucide-react'
import { STAGES } from '../../config/constants'



interface ProgressStepperProps {
  currentStage: string
}
// currentStage = aadhaar_verhoeff_check
export default function ProgressStepper({ currentStage }: ProgressStepperProps) {
  // currentStage = 'aadhaar_verhoeff_check'

  const getStepStatus = (stageId: string): 'completed' | 'active' | 'pending' => {
    const currentIndex = STAGES.findIndex(s => s.id === currentStage)
    const stepIndex = STAGES.findIndex(s => s.id === stageId)

    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'active'
    return 'pending'
  }

  return (
    <div className="w-full">
    <div className="flex w-full">
  {STAGES.map((stage, index) => {
    const status = getStepStatus(stage.id)
    const isLast = index === STAGES.length - 1

    return (
      <div key={stage.id} className="flex-1 flex flex-col items-center">
        
        {/* Top: circle + line */}
        <div className="flex items-center w-full">
          
          {/* Circle */}
          <div className="relative flex items-center justify-center">
            {status === 'active' && (
              <div className="absolute w-12 h-12 rounded-full bg-purple-400 animate-ping opacity-75" />
            )}

            <div className={`w-12 h-12 rounded-full flex items-center justify-center
              ${status === 'completed'
                ? 'bg-emerald-500 text-white'
                : status === 'active'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-400'
              }`}>
              {status === 'completed' ? (
                <Check className="w-6 h-6" />
              ) : status === 'active' ? (
                <Loader2 className="w-6 h-6 animate-spin" />
              ) : (
                index + 1
              )}
            </div>
          </div>

          {/* Line */}
          {!isLast && (
            <div className={`flex-1 h-1 mx-2
              ${status === 'completed' ? 'bg-emerald-500' : 'bg-gray-200'}
            `} />
          )}
        </div>

        {/* Label */}
        <p className ={`mt-2 text-sm text-left w-full break-words
            mt-2 text-sm text-left w-24 break-words
          ${status === 'active' ? 'text-purple-600' : 'text-gray-500'}
        `}>
          {stage.label}
        </p>
      </div>
    )
  })}
</div>  
    </div>
  )
}
