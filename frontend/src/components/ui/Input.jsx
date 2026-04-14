import React from 'react';
import { cn } from '../../lib/utils';

const Input = React.forwardRef(({ className, type = 'text', ...props }, ref) => (
  <input
    ref={ref}
    type={type}
    className={cn('glass-input', className)}
    {...props}
  />
));
Input.displayName = 'Input';

const Textarea = React.forwardRef(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn('glass-input glass-textarea', className)}
    {...props}
  />
));
Textarea.displayName = 'Textarea';

const Label = ({ className, ...props }) => (
  <label className={cn('input-label', className)} {...props} />
);
Label.displayName = 'Label';

const FormField = ({ label, hint, children, className }) => (
  <div className={cn('form-field', className)}>
    {label && <Label>{label}</Label>}
    {children}
    {hint && <span className="input-hint">{hint}</span>}
  </div>
);

export { Input, Textarea, Label, FormField };
