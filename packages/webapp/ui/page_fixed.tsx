"use client";
import AdvancedConfigSection from "@/components/AdvancedConfigSection";
import DropdownField from "@/components/DropdownField";
import ProjectTimeline from "@/components/ProjectTimeline";
import TextAreaField from "@/components/TextAreaField";
import { generateArchitecture } from "@/lib/generateArchitecture";
import { generatePlan } from "@/lib/generatePlan";
import { useState } from "react";
import { z } from "zod";

const techStackOptions = [
  "Next.js",
  "NestJS",
  "Django",
  "Flask",
  "Rails",
] as const;
const authOptions = ["None", "JWT", "OAuth", "Session"] as const;
const databaseOptions = ["PostgreSQL", "MySQL", "MongoDB", "SQLite"] as const;
const deploymentOptions = [
  "Docker",
  "Kubernetes",
  "Serverless",
  "VMs",
] as const;

export default function Home() {
  const [formData, setFormData] = useState({
    project_name: "",
    project_type: "",
    backend_stack: "",
    scale: "",
    description: "",
    problem: "",
    core_features: "",
    nice_to_have_features: "",
    final_product_vision: "",
    project_goal: "",
    target_users: "",
    value_proposition: "",
    roadmap_milestones: "",
    timeline: "",
    business_model: "",
    complexity_estimate: "",
    architecture_style: "",
    cloud_provider: "",
    auth_type: "",
    database_type: "",
    deploy_target: "",
    third_party_integrations: "",
    compliance_targets: "",
    i18n: false,
    languages: "",
    environments: "",
    security_level: "",
    performance: "",
  });
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [zipUrl, setZipUrl] = useState<string | null>(null);
  const [archLoading, setArchLoading] = useState(false);
  const [planSteps, setPlanSteps] = useState<string[]>([]);

  const sanitize = (value: string) => value.replace(/[<>"'`]/g, "");

  const formSchema = z.object({
    project_name: z
      .string()
      .min(1, "Required")
      .max(100, "Too long"),
    project_type: z.string().min(1, "Required").max(100, "Too long"),
    backend_stack: z.enum(techStackOptions),
    scale: z.string().min(1, "Required").max(100, "Too long"),
    description: z.string().min(1, "Required").max(500, "Too long"),
    problem: z.string().min(1, "Required").max(500, "Too long"),
    core_features: z.string().min(1, "Required"),
    nice_to_have_features: z.string().min(1, "Required"),
    final_product_vision: z.string().min(1, "Required"),
    project_goal: z.string().max(200, "Too long").optional(),
    target_users: z.string().max(200, "Too long").optional(),
    value_proposition: z.string().max(500, "Too long").optional(),
    roadmap_milestones: z.string().max(500, "Too long").optional(),
    timeline: z.string().max(100, "Too long").optional(),
    business_model: z.string().max(100, "Too long").optional(),
    complexity_estimate: z.string().max(100, "Too long").optional(),
    architecture_style: z.string().max(100, "Too long").optional(),
    cloud_provider: z.string().max(100, "Too long").optional(),
    auth_type: z.enum(authOptions).optional(),
    database_type: z.enum(databaseOptions).optional(),
    deploy_target: z.enum(deploymentOptions).optional(),
    third_party_integrations: z.string().max(200, "Too long").optional(),
    compliance_targets: z.string().max(200, "Too long").optional(),
    i18n: z.boolean().optional(),
    languages: z.string().max(100, "Too long").optional(),
    environments: z.string().max(100, "Too long").optional(),
    security_level: z.string().max(100, "Too long").optional(),
    performance: z.string().max(100, "Too long").optional(),
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value, type, checked } = e.target as HTMLInputElement;
    const val = type === "checkbox" ? checked : value;
    setFormData({ ...formData, [name]: val });
    setFieldErrors({ ...fieldErrors, [name]: "" });
  };

  const handleSubmit = async () => {
    setError(null);
    setZipUrl(null);
    const sanitizedData = Object.fromEntries(
      Object.entries(formData).map(([k, v]) => [k, sanitize(v as string)])
    );

    const parse = formSchema.safeParse(sanitizedData);
    if (!parse.success) {
      const flattened = parse.error.flatten().fieldErrors;
      const errors: Record<string, string> = {};
      Object.entries(flattened).forEach(([key, fieldError]) => {
        if (fieldError && fieldError.length > 0) {
          errors[key] = fieldError[0];
        }
      });
      setFieldErrors(errors);
      setError("Please fix the highlighted fields");
      return;
    }

    setFieldErrors({});
    setLoading(true);
    const res = await fetch("/api/dry-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parse.data),
    });
    const data = await res.json();
    if (data.error) {
      setError(data.error);
    } else {
      setResponse(JSON.stringify(data.preview, null, 2));
    }
    setLoading(false);
  };

  const handleDownload = () => {
    if (!response) return;
    const blob = new Blob([response], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "project_config.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleGeneratePlan = async () => {
    if (!formData) return;
    try {
      const planRequest = {
        projectName: formData.project_name,
        description: formData.description,
        techStack: {
          backend: formData.backend_stack,
          frontend: formData.project_type,
          database: formData.database_type || "Not specified",
        },
        requirements: formData.problem,
      };
      const planResult = await generatePlan(planRequest);
      if (planResult.success && planResult.plan) {
        setPlanSteps(planResult.plan);
      } else {
        setError(planResult.error || "Plan generation failed");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Plan generation failed";
      setError(message);
    }
  };

  const handleGenerateArchitecture = async () => {
    setError(null);
    setArchLoading(true);
    try {
      const architectureRequest = {
        projectName: formData.project_name,
        description: formData.description,
        techStack: {
          backend: formData.backend_stack,
          frontend: formData.project_type,
          database: formData.database_type || "Not specified",
        },
        features: formData.core_features.split(',').map(f => f.trim()),
        requirements: formData.problem,
      };
      const architectureResult = await generateArchitecture(architectureRequest);
      if (architectureResult.success && architectureResult.files) {
        // Create a downloadable link for the generated files
        const blob = new Blob([JSON.stringify(architectureResult.files, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        setZipUrl(url);
      } else {
        setError(architectureResult.error || "Architecture generation failed");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Architecture generation failed";
      setError(message);
    }
    setArchLoading(false);
  };

  return (
    <div className="max-w-3xl mx-auto mt-12 p-4 font-sans">
      <div className="shadow-xl bg-white dark:bg-zinc-900 rounded p-6 space-y-4">
        <h2 className="text-2xl font-bold">Vibe Init Project Form</h2>
        <h3 className="font-semibold">Contexte</h3>
        <input
          className="w-full border rounded p-2"
          name="project_name"
          placeholder="Project Name"
          onChange={handleChange}
        />
        {fieldErrors.project_name && (
          <p className="text-red-600 text-xs">{fieldErrors.project_name}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="project_type"
          placeholder="Type (API / Web App / Desktop)"
          onChange={handleChange}
        />
        {fieldErrors.project_type && (
          <p className="text-red-600 text-xs">{fieldErrors.project_type}</p>
        )}
        <DropdownField
          name="backend_stack"
          options={techStackOptions}
          placeholder="Select Stack"
          onChange={handleChange}
          error={fieldErrors.backend_stack}
        />
        <input
          className="w-full border rounded p-2"
          name="scale"
          placeholder="Scale (MVP / Enterprise)"
          onChange={handleChange}
        />
        {fieldErrors.scale && (
          <p className="text-red-600 text-xs">{fieldErrors.scale}</p>
        )}
        <TextAreaField
          name="description"
          placeholder="Short Description"
          onChange={handleChange}
          error={fieldErrors.description}
          helpText="Brief overview of the project"
        />
        <TextAreaField
          name="problem"
          placeholder="Problem to Solve"
          onChange={handleChange}
          error={fieldErrors.problem}
          helpText="Describe the issue you aim to solve"
        />
        <h3 className="font-semibold">Features</h3>
        <TextAreaField
          name="core_features"
          placeholder="Core Features (comma separated)"
          onChange={handleChange}
          error={fieldErrors.core_features}
          helpText="Essential features separated by commas"
        />
        <TextAreaField
          name="nice_to_have_features"
          placeholder="Nice-to-have Features"
          onChange={handleChange}
          error={fieldErrors.nice_to_have_features}
          helpText="Optional improvements or stretch goals"
        />
        <TextAreaField
          name="final_product_vision"
          placeholder="Final Product Vision"
          onChange={handleChange}
          error={fieldErrors.final_product_vision}
          helpText="What the final product should look like"
        />
        <h3 className="font-semibold">Business</h3>
        <input
          className="w-full border rounded p-2"
          name="project_goal"
          placeholder="Project Goal"
          onChange={handleChange}
          title="Main objective of the project"
        />
        {fieldErrors.project_goal && (
          <p className="text-red-600 text-xs">{fieldErrors.project_goal}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="target_users"
          placeholder="Target Users"
          onChange={handleChange}
          title="Describe who will use this product"
        />
        {fieldErrors.target_users && (
          <p className="text-red-600 text-xs">{fieldErrors.target_users}</p>
        )}
        <TextAreaField
          name="value_proposition"
          placeholder="Value Proposition"
          onChange={handleChange}
          error={fieldErrors.value_proposition}
          helpText="Why users will choose your product"
        />
        <TextAreaField
          name="roadmap_milestones"
          placeholder="Roadmap Milestones"
          onChange={handleChange}
          error={fieldErrors.roadmap_milestones}
          helpText="Major milestones or phases"
        />
        <input
          className="w-full border rounded p-2"
          name="timeline"
          placeholder="Timeline"
          onChange={handleChange}
          title="Expected timeline or deadlines"
        />
        {fieldErrors.timeline && (
          <p className="text-red-600 text-xs">{fieldErrors.timeline}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="business_model"
          placeholder="Business Model"
          onChange={handleChange}
          title="How this project will generate revenue"
        />
        {fieldErrors.business_model && (
          <p className="text-red-600 text-xs">{fieldErrors.business_model}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="complexity_estimate"
          placeholder="Complexity Estimate"
          onChange={handleChange}
          title="Rough effort or difficulty"
        />
        {fieldErrors.complexity_estimate && (
          <p className="text-red-600 text-xs">{fieldErrors.complexity_estimate}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="architecture_style"
          placeholder="Architecture Style"
          onChange={handleChange}
          title="Monolithic, microservices, etc."
        />
        {fieldErrors.architecture_style && (
          <p className="text-red-600 text-xs">{fieldErrors.architecture_style}</p>
        )}
        <input
          className="w-full border rounded p-2"
          name="cloud_provider"
          placeholder="Cloud Provider"
          onChange={handleChange}
          title="Target hosting platform"
        />
        {fieldErrors.cloud_provider && (
          <p className="text-red-600 text-xs">{fieldErrors.cloud_provider}</p>
        )}
        <AdvancedConfigSection
          handleChange={handleChange}
          fieldErrors={fieldErrors}
          authOptions={authOptions}
          databaseOptions={databaseOptions}
          deploymentOptions={deploymentOptions}
        />
        <button
          className="bg-black text-white rounded px-4 py-2"
          disabled={loading}
          onClick={handleSubmit}
        >
          {loading ? "Generating..." : "Generate Config"}
        </button>
        {error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        {response && (
          <pre className="mt-4 bg-gray-900 text-green-400 p-4 rounded overflow-x-auto text-sm">
            {response}
          </pre>
        )}
        {response && planSteps.length === 0 && (
          <button
            className="mt-2 bg-purple-600 text-white px-3 py-1 rounded"
            onClick={handleGeneratePlan}
          >
            Generate Plan
          </button>
        )}
        {planSteps.length > 0 && (
          <ProjectTimeline
            steps={planSteps.map((name) => ({ name, status: 'pending' }))}
          />
        )}
        {response && (
          <button
            className="mt-2 bg-blue-600 text-white px-3 py-1 rounded"
            onClick={handleDownload}
          >
            Download JSON
          </button>
        )}
        {response && !zipUrl && (
          <button
            className="mt-2 bg-green-600 text-white px-3 py-1 rounded"
            onClick={handleGenerateArchitecture}
            disabled={archLoading}
          >
            {archLoading ? "Generating..." : "Generate Architecture"}
          </button>
        )}
        {zipUrl && (
          <a
            className="mt-2 bg-green-700 text-white px-3 py-1 rounded"
            href={zipUrl}
            download
          >
            Download Architecture
          </a>
        )}
      </div>
    </div>
  );
}
