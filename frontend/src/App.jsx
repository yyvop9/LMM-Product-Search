import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage'; // (!!!) 1. 새로 만들 페이지
import ProductDetailPage from './pages/ProductDetailPage'; // (!!!) 2. 새로 만들 페이지
import './App.css'; // (CSS는 그대로 둡니다)

function App() {
  return (
    <div className="App">
      {/* --- 1. 헤더 (모든 페이지 공통) --- */}
      <header className="app-header">
        {/* 로고를 누르면 홈으로 이동 */}
        <Link to="/" style={{ textDecoration: 'none', color: '#1a1a1a' }}>
          <h1>Modify (LMM AI 제품 검색)</h1>
        </Link>
      </header>

      {/* --- 2. 페이지 교체 영역 (핵심) --- */}
      <main>
        <Routes>
          {/* '/' 경로는 HomePage 컴포넌트를 보여줌 */}
          <Route path="/" element={<HomePage />} />
          
          {/* '/product/:id' 경로는 ProductDetailPage를 보여줌 */}
          <Route path="/product/:productId" element={<ProductDetailPage />} />
          
          {/* (나중에 관리자 페이지를 만든다면) */}
          {/* <Route path="/admin" element={<AdminPage />} /> */}
        </Routes>
      </main>
    </div>
  );
}

export default App;