import type { ReactNode } from "react";

interface Props {
  title: string;
  eyebrow?: string;
  subtitle?: string;
  actions?: ReactNode;
}

const SectionHeader = ({ title, eyebrow, subtitle, actions }: Props) => {
  return (
    <div className="section-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {actions && <div className="section-actions">{actions}</div>}
    </div>
  );
};

export default SectionHeader;
