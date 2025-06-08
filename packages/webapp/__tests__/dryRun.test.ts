import { POST } from '../api/dry-run';
import { execFile } from 'child_process';

jest.mock('child_process');
const mocked = execFile as jest.Mock;

describe('dry-run endpoint', () => {
  afterEach(() => mocked.mockReset());

  it('returns preview json', async () => {
    mocked.mockImplementation((c,a,o,cb) => cb(null, '{"files":[]}', ''));
    const req = { json: async () => ({}) } as any;
    const res = await POST(req as any);
    const data = await res.json();
    expect(Array.isArray(data.preview.files)).toBe(true);
  });

  it('handles parse errors', async () => {
    mocked.mockImplementation((c,a,o,cb) => cb(null, 'oops', ''));
    const req = { json: async () => ({}) } as any;
    const res = await POST(req as any);
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.error).toBe('Failed to parse preview');
  });
});
