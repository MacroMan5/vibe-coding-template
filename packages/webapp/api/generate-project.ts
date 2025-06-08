import { spawn } from "child_process";
import { NextRequest, NextResponse } from "next/server";
import path from "path";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const body = await req.json();
  const repoRoot = path.resolve(__dirname, "..", "..", "..");
  
  // Extract project name from the request
  const projectName = body.project_name || body.name || "generated-project";
  
  // Create comprehensive config JSON with all webapp form fields
  const configData = {
    project_name: projectName,
    project_description: body.project_description || body.description || "",
    architecture_style: body.architecture_style || body.architecture || "layered",
    cloud_provider: body.cloud_provider || "aws",
    backend_stack: body.backend_stack || body.backend || "nodejs",
    frontend_stack: body.frontend_stack || body.frontend || "react",
    database_type: body.database_type || body.database || "postgresql",
    auth_type: body.auth_type || body.auth || "jwt",
    deploy_target: body.deploy_target || body.deployment || "docker",
    core_features: body.core_features || body.features || [],
    nice_to_have_features: body.nice_to_have_features || body.optional_features || [],
    final_product_vision: body.final_product_vision || body.vision || "",
    performance: body.performance || {},
    compliance_targets: body.compliance_targets || [],
    third_party_integrations: body.third_party_integrations || []
  };

  return new Promise<NextResponse>((resolve) => {
    const pythonScript = `
import sys
import os
import json

# Add the core package to Python path
sys.path.insert(0, os.path.join('${repoRoot}', 'packages', 'core', 'src'))

from vibe_core.workflows.generate import GenerationWorkflow, WorkflowOptions

try:
    config_json = '''${JSON.stringify(configData).replace(/'/g, "\\'")}'''
    options = WorkflowOptions(config_json=config_json, dry_run=False)
    
    # Set base directory to VIBE-CODING-INIT where templates are located
    from pathlib import Path
    vibe_init_dir = Path('${repoRoot}') / 'VIBE-CODING-INIT'
    workflow = GenerationWorkflow(base_dir=vibe_init_dir)
    result = workflow.run(options)
    
    # Output the result as JSON
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
    sys.exit(1)
`;

    const pythonProcess = spawn("python3", ["-c", pythonScript], {
      cwd: repoRoot,
      stdio: ["pipe", "pipe", "pipe"]
    });

    let stdout = "";
    let stderr = "";

    pythonProcess.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    pythonProcess.on("close", (code) => {
      if (code !== 0) {
        console.error("Python script error:", stderr);
        resolve(NextResponse.json({ 
          error: `Generation failed: ${stderr || "Unknown error"}` 
        }, { status: 500 }));
        return;
      }

      try {
        const result = JSON.parse(stdout.trim());
        if (result.success) {
          resolve(NextResponse.json({ result: result.result }));
        } else {
          resolve(NextResponse.json({ 
            error: result.error 
          }, { status: 500 }));
        }
      } catch (parseError) {
        console.error("Failed to parse Python output:", stdout, stderr);
        resolve(NextResponse.json({ 
          error: `Invalid response format: ${parseError}` 
        }, { status: 500 }));
      }
    });

    pythonProcess.on("error", (error) => {
      console.error("Failed to start Python process:", error);
      resolve(NextResponse.json({ 
        error: `Failed to start generation process: ${error.message}` 
      }, { status: 500 }));
    });
  });
}
