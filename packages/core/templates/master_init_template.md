# Master Init Template

Project: {{project_name}}

{{#if description}}
{{description}}
{{/if}}

{{#if features.database}}
## Database
Use {{features.database}} with ORM setup.
{{/if}}

{{#if features.auth}}
## Authentication
Implement {{features.auth}} based auth.
{{/if}}

{{#if features.ci_cd}}
## CI/CD
Include pipeline configuration.
{{/if}}

{{#if features.monitoring}}
## Monitoring
Set up monitoring tools.
{{/if}}

{{#if features.testing}}
## Testing
Add {{features.testing}} with example tests.
{{/if}}

{{#if features.logging}}
## Logging
Configure {{features.logging}} for the project.
{{/if}}
