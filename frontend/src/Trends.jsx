import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ComposedChart,
} from "recharts";

// Group entries by parameter, then by date
function groupByParameter(data) {
  const grouped = {};

  data.forEach((item) => {
    if (!grouped[item.name]) {
      grouped[item.name] = [];
    }

    // Parse range for reference lines
    let normalRange = null;
    if (item.range && item.range !== "N/A" && item.range.includes("-")) {
      const [low, high] = item.range.split("-").map(Number);
      normalRange = { low, high };
    }

    // Push { date, value, status, normalRange }
    grouped[item.name].push({
      date: item.date || "Unknown",
      value: item.value,
      status: item.status,
      severity: item.severity,
      normalRange,
      unit: item.unit,
    });
  });

  // Sort by date for each parameter
  Object.keys(grouped).forEach((param) => {
    grouped[param].sort((a, b) => new Date(a.date) - new Date(b.date));
  });

  return grouped;
}

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-800">{`Date: ${label}`}</p>
        <p className="text-blue-600">{`Value: ${data.value} ${data.unit}`}</p>
        <p className={`font-medium ${
          data.status === "Normal" ? "text-green-600" : "text-red-600"
        }`}>
          {`Status: ${data.status}`}
        </p>
        {data.severity && data.severity !== "None" && (
          <p className="text-orange-600">{`Severity: ${data.severity}`}</p>
        )}
        {data.normalRange && (
          <p className="text-gray-500 text-sm">
            {`Normal Range: ${data.normalRange.low}-${data.normalRange.high}`}
          </p>
        )}
      </div>
    );
  }
  return null;
};

// Get line color based on latest status
const getLineColor = (entries) => {
  const latestEntry = entries[entries.length - 1];
  switch (latestEntry.status) {
    case "Normal":
      return "#10b981"; // Green
    case "High":
      return "#f59e0b"; // Orange
    case "Low":
      return "#3b82f6"; // Blue
    case "Needs Attention":
    case "Abnormal":
      return "#ef4444"; // Red
    default:
      return "#6b7280"; // Gray
  }
};

function Trends({ data }) {
  const groupedData = groupByParameter(data);

  if (Object.keys(groupedData).length === 0) {
    return (
      <div className="mt-12">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-8">
          <div className="text-center">
            <div className="text-4xl mb-4">📈</div>
            <h3 className="text-xl font-medium text-gray-600 mb-2">No Trend Data Available</h3>
            <p className="text-gray-500">
              Upload multiple reports with the same parameters to see trends over time
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-12">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-green-50 to-blue-50 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            📈 Health Trends Analysis
            <span className="ml-3 text-sm font-normal bg-green-100 text-green-800 px-2 py-1 rounded-full">
              {Object.keys(groupedData).length} parameter{Object.keys(groupedData).length !== 1 ? 's' : ''}
            </span>
          </h2>
          <p className="text-gray-600 mt-1">Track your health parameters over time</p>
        </div>

        <div className="p-6 space-y-8">
          {Object.entries(groupedData).map(([paramName, entries]) => {
            const lineColor = getLineColor(entries);
            const hasNormalRange = entries.some(entry => entry.normalRange);
            const normalRange = entries.find(entry => entry.normalRange)?.normalRange;

            return (
              <div key={paramName} className="bg-gray-50 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-800">{paramName}</h3>
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      {entries.length} reading{entries.length !== 1 ? 's' : ''}
                    </span>
                    <div className="flex items-center">
                      <div 
                        className="w-3 h-3 rounded-full mr-2" 
                        style={{ backgroundColor: lineColor }}
                      ></div>
                      <span className="text-sm font-medium text-gray-700">
                        Latest: {entries[entries.length - 1].status}
                      </span>
                    </div>
                  </div>
                </div>

                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart
                    data={entries}
                    margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <YAxis 
                      domain={["auto", "auto"]} 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    
                    {/* Normal range reference lines */}
                    {hasNormalRange && normalRange && (
                      <>
                        <ReferenceLine 
                          y={normalRange.low} 
                          stroke="#10b981" 
                          strokeDasharray="5 5" 
                          label={{ value: "Normal Low", position: "insideTopRight" }}
                        />
                        <ReferenceLine 
                          y={normalRange.high} 
                          stroke="#10b981" 
                          strokeDasharray="5 5" 
                          label={{ value: "Normal High", position: "insideTopRight" }}
                        />
                      </>
                    )}
                    
                    {/* Trend line */}
                    <Line
                      type="monotone"
                      dataKey="value"
                      name={`${paramName} (${entries[0].unit})`}
                      stroke={lineColor}
                      strokeWidth={3}
                      dot={{ fill: lineColor, strokeWidth: 2, r: 6 }}
                      activeDot={{ r: 8, stroke: lineColor, strokeWidth: 2 }}
                    />
                  </ComposedChart>
                </ResponsiveContainer>

                {/* Trend Summary */}
                <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Latest Value:</span>
                      <span className="ml-2 font-semibold text-gray-900">
                        {entries[entries.length - 1].value} {entries[entries.length - 1].unit}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Status:</span>
                      <span className={`ml-2 font-semibold ${
                        entries[entries.length - 1].status === "Normal" ? "text-green-600" : "text-red-600"
                      }`}>
                        {entries[entries.length - 1].status}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Trend:</span>
                      <span className="ml-2 font-semibold text-gray-900">
                        {entries.length >= 2 ? (
                          entries[entries.length - 1].value > entries[entries.length - 2].value 
                            ? "↗️ Increasing" 
                            : entries[entries.length - 1].value < entries[entries.length - 2].value 
                              ? "↘️ Decreasing" 
                              : "→ Stable"
                        ) : "→ Single Reading"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default Trends;
