/** @jest-environment jsdom */
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import TextAreaField from '../components/TextAreaField';
import DropdownField from '../components/DropdownField';
import React from 'react';

describe('Field components', () => {
  it('shows help icon in TextAreaField', () => {
    render(
      <TextAreaField
        name="desc"
        placeholder="desc"
        onChange={() => {}}
        helpText="help"
      />
    );
    expect(screen.getByLabelText('help')).toBeInTheDocument();
  });

  it('shows help icon in DropdownField', () => {
    render(
      <DropdownField
        name="sel"
        options={["one"]}
        placeholder="pick"
        onChange={() => {}}
        helpText="info"
      />
    );
    expect(screen.getByLabelText('info')).toBeInTheDocument();
  });
});
