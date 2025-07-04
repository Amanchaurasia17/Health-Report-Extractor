import { useState } from "react";
import axios from "axios";
import Table from "./Table";
import Trends from "./Trends";

function App() {
  const [data, setData] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const clearMessages = () => {
    setError(null);
    setSuccess(false);
  };

  const validateFile = (file) => {
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    const maxSize = 10 * 1024 * 1024;

    if (!allowedTypes.includes(file.type)) {
      throw new Error('Please select a valid PDF or image file (JPEG, PNG)');
    }
    
    if (file.size > maxSize) {
      throw new Error('File size must be less than 10MB');
    }
  };

  const handleFileChange = (e) => {
    clearMessages();
    const selectedFile = e.target.files[0];
    
    if (selectedFile) {
      try {
        validateFile(selectedFile);
        setFile(selectedFile);
      } catch (err) {
        setError(err.message);
        setFile(null);
        e.target.value = '';
      }
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    clearMessages();
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 seconds timeout
      });

      if (res.data && Array.isArray(res.data.data)) {
        setData((prev) => [...prev, ...res.data.data]);
        setSuccess(true);
        setFile(null);
        // Reset file input
        document.querySelector('input[type="file"]').value = '';
      } else {
        throw new Error('Invalid response format from server');
      }
    } catch (err) {
      console.error("Upload failed:", err);
      
      if (err.code === 'ECONNABORTED') {
        setError('Upload timeout. Please try again with a smaller file.');
      } else if (err.response?.status === 413) {
        setError('File too large. Please select a smaller file.');
      } else if (err.response?.status === 400) {
        setError('Invalid file format. Please select a PDF or image file.');
      } else if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else {
        setError('Upload failed. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const clearData = () => {
    setData([]);
    clearMessages();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🩺 Health Report Extractor
          </h1>
          <p className="text-gray-600">
            Upload your medical reports (PDF or images) to extract and analyze health data
          </p>
        </div>

        {/* Upload Section */}
        <div className="max-w-2xl mx-auto bg-white p-8 rounded-2xl shadow-lg border border-gray-200 mb-8">
          <div className="space-y-6">
            {/* File Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Health Report
              </label>
              <input
                type="file"
                accept="application/pdf,image/jpeg,image/png,image/jpg"
                onChange={handleFileChange}
                className="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors cursor-pointer hover:border-gray-400"
                disabled={loading}
              />
              <p className="text-sm text-gray-500 mt-1">
                Supported formats: PDF, JPEG, PNG (max 10MB)
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-red-600 font-medium">❌ Error:</span>
                  <span className="text-red-700 ml-2">{error}</span>
                </div>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <span className="text-green-600 font-medium">✅ Success:</span>
                  <span className="text-green-700 ml-2">File processed successfully!</span>
                </div>
              </div>
            )}

            {/* Selected File Info */}
            {file && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-900">Selected File:</p>
                    <p className="text-sm text-blue-700">{file.name}</p>
                    <p className="text-xs text-blue-600">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setFile(null);
                      clearMessages();
                      document.querySelector('input[type="file"]').value = '';
                    }}
                    className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={handleUpload}
                disabled={!file || loading}
                className={`flex-1 py-3 px-6 rounded-lg font-medium transition-all duration-200 ${
                  file && !loading
                    ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                    : "bg-gray-300 text-gray-500 cursor-not-allowed"
                }`}
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Processing...
                  </span>
                ) : (
                  "Upload & Extract Data"
                )}
              </button>
              
              {data.length > 0 && (
                <button
                  onClick={clearData}
                  disabled={loading}
                  className="py-3 px-6 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-colors"
                >
                  Clear Data
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Results Section */}
        {data.length > 0 && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                📊 Extracted Health Data
              </h2>
              <p className="text-gray-600">
                {data.length} record{data.length !== 1 ? 's' : ''} found
              </p>
            </div>
            
            <Table data={data} />
            <Trends data={data} />
          </div>
        )}

        {/* Empty State */}
        {data.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-medium text-gray-600 mb-2">No Data Yet</h3>
            <p className="text-gray-500">
              Upload a health report to get started with data extraction and analysis
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
