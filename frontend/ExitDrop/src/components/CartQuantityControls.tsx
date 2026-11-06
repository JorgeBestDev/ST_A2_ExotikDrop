type CartQuantityControlsProps = {
  className: string
  quantity: number
  label: string
  decreaseLabel: string
  increaseLabel: string
  onDecrease: () => void
  onIncrease: () => void
  canIncrease: boolean
  disabled?: boolean
  onRemove?: () => void
  removeClassName?: string
}

export default function CartQuantityControls({
  className,
  quantity,
  label,
  decreaseLabel,
  increaseLabel,
  onDecrease,
  onIncrease,
  canIncrease,
  disabled = false,
  onRemove,
  removeClassName,
}: CartQuantityControlsProps) {
  return <div className={className} role="group" aria-label={label}>
    <button type="button" aria-label={decreaseLabel} disabled={disabled || quantity <= 1} onClick={onDecrease}>−</button>
    <span aria-live="polite">{quantity}</span>
    <button type="button" aria-label={increaseLabel} disabled={disabled || !canIncrease} onClick={onIncrease}>+</button>
    {onRemove && <button type="button" className={removeClassName} disabled={disabled} onClick={onRemove}>Remove</button>}
  </div>
}
