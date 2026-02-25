interface ScoreDisplayProps {
  score: {
    overall: number;
    accuracy: number;
    fluency: number;
    completeness: number;
  };
}

export function ScoreDisplay({ score }: ScoreDisplayProps) {
  const getScoreClass = (value: number) => {
    if (value >= 90) return "score-excellent";
    if (value >= 70) return "score-good";
    if (value >= 50) return "score-fair";
    return "score-poor";
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Điểm số</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className={`text-3xl font-bold ${getScoreClass(score.overall)}`}>
            {score.overall}
          </p>
          <p className="text-sm text-gray-500">Tổng điểm</p>
        </div>
        <div className="text-center">
          <p className={`text-2xl font-semibold ${getScoreClass(score.accuracy)}`}>
            {score.accuracy}
          </p>
          <p className="text-sm text-gray-500">Độ chính xác</p>
        </div>
        <div className="text-center">
          <p className={`text-2xl font-semibold ${getScoreClass(score.fluency)}`}>
            {score.fluency}
          </p>
          <p className="text-sm text-gray-500">Độ trôi chảy</p>
        </div>
        <div className="text-center">
          <p className={`text-2xl font-semibold ${getScoreClass(score.completeness)}`}>
            {score.completeness}
          </p>
          <p className="text-sm text-gray-500">Hoàn thiện</p>
        </div>
      </div>
    </div>
  );
}
