import classNames from "classnames";

interface Props {
  score?: number | null;
  className?: string;
}

const getBucket = (score?: number | null) => {
  if (score === undefined || score === null) return "unknown";
  if (score >= 0.75) return "high";
  if (score >= 0.5) return "medium";
  return "low";
};

const getLabel = (bucket: string) => {
  switch (bucket) {
    case "high":
      return "High";
    case "medium":
      return "Medium";
    case "low":
      return "Low";
    default:
      return "Unknown";
  }
};

const ScoreBadge = ({ score, className }: Props) => {
  const bucket = getBucket(score);
  const label = getLabel(bucket);

  return (
    <span className={classNames("badge", `badge-${bucket}` , className)}>
      <span className="badge-dot" />
      <span>{label}</span>
      {score !== undefined && score !== null && (
        <span className="badge-value">{score.toFixed(2)}</span>
      )}
    </span>
  );
};

export default ScoreBadge;
