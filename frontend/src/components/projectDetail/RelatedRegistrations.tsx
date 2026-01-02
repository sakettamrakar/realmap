import type { ProjectDetail } from "../../types/projects";

interface Props {
    project: ProjectDetail;
    onSelectProject?: (projectId: number) => void;
}

export function RelatedRegistrations({ project, onSelectProject }: Props) {
    const { other_registrations } = project.project;

    if (!other_registrations || other_registrations.length === 0) {
        return null;
    }

    return (
        <div className="related-registrations mt-6 px-4">
            <h3 className="text-lg font-semibold mb-3">Other Phases / Registrations</h3>
            <div className="space-y-2">
                {other_registrations.map((reg) => (
                    <div 
                        key={reg.project_id} 
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200 hover:border-blue-300 transition-colors cursor-pointer"
                        onClick={() => onSelectProject?.(reg.project_id)}
                    >
                        <div>
                            <div className="font-medium text-sm">{reg.rera_number}</div>
                            <div className="text-xs text-gray-500">
                                {reg.status} • Registered: {reg.registration_date || 'N/A'}
                            </div>
                        </div>
                        <button className="text-blue-600 text-xs font-medium hover:underline">
                            View Details →
                        </button>
                    </div>
                ))}
            </div>
            <p className="text-xs text-gray-400 mt-2 italic">
                These registrations belong to the same physical project.
            </p>
        </div>
    );
}
