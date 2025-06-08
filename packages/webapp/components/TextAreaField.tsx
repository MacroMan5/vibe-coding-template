import React from 'react';

import HelpIcon from './HelpIcon';

interface TextAreaFieldProps {
  name: string;
  placeholder: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  error?: string;
  helpText?: string;
}

export default function TextAreaField({ name, placeholder, onChange, error, helpText }: TextAreaFieldProps) {
  return (
    <div className="relative">
      <textarea
        className="w-full border rounded p-2"
        name={name}
        placeholder={placeholder}
        onChange={onChange}
      />
      {helpText && (
        <HelpIcon text={helpText} />
      )}
      {error && <p className="text-red-600 text-xs">{error}</p>}
    </div>
  );
}
