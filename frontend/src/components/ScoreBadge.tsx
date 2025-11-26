import classNames from "classnames";

interface Props {
  score?: number | null;
  status?: 'ok' | 'partial' | 'insufficient_data';
  reason?: string | string[] | Record<string, unknown>;
  className?: string;
}

const getBucket = (score: number | null | undefined, status?: string) => {
  if (status === 'insufficient_data' || score === undefined || score === null) return "unknown";
  // Assuming 0-100 scale based on backend logic
  if (score >= 75) return "high";
  if (score >= 50) return "medium";
  return "low";
};

const getLabel = (bucket: string, status?: string) => {
  if (status === 'insufficient_data') return "N/A";
  switch (bucket) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
    default:
      return "N/A";
  }
};

const ScoreBadge = ({ score, status, reason, className }: Props) => {
  const bucket = getBucket(score, status);
  const label = getLabel(bucket, status);

  let tooltip: string | undefined;
  if (status === 'partial') {
    tooltip = `Partial Data${reason ? `: ${Array.isArray(reason) ? reason.join(", ") : reason}` : ""}`;
  } else if (status === 'insufficient_data') {
    tooltip = "Not enough data to compute score yet.";
  }

  return (
    <span className={classNames("badge", `badge-${bucket}`, className)} title={tooltip}>
      <span className="badge-dot" />
      <span>{label}</span>
      {bucket !== "unknown" && score !== undefined && score !== null && (
        <span className="badge-value">
          {score.toFixed(0)}
          {status === 'partial' && <span style={{ marginLeft: '4px' }}>⚠️</span>}
        </span>
      )}
    </span>
  );
};

export default ScoreBadge;
