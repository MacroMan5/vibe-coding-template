import React from 'react';
import DropdownField from './DropdownField';

interface Props {
  handleChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => void;
  fieldErrors: Record<string, string>;
  authOptions: readonly string[];
  databaseOptions: readonly string[];
  deploymentOptions: readonly string[];
}

export default function AdvancedConfigSection({ handleChange, fieldErrors, authOptions, databaseOptions, deploymentOptions }: Props) {
  return (
    <>
      <h3 className="font-semibold">Advanced</h3>
        <DropdownField
          name="auth_type"
          options={authOptions}
          placeholder="Authentication Needs"
          onChange={handleChange}
          error={fieldErrors.auth_type}
          helpText="How users will authenticate"
        />
        <DropdownField
          name="database_type"
          options={databaseOptions}
          placeholder="Database"
          onChange={handleChange}
          error={fieldErrors.database_type}
          helpText="Primary database technology"
        />
      <input
        className="w-full border rounded p-2"
        name="third_party_integrations"
        placeholder="Third-party Integrations"
        onChange={handleChange}
        title="APIs or services to integrate"
      />
      {fieldErrors.third_party_integrations && (
        <p className="text-red-600 text-xs">{fieldErrors.third_party_integrations}</p>
      )}
        <DropdownField
          name="deploy_target"
          options={deploymentOptions}
          placeholder="Deployment Target"
          onChange={handleChange}
          error={fieldErrors.deploy_target}
          helpText="Where the app will run"
        />
      <input
        className="w-full border rounded p-2"
        name="performance"
        placeholder="Performance Expectations"
        onChange={handleChange}
        title="Key performance goals"
      />
      {fieldErrors.performance && (
        <p className="text-red-600 text-xs">{fieldErrors.performance}</p>
      )}
      <input
        className="w-full border rounded p-2"
        name="compliance_targets"
        placeholder="Compliance Targets"
        onChange={handleChange}
        title="Regulations or standards"
      />
      {fieldErrors.compliance_targets && (
        <p className="text-red-600 text-xs">{fieldErrors.compliance_targets}</p>
      )}
      <label className="flex items-center space-x-2">
        <input type="checkbox" name="i18n" onChange={handleChange} />
        <span>Internationalisation</span>
      </label>
      <input
        className="w-full border rounded p-2"
        name="languages"
        placeholder="Languages"
        onChange={handleChange}
        title="Supported languages"
      />
      {fieldErrors.languages && (
        <p className="text-red-600 text-xs">{fieldErrors.languages}</p>
      )}
      <input
        className="w-full border rounded p-2"
        name="environments"
        placeholder="Environments"
        onChange={handleChange}
        title="Development environments"
      />
      {fieldErrors.environments && (
        <p className="text-red-600 text-xs">{fieldErrors.environments}</p>
      )}
      <input
        className="w-full border rounded p-2"
        name="security_level"
        placeholder="Security Level"
        onChange={handleChange}
        title="Expected security requirements"
      />
      {fieldErrors.security_level && (
        <p className="text-red-600 text-xs">{fieldErrors.security_level}</p>
      )}
    </>
  );
}
