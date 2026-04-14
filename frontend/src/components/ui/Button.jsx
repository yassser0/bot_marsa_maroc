import React from 'react';
import { cn } from '../../lib/utils';

const Button = React.forwardRef(
  ({ className, variant = 'primary', size = 'md', disabled, children, ...props }, ref) => {
    const variants = {
      primary: 'btn btn-primary',
      outline: 'btn btn-outline',
      ghost: 'btn btn-ghost',
      danger: 'btn btn-danger',
      success: 'btn btn-success',
    };
    const sizes = {
      sm: 'btn-sm',
      md: 'btn-md',
      lg: 'btn-lg',
      icon: 'btn-icon',
    };

    return (
      <button
        ref={ref}
        className={cn(variants[variant], sizes[size], disabled && 'btn-disabled', className)}
        disabled={disabled}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';

export { Button };
