import { NextRequest } from "next/server";
import { POST as dryRun } from "@/api/dry-run";

export async function POST(req: NextRequest) {
  return dryRun(req);
}
