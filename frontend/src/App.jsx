import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';

// 컴포넌트 임포트
import Sidebar from './components/Sidebar'; // [New] 사이드바 추가
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import ProductDetailPage from './pages/ProductDetailPage';
import AdminPage from './pages/AdminPage';
import WishlistPage from './pages/WishlistPage';

// [Layout] 사이드바를 포함하는 레이아웃 컴포넌트
const Layout = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-black text-white">
      {/* 사이드바는 고정 */}
      <Sidebar />
      {/* 메인 콘텐츠 영역 */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto h-screen scrollbar-hide">
        {children}
      </main>
    </div>
  );
};

// [ProtectedRoute] 로그인이 필요한 페이지 보호 (선택 사항, 현재는 간단히 구현)
const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  // 토큰이 없으면 로그인 페이지로 리다이렉트
  return token ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 1. 인증 페이지 (사이드바 없음) */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* 2. 메인 서비스 (사이드바 포함 레이아웃 적용) */}
        <Route path="/" element={
          <PrivateRoute>
            <Layout>
              <HomePage />
            </Layout>
          </PrivateRoute>
        } />

        {/* 기존 /home 경로도 /로 리다이렉트 처리하여 통일 */}
        <Route path="/home" element={<Navigate to="/" replace />} />

        {/* 3. 상세 페이지 */}
        <Route path="/product/:id" element={
          <PrivateRoute>
            <Layout>
              <ProductDetailPage />
            </Layout>
          </PrivateRoute>
        } />

        {/* 4. 관리자 페이지 */}
        <Route path="/admin" element={
          <PrivateRoute>
            <Layout>
              <AdminPage />
            </Layout>
          </PrivateRoute>
        } />

        {/* 5. 찜 목록 */}
        <Route path="/wishlist" element={
          <PrivateRoute>
            <Layout>
              <WishlistPage />
            </Layout>
          </PrivateRoute>
        } />

        {/* 잘못된 경로는 홈으로 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;