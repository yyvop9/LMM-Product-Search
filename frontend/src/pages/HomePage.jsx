import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import '../App.css';

const API_URL = import.meta.env.VITE_API_BASE_URL;

function HomePage() {
  const [query, setQuery] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (endpoint, payload, isFile=false) => {
    setLoading(true); setError(null); setResults([]);
    try {
      const config = isFile ? { headers: { 'Content-Type': 'multipart/form-data' } } : {};
      const res = await axios.post(`${API_URL}${endpoint}`, payload, config);
      setResults(res.data);
    } catch (err) {
      console.error(err);
      setError("검색 중 오류가 발생했습니다.");
    }
    setLoading(false);
  };

  return (
    <>
      <div className="search-controls">
        <div className="search-box">
          <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="예: 남자 여름 코디 추천해줘" />
          <div style={{ display: 'flex', gap: '5px' }}>
            <button onClick={() => handleSearch('/search/text', { query, top_k: 5 })}>검색</button>
            <button style={{ backgroundColor: '#6200ea' }} onClick={() => handleSearch('/search/smart', { query, top_k: 5 })}>✨ AI 추천</button>
          </div>
        </div>
        <div className="search-box">
          <input type="file" accept="image/*" onChange={(e) => setSelectedFile(e.target.files[0])} />
          <button onClick={() => {
             const fd = new FormData(); fd.append('file', selectedFile); fd.append('top_k', 5);
             handleSearch('/search/image', fd, true);
          }} disabled={!selectedFile}>이미지로 검색</button>
        </div>
      </div>
      <hr />
      <div className="results-container">
        {loading && <p className="status-message">AI가 분석 중입니다... 🤖</p>}
        {error && <p className="status-message error">{error}</p>}
        
        {results.length === 0 && !loading && !error && (
          <div className="info-message">
            <p><strong>[✨ AI 추천]</strong> 버튼을 누르면 문맥을 이해하여 추천합니다.</p>
            <p>예: "크리스마스 데이트룩 추천해줘"</p>
          </div>
        )}

        <div className="pinterest-grid">
          {results.map((p) => (
            <Link to={`/product/${p.id}`} key={p.id} className="result-item" style={{ textDecoration: 'none' }}>
              <img src={`${API_URL}/static/images/${p.image_file}`} alt={p.product_name} />
              <div className="card-info">
                <p className="card-title"><strong>{p.product_name}</strong></p>
                
                {/* (!!!) [추가] 메인 화면에 가격 표시 */}
                <p className="card-price" style={{ color: '#e60023', fontWeight: 'bold', margin: '5px 0 0 0' }}>
                  {p.price ? `${p.price.toLocaleString()}원` : ""}
                </p>
                
              </div>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
export default HomePage;