import { POST } from '../api/optimize-fields';

const request = (body: any) => ({ json: async () => body } as any);

describe('optimize-fields endpoint', () => {
  it('optimizes long descriptions', async () => {
    const reqBody = {
      context: 'demo',
      fields: [
        { id: '1', type: 'long_description', content: 'text    with spaces' },
        { id: '2', type: 'short', content: 'skip' }
      ]
    };
    const res = await POST(request(reqBody));
    const data = await res.json();
    expect(data.fields).toHaveLength(1);
    expect(data.fields[0].optimized).toBe('text with spaces');
  });

  it('handles invalid payload', async () => {
    const res = await POST(request({ bad: true }));
    expect(res.status).toBe(400);
  });
});
