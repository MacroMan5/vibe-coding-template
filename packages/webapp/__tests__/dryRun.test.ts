import { spawn } from 'child_process';
import { EventEmitter } from 'events';
import { POST } from '../api/dry-run';

jest.mock('child_process');
const mockSpawn = spawn as jest.MockedFunction<typeof spawn>;

describe('dry-run endpoint', () => {
  afterEach(() => mockSpawn.mockReset());

  it('returns preview json', async () => {
    const mockChild = new EventEmitter() as any;
    mockChild.stdout = new EventEmitter();
    mockChild.stderr = new EventEmitter();
    
    mockSpawn.mockReturnValue(mockChild);
    
    const req = { json: async () => ({}) } as any;
    const resPromise = POST(req as any);
    
    // Simulate successful response
    setTimeout(() => {
      mockChild.stdout.emit('data', '{"files":[]}');
      mockChild.emit('close', 0);
    }, 10);
    
    const res = await resPromise;
    const data = await res.json();
    expect(Array.isArray(data.preview.files)).toBe(true);
  });

  it('handles parse errors', async () => {
    const mockChild = new EventEmitter() as any;
    mockChild.stdout = new EventEmitter();
    mockChild.stderr = new EventEmitter();
    
    mockSpawn.mockReturnValue(mockChild);
    
    const req = { json: async () => ({}) } as any;
    const resPromise = POST(req as any);
    
    // Simulate invalid JSON response
    setTimeout(() => {
      mockChild.stdout.emit('data', 'oops');
      mockChild.emit('close', 0);
    }, 10);
    
    const res = await resPromise;
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.error).toContain('Failed to parse workflow output');
  });
});
