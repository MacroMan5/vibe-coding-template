import { POST as generate } from "@/api/generate-project";
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  return generate(req);
}
