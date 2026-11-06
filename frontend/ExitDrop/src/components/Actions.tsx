import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link, type LinkProps } from 'react-router-dom'

export type ActionVariant = 'brown' | 'dark' | 'outline'

type ActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ActionVariant
  children: ReactNode
}

type ActionLinkProps = LinkProps & {
  variant?: ActionVariant
  children: ReactNode
}

function actionClass(variant: ActionVariant, className = '') {
  return `button button-${variant}${className ? ` ${className}` : ''}`
}

export function ActionButton({ variant = 'brown', className, children, ...props }: ActionButtonProps) {
  return <button type="button" className={actionClass(variant, className)} {...props}>{children}</button>
}

export function ActionLink({ variant = 'brown', className, children, ...props }: ActionLinkProps) {
  return <Link className={actionClass(variant, className)} {...props}>{children}</Link>
}
