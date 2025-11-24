import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// 페이지 컴포넌트 임포트 (경로: src/pages/...)
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import ProductDetailPage from './pages/ProductDetailPage';
import AdminPage from './pages/AdminPage';
import WishlistPage from './pages/WishlistPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 1. 로그인 (기본 경로) */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* 2. 메인 검색 */}
        <Route path="/home" element={<HomePage />} />
        
        {/* 3. 상세 페이지 */}
        <Route path="/product/:id" element={<ProductDetailPage />} />

        {/* 4. 관리자 등록 */}
        <Route path="/admin" element={<AdminPage />} />

        {/* 5. 찜 목록 */}
        <Route path="/wishlist" element={<WishlistPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;