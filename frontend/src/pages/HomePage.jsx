import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom'; // (!!!) Link로 수정
import '../App.css'; // (CSS 경로 수정 ../)

const API_URL = import.meta.env.VITE_API_BASE_URL;

function HomePage() {
  // (기존 App.jsx의 state와 함수들 전부 복사)
  const [query, setQuery] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleTextSearch = async () => {
    // ... (기존 코드와 100% 동일)
    if (!query) return;
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const response = await axios.post(`${API_URL}/search/text`, {
        query: query,
        top_k: 12
      });
      setResults(response.data);
    } catch (err) {
      setError("텍스트 검색 중 오류가 발생했습니다.");
      console.error(err);
    }
    setLoading(false);
  };

  const handleImageSearch = async () => {
    // ... (기존 코드와 100% 동일)
    if (!selectedFile) return;
    setLoading(true);
    setError(null);
    setResults([]);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("top_k", 12);
    try {
      const response = await axios.post(`${API_URL}/search/image`, formData, {
        headers: { 'Content-Type': 'multipart-form-data' }
      });
      setResults(response.data);
    } catch (err) {
      setError("이미지 검색 중 오류가 발생했습니다.");
      console.error(err);
    }
    setLoading(false);
  };

  // (!!!) [수정] 연관 상품 검색 함수는 이제 필요 없음
  // (상세 페이지로 이동할 것이기 때문)
  // const handleRelatedSearch = ... (이 함수는 삭제!)

  return (
    // (기존 App.jsx의 return문에서 <div className="App">만 뺀 내용)
    <>
      <div className="search-controls">
        <div className="search-box">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="예: 파란색 셔츠, 겨울 후드티"
          />
          <button onClick={handleTextSearch} disabled={loading}>
            텍스트로 검색
          </button>
        </div>
        <div className="search-box">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setSelectedFile(e.target.files[0])}
          />
          <button onClick={handleImageSearch} disabled={!selectedFile || loading}>
            이미지로 검색
          </button>
        </div>
      </div>

      <hr />

      <div className="results-container">
        {loading && <p className="status-message">검색 중입니다...</p>}
        {error && <p className="status-message error">{error}</p>}
        
        {results.length === 0 && !loading && !error && (
          <div className="info-message">
            <p>텍스트로 원하는 스타일을 검색하거나, 이미지를 업로드하여 비슷한 상품을 찾아보세요.</p>
            {/* (!!!) [수정] 클릭 시 이동한다고 안내 */}
            <p>(검색 결과의 이미지를 클릭하면 상세 페이지로 이동합니다.)</p>
          </div>
        )}

        <div className="pinterest-grid">
          {results.map((product) => (
            // (!!!) [수정] onClick 이벤트를 <Link>로 변경
            <Link 
              to={`/product/${product.id}`} // (!!!) 상세 페이지 경로
              key={product.id} 
              className="result-item" 
              style={{ textDecoration: 'none' }} // 밑줄 제거
            >
              <img 
                src={`${API_URL}/static/images/${product.image_file}`} 
                alt={product.product_name}
              />
              <p><strong>{product.product_name || product.id}</strong></p>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}

export default HomePage;