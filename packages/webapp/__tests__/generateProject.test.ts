import { spawn } from 'child_process';
import { EventEmitter } from 'events';
import { POST } from '../api/generate-project';

jest.mock('child_process');
const mockSpawn = spawn as jest.MockedFunction<typeof spawn>;

describe('generate-project endpoint', () => {
  afterEach(() => {
    mockSpawn.mockReset();
  });

  it('returns result on success', async () => {
    const mockChild = new EventEmitter() as any;
    mockChild.stdout = new EventEmitter();
    mockChild.stderr = new EventEmitter();
    
    mockSpawn.mockReturnValue(mockChild);
    
    const req = { json: async () => ({ name: 'demo' }) } as any;
    const resPromise = POST(req as any);
    
    // Simulate successful response
    setTimeout(() => {
      mockChild.stdout.emit('data', '{"success": true, "result": {"success": true}}');
      mockChild.emit('close', 0);
    }, 10);
    
    const res = await resPromise;
    const data = await res.json();
    expect(data.result.success).toBe(true);
  });

  it('handles errors', async () => {
    const mockChild = new EventEmitter() as any;
    mockChild.stdout = new EventEmitter();
    mockChild.stderr = new EventEmitter();
    
    mockSpawn.mockReturnValue(mockChild);
    
    const req = { json: async () => ({}) } as any;
    const resPromise = POST(req as any);
    
    // Simulate error
    setTimeout(() => {
      mockChild.stderr.emit('data', 'Python execution failed');
      mockChild.emit('close', 1);
    }, 10);
    
    const res = await resPromise;
    const data = await res.json();
    expect(res.status).toBe(500);
    expect(data.error).toContain('Generation failed');
  });
});
