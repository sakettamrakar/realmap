import classNames from "classnames";
import type { ProjectSummary } from "../types/projects";

interface Props {
  open: boolean;
  shortlist: ProjectSummary[];
  onClose: () => void;
  onSelectProject: (projectId: number) => void;
  onRemove: (projectId: number) => void;
  compareSelection: number[];
  onToggleCompareSelection: (projectId: number) => void;
  onOpenCompare: () => void;
  warning?: string | null;
}

const ShortlistPanel = ({
  open,
  shortlist,
  onClose,
  onSelectProject,
  onRemove,
  compareSelection,
  onToggleCompareSelection,
  onOpenCompare,
  warning,
}: Props) => {
  return (
    <div className={classNames("shortlist-drawer", { open })} aria-hidden={!open}>
      <div className="shortlist-header">
        <div>
          <p className="eyebrow">Shortlist</p>
          <h3>Saved projects ({shortlist.length})</h3>
        </div>
        <button className="pill pill-muted" onClick={onClose} type="button">
          Close
        </button>
      </div>

      {warning && <div className="banner banner-warning">{warning}</div>}

      <div className="shortlist-body">
        {shortlist.length === 0 && (
          <p className="muted">Add projects from the list to build your shortlist.</p>
        )}
        {shortlist.map((project) => (
          <div key={project.project_id} className="shortlist-row">
            <div className="shortlist-info" onClick={() => onSelectProject(project.project_id)}>
              <p className="eyebrow">{project.district || "District unknown"}</p>
              <strong>{project.name}</strong>
              <p className="muted">{project.status || "Status unknown"}</p>
            </div>
            <div className="shortlist-actions">
              <label className="compare-checkbox">
                <input
                  type="checkbox"
                  checked={compareSelection.includes(project.project_id)}
                  onChange={() => onToggleCompareSelection(project.project_id)}
                  aria-label="Select for compare"
                />
                <span>Select</span>
              </label>
              <button
                type="button"
                className="ghost-button"
                onClick={() => onRemove(project.project_id)}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="shortlist-footer">
        <button
          type="button"
          className="pill"
          onClick={onOpenCompare}
          disabled={compareSelection.length < 2}
        >
          Compare ({compareSelection.length})
        </button>
        <p className="eyebrow">Pick 2–3 projects to compare side-by-side.</p>
      </div>
    </div>
  );
};

export default ShortlistPanel;
