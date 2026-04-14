import React from 'react';
import { cn } from '../../lib/utils';

const Badge = React.forwardRef(({ className, variant = 'default', ...props }, ref) => {
  const variants = {
    default: 'badge-default',
    success: 'badge-success',
    danger: 'badge-danger',
    warning: 'badge-warning',
    info: 'badge-info',
  };
  return (
    <span
      ref={ref}
      className={cn('badge', variants[variant] || variants.default, className)}
      {...props}
    />
  );
});
Badge.displayName = 'Badge';

export { Badge };
