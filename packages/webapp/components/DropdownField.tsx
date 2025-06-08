import React from 'react';
import HelpIcon from './HelpIcon';

interface DropdownFieldProps {
  name: string;
  options: readonly string[];
  placeholder: string;
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  error?: string;
  helpText?: string;
}

export default function DropdownField({ name, options, placeholder, onChange, error, helpText }: DropdownFieldProps) {
  return (
    <div className="relative">
      <select
        className="w-full border rounded p-2"
        name={name}
        onChange={onChange}
        defaultValue=""
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      {helpText && <HelpIcon text={helpText} />}
      {error && <p className="text-red-600 text-xs">{error}</p>}
    </div>
  );
}
