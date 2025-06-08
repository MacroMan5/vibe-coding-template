# JSON Generator Webapp

This Next.js app provides a simple form that sends your project details to the OpenAI API and returns a `project_config.json` file. It expects an `OPENAI_API_KEY` defined in a `.env` file at the repository root.

## Getting Started

Install dependencies using the root script and start the dev server:

```bash
../runinstall.sh
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and fill in the form to generate your configuration.

## Form Fields

The form collects the following information:

- **Project Name** – basic identifier for the project *(required)*
- **Type** – API, webapp or desktop *(required)*
- **Tech Stack** – preferred technologies *(required)*
- **Scale** – MVP or enterprise level *(required)*
- **Short Description** – high level idea *(required)*
- **Problem to Solve** – issue your product tackles *(required)*
- **Core Features** – must-have features list *(required)*
- **Nice-to-have Features** – optional extras *(required)*
- **Final Product Vision** – long term vision *(required)*
- **Project Goal** – overall objective
- **Target Users** – who will use the app
- **Value Proposition** – why your product matters
- **Roadmap Milestones** – short/medium term goals
- **Timeline** – expected delivery window
- **Business Model** – SaaS, freemium, etc.
- **Complexity Estimate** – simple/medium/high
- **Authentication Needs**
- **Database**
- **Third-party Integrations**
- **Compliance Targets**
- **Internationalisation** and **Languages**
- **Environments** – dev/staging/prod
- **Security Level** – base to critical
- **Performance Expectations**

## Field Mapping

The form names correspond directly to keys written in `project_config.json`:

| Form Label | JSON Key |
|------------|---------|
| Project Name | `project_name` |
| Type | `project_type` |
| Tech Stack | `backend_stack` |
| Core Features | `core_features` |
| Nice-to-have Features | `nice_to_have_features` |
| Final Product Vision | `final_product_vision` |
| Authentication Needs | `auth_type` |
| Database | `database_type` |
| Deployment Target | `deploy_target` |
| Architecture Style | `architecture_style` |
| Cloud Provider | `cloud_provider` |

## Execution Plan and Timeline

After generating `project_config.json` you can request a step-by-step plan via the `/api/plan-agent` endpoint. The frontend streams this plan and displays each step in the **ProjectTimeline** component. Once a plan is in place you can trigger architecture generation which will produce a zip archive under `VIBE-CODING-INIT/build/`.
