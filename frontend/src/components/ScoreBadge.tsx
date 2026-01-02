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
  if (status === 'insufficient_data') return "Incomplete";
  if (status === 'partial') return "Scoring Partial";
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

const getBucketStyles = (bucket: string, isNeutral: boolean) => {
  if (isNeutral) return "bg-slate-100 text-slate-600 border-slate-200";

  switch (bucket) {
    case "excellent":
      return "bg-emerald-50 text-emerald-700 border-emerald-200 ring-1 ring-emerald-500/10";
    case "good":
      return "bg-sky-50 text-sky-700 border-sky-200 ring-1 ring-sky-500/10";
    case "average":
      return "bg-orange-50 text-orange-700 border-orange-200 ring-1 ring-orange-500/10";
    case "weak":
      return "bg-rose-50 text-rose-700 border-rose-200 ring-1 ring-rose-500/10";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200 ring-1 ring-slate-500/10";
  }
}

const getDotColor = (bucket: string, isNeutral: boolean) => {
  if (isNeutral) return "bg-slate-400";
  switch (bucket) {
    case "excellent": return "bg-emerald-500";
    case "good": return "bg-sky-500";
    case "average": return "bg-orange-500";
    case "weak": return "bg-rose-500";
    default: return "bg-slate-400";
  }
}

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
  const styles = getBucketStyles(bucket, isNeutral);
  const dotColor = getDotColor(bucket, isNeutral);

  return (
    <span
      className={classNames(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all",
        styles,
        className
      )}
      title={tooltip.trim()}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{label}</span>
      {!isNeutral && normalizedScore !== null && (
        <span className="ml-1 opacity-75 font-bold">
          {normalizedScore.toFixed(1)}
        </span>
      )}
      {status === 'partial' && <span className="ml-1 text-xs opacity-75">⚠️</span>}
    </span>
  );
};

export default ScoreBadge;
