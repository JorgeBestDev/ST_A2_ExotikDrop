import { useEffect, useState } from 'react'

export default function ReservationCountdown({
  expiresAt,
  serverOffset = 0,
  onExpire,
}: {
  expiresAt: string
  serverOffset?: number
  onExpire?: () => void
}) {
  const [secondsRemaining, setSecondsRemaining] = useState(() =>
    Math.max(0, Math.ceil((Date.parse(expiresAt) - (Date.now() + serverOffset)) / 1000)),
  )

  useEffect(() => {
    let notified = false
    const update = () => {
      const remaining = Math.max(0, Math.ceil((Date.parse(expiresAt) - (Date.now() + serverOffset)) / 1000))
      setSecondsRemaining(remaining)
      if (remaining === 0 && !notified) {
        notified = true
        onExpire?.()
      }
    }

    update()
    const intervalId = window.setInterval(update, 1000)
    return () => window.clearInterval(intervalId)
  }, [expiresAt, serverOffset, onExpire])

  const minutes = Math.floor(secondsRemaining / 60).toString().padStart(2, '0')
  const seconds = (secondsRemaining % 60).toString().padStart(2, '0')
  return <time aria-label={`${minutes} minutes and ${seconds} seconds remaining`}>{minutes}:{seconds}</time>
}
