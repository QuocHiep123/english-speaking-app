interface ScoreRingProps {
  value: number | null;
  max?: number;
  label: string;
  gradientId: string;
  colorFrom: string;
  colorTo: string;
  size?: number;
  strokeWidth?: number;
}

function ScoreRing({
  value,
  max = 9,
  label,
  gradientId,
  colorFrom,
  colorTo,
  size = 140,
  strokeWidth = 10,
}: ScoreRingProps) {
  const displayValue = value ?? 0;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(Math.max(displayValue, 0), max);
  const dashOffset = circumference * (1 - clamped / max);
  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="-rotate-90"
          viewBox={`0 0 ${size} ${size}`}
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colorFrom} />
              <stop offset="100%" stopColor={colorTo} />
            </linearGradient>
          </defs>
          {/* Track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#f1f5f9"
            strokeWidth={strokeWidth}
          />
          {/* Progress arc */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Centered score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-slate-800">
            {value !== null ? clamped.toFixed(1) : "—"}
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
            / {max}
          </span>
        </div>
      </div>
      <span className="text-sm font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </span>
    </div>
  );
}

interface ScoreDisplayProps {
  lexicalScore: number | null;
  grammarScore: number | null;
}

export function ScoreDisplay({ lexicalScore, grammarScore }: ScoreDisplayProps) {
  return (
    <div className="rounded-2xl bg-white p-8 shadow-sm transition-shadow hover:shadow-md">
      <h3 className="mb-8 text-center text-lg font-bold tracking-tight text-slate-800">
        IELTS Band Scores
      </h3>
      <div className="flex items-center justify-center gap-12">
        <ScoreRing
          value={lexicalScore}
          label="Lexical Resource"
          gradientId="lexical-grad"
          colorFrom="#6366f1"
          colorTo="#3b82f6"
        />
        <ScoreRing
          value={grammarScore}
          label="Grammar"
          gradientId="grammar-grad"
          colorFrom="#10b981"
          colorTo="#14b8a6"
        />
      </div>
    </div>
  );
}
