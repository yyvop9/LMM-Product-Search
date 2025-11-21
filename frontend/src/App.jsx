import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ProductDetailPage from './pages/ProductDetailPage';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="app-header">
        <Link to="/" style={{ textDecoration: 'none', color: '#1a1a1a' }}>
          <h1>Modify (LMM AI 제품 검색)</h1>
        </Link>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/product/:productId" element={<ProductDetailPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;