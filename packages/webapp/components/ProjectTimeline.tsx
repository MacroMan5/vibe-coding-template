interface Step {
  name: string;
  status: 'pending' | 'in-progress' | 'done';
}

export default function ProjectTimeline({ steps }: { steps: Step[] }) {
  return (
    <ul className="space-y-1 mt-4">
      {steps.map((s) => (
        <li key={s.name} className={s.status === 'done' ? 'text-green-600' : s.status === 'in-progress' ? 'text-blue-600' : ''}>
          {s.name}
        </li>
      ))}
    </ul>
  );
}

