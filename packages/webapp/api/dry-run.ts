import { spawn } from "child_process";
import { NextRequest, NextResponse } from "next/server";
import path from "path";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const body = await req.json();
  const repoRoot = path.resolve(__dirname, "..", "..", "..");
  
  // Extract project name from request body, default to "my-project" if not provided
  const projectName = body.project_name || "my-project";
  
  // Create a comprehensive config JSON that matches what the workflow expects
  const configData = {
    project_name: projectName,
    project_description: body.description || `Generated project: ${projectName}`,
    architecture_style: body.architecture_style || "monolith",
    cloud_provider: body.cloud_provider || "aws",
    backend_stack: body.tech_stack?.backend || body.backend_stack || "node",
    frontend_stack: body.tech_stack?.frontend || body.frontend_stack || "react",
    database_type: body.tech_stack?.database || body.database_type || "postgres",
    auth_type: body.auth_type || "jwt",
    deploy_target: body.deploy_target || "docker",
    core_features: Array.isArray(body.core_features) ? body.core_features : (body.core_features ? [body.core_features] : []),
    nice_to_have_features: Array.isArray(body.nice_to_have_features) ? body.nice_to_have_features : (body.nice_to_have_features ? [body.nice_to_have_features] : []),
    final_product_vision: body.final_product_vision || body.requirements || "",
    performance: body.performance || "",
    compliance_targets: body.compliance_targets || "",
    third_party_integrations: body.third_party_integrations || "",
    ...body // Include any additional fields from the request
  };

  // Use Python to call the workflow directly for better control over configuration
  const pythonScript = `
import sys
import json
import os
from pathlib import Path
sys.path.insert(0, '${path.join(repoRoot, 'packages/core/src')}')

from vibe_core.workflows.generate import GenerationWorkflow, WorkflowOptions

# Get config from command line argument
config_json = sys.argv[1]

# Create workflow options
options = WorkflowOptions(
    config_json=config_json,
    dry_run=True,
    json_output=True,
    verbose=False
)

# Set the base directory to VIBE-CODING-INIT so it can find templates/
vibe_init_dir = Path('${repoRoot}') / 'VIBE-CODING-INIT'
workflow = GenerationWorkflow(base_dir=vibe_init_dir)
result = workflow.run(options)

# Output the result as JSON
if result.success and result.output_data:
    print(json.dumps(result.output_data))
elif result.success and result.generation_result:
    # Fallback: create preview data from generation result
    preview_data = {
        "steps": result.generation_result.files_created or [],
        "summary": "Dry run completed successfully"
    }
    print(json.dumps(preview_data))
else:
    error_data = {"error": result.errors[0] if result.errors else "Unknown error"}
    print(json.dumps(error_data))
`;

  return new Promise<NextResponse>((resolve) => {
    const python = spawn("python3", ["-c", pythonScript, JSON.stringify(configData)], {
      cwd: repoRoot,
      stdio: ["pipe", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    python.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    python.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    python.on("close", (code) => {
      if (code !== 0) {
        console.error("Python script error:", stderr);
        resolve(NextResponse.json({ error: `Python execution failed: ${stderr}` }, { status: 500 }));
        return;
      }

      try {
        const data = JSON.parse(stdout.trim());
        if (data.error) {
          resolve(NextResponse.json({ error: data.error }, { status: 500 }));
        } else {
          resolve(NextResponse.json({ preview: data }));
        }
      } catch {
        console.error("Failed to parse python output:", stdout);
        console.error("Stderr:", stderr);
        resolve(
          NextResponse.json({ 
            error: "Failed to parse workflow output", 
            output: stdout,
            stderr: stderr 
          }, { status: 500 })
        );
      }
    });
  });
}
