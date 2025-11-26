import classNames from "classnames";

interface Props {
  score?: number | null;
  status?: 'ok' | 'partial' | 'insufficient_data';
  reason?: string | string[] | Record<string, unknown>;
  className?: string;
  amenityScore?: number | null;
  locationScore?: number | null;
}

const normalizeScore = (score: number): number => {
  if (score <= 1) return score * 10;
  if (score > 10) return score / 10;
  return score;
};

const getBucket = (score: number | null | undefined, status?: string) => {
  if (status === 'insufficient_data' || score === undefined || score === null) return "unknown";

  const val = normalizeScore(score);

  if (val >= 8) return "excellent";
  if (val >= 6) return "good";
  if (val >= 4) return "average";
  return "weak";
};

const getLabel = (bucket: string, status?: string) => {
  if (status === 'insufficient_data' || status === 'partial') return "Incomplete data";
  switch (bucket) {
    case "excellent":
      return "Excellent";
    case "good":
      return "Good";
    case "average":
      return "Average";
    case "weak":
      return "Weak";
    default:
      return "N/A";
  }
};

const ScoreBadge = ({ score, status, reason, className, amenityScore, locationScore }: Props) => {
  const bucket = getBucket(score, status);
  const label = getLabel(bucket, status);
  const normalizedScore = score !== undefined && score !== null ? normalizeScore(score) : null;

  let tooltip = "";
  if (status === 'partial') {
    tooltip = `Partial Data${reason ? `: ${Array.isArray(reason) ? reason.join(", ") : reason}` : ""}`;
  } else if (status === 'insufficient_data') {
    tooltip = "Not enough data to compute score yet.";
  }

  if (amenityScore !== undefined || locationScore !== undefined) {
    if (tooltip) tooltip += "\n\n";
    if (amenityScore !== undefined && amenityScore !== null) {
      tooltip += `Amenity score: ${normalizeScore(amenityScore).toFixed(1)} / 10\n`;
    }
    if (locationScore !== undefined && locationScore !== null) {
      tooltip += `Location score: ${normalizeScore(locationScore).toFixed(1)} / 10`;
    }
  }

  const isNeutral = status === 'insufficient_data' || status === 'partial';

  return (
    <span className={classNames("badge", isNeutral ? "badge-neutral" : `badge-${bucket}`, className)} title={tooltip.trim()}>
      <span className="badge-dot" />
      <span>{label}</span>
      {!isNeutral && normalizedScore !== null && (
        <span className="badge-value">
          {normalizedScore.toFixed(1)}
        </span>
      )}
      {status === 'partial' && <span style={{ marginLeft: '4px' }}>⚠️</span>}
    </span>
  );
};

export default ScoreBadge;
