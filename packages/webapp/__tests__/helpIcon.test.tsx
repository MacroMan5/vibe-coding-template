/** @jest-environment jsdom */
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HelpIcon from '../components/HelpIcon';

describe('HelpIcon', () => {
  it('renders with tooltip', () => {
    render(<HelpIcon text="info" />);
    const icon = screen.getByLabelText('info');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute('title', 'info');
  });
});
