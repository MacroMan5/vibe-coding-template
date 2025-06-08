import React from 'react';

interface Props {
  text: string;
}

export default function HelpIcon({ text }: Props) {
  return (
    <span
      className="ml-1 text-gray-500 cursor-pointer"
      title={text}
      aria-label={text}
    >
      ?
    </span>
  );
}
