import { POST } from '../api/generate-project';
import { execFile } from 'child_process';

jest.mock('child_process');
const mocked = execFile as jest.Mock;

describe('generate-project endpoint', () => {
  afterEach(() => {
    mocked.mockReset();
  });

  it('returns result on success', async () => {
    mocked.mockImplementation((c,a,o,cb) => cb(null, 'ok', ''));
    const req = { json: async () => ({ name: 'demo' }) } as any;
    const res = await POST(req as any);
    const data = await res.json();
    expect(data.result).toBe('ok');
  });

  it('handles errors', async () => {
    mocked.mockImplementation((c,a,o,cb) => cb(new Error('fail'), '', ''));
    const req = { json: async () => ({}) } as any;
    const res = await POST(req as any);
    const data = await res.json();
    expect(res.status).toBe(500);
    expect(data.error).toBe('fail');
  });
});
