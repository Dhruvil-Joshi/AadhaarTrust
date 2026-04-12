export default function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }
  
  return (
    <div className="flex items-center justify-center">
      <div
        className={`${sizes[size]} border-4 border-purple-light border-t-purple-primary rounded-full animate-spin`}
      />
    </div>
  )
}
