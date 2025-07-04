function Table({ data }) {
  const getStatusColor = (status) => {
    switch (status) {
      case "Normal":
        return "bg-green-100 text-green-800";
      case "High":
      case "Low":
        return "bg-yellow-100 text-yellow-800";
      case "Needs Attention":
      case "Abnormal":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "None":
        return "bg-green-100 text-green-700";
      case "Mild":
        return "bg-yellow-100 text-yellow-700";
      case "Moderate":
        return "bg-orange-100 text-orange-700";
      case "Severe":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case "None":
        return "✅";
      case "Mild":
        return "⚠️";
      case "Moderate":
        return "🔶";
      case "Severe":
        return "🔴";
      default:
        return "❓";
    }
  };

  return (
    <div className="mt-8">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            🧪 Lab Report Summary
            <span className="ml-3 text-sm font-normal bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              {data.length} result{data.length !== 1 ? 's' : ''}
            </span>
          </h2>
          <p className="text-gray-600 mt-1">Comprehensive analysis of your health parameters</p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Parameter
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Unit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Normal Range
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Severity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  AI Insight
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.map((item, i) => (
                <tr key={item.id || i} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{item.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-semibold text-gray-900">{item.value}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{item.unit}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{item.range}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(item.severity)}`}>
                      <span className="mr-1">{getSeverityIcon(item.severity)}</span>
                      {item.severity || "None"}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-700 max-w-xs">
                      <div className="group relative">
                        <div className="truncate">
                          {item.ai_insight || "No insight available"}
                        </div>
                        {item.ai_insight && item.ai_insight.length > 50 && (
                          <div className="absolute z-10 invisible group-hover:visible bg-gray-800 text-white text-xs rounded-lg px-3 py-2 bottom-full left-0 mb-2 w-64 shadow-lg">
                            {item.ai_insight}
                            <div className="absolute top-full left-4 w-2 h-2 bg-gray-800 rotate-45 transform -mt-1"></div>
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{item.date}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {data.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              <div className="text-4xl mb-4">🔬</div>
              <p>No lab results available</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Table;