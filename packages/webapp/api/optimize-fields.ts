import { NextRequest, NextResponse } from 'next/server';
import { optimizeFields, OptimizeRequest } from '@/lib/optimizeFields';

export async function POST(req: NextRequest) {
  try {
    const body = (await req.json()) as OptimizeRequest;
    if (!body || !Array.isArray(body.fields)) {
      return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
    }
    const result = optimizeFields(body);
    return NextResponse.json({ fields: result });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Internal error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
