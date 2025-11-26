import type { ProjectDetail } from "../../types/projects";

interface Props {
    project: ProjectDetail;
}

export function ProjectSnapshot({ project }: Props) {
    const { project: p, location, pricing } = project;

    const items = [
        { label: "Project Type", value: p.project_type },
        { label: "RERA ID", value: p.rera_number },
        { label: "District", value: location?.district },
        { label: "Tehsil", value: location?.tehsil },
        { label: "Approved", value: p.registration_date },
        { label: "Completion", value: p.expected_completion },
    ];

    if (pricing?.unit_types && pricing.unit_types.length > 0) {
        // Could add unit summary here if needed, but keeping it simple for now
    }

    return (
        <div className="project-snapshot">
            {items.map((item) => (
                <div key={item.label} className="snapshot-item">
                    <span className="snapshot-label">{item.label}</span>
                    <span className="snapshot-value">{item.value || "N/A"}</span>
                </div>
            ))}
        </div>
    );
}
