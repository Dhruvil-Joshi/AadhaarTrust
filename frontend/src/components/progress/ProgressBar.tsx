import { motion } from 'framer-motion'

interface ProgressBarProps {
  percentage: number
  label?: string
}

export default function ProgressBar({ percentage, label }: ProgressBarProps) {
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm font-medium text-purple-primary">{percentage}%</span>
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="h-full bg-gradient-to-r from-purple-primary to-purple-accent rounded-full"
        />
      </div>
    </div>
  )
}
