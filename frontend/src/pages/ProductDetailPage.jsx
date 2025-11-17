// C:/LMM-Product-Search/frontend/src/pages/ProductDetailPage.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom'; // (!!!) Link 추가
import axios from 'axios';
import '../App.css'; // (!!!) [수정 1] CSS 임포트 추가 (UI 깨짐 해결)

const API_URL = import.meta.env.VITE_API_BASE_URL;

function ProductDetailPage() {
  const { productId } = useParams(); // URL에서 상품 ID 가져오기
  
  // [수정 2] state 추가
  const [product, setProduct] = useState(null); // 메인 상품 정보
  const [relatedProducts, setRelatedProducts] = useState([]); // 연관 상품 목록
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // [수정 3] API 호출 로직 (useEffect)
  useEffect(() => {
    // 상품 ID가 바뀔 때마다 (페이지 이동 시) 데이터를 새로 불러옴
    const fetchProductData = async () => {
      setLoading(true);
      setError(null);
      setProduct(null);
      setRelatedProducts([]);

      try {
        // --- API 호출 1: 메인 상품 정보 ---
        const productRes = await axios.get(`${API_URL}/product/${productId}`);
        setProduct(productRes.data);

        // --- API 호출 2: 연관 상품 목록 (아이디어 1) ---
        const relatedRes = await axios.get(`${API_URL}/search/related/${productId}`, {
          params: { top_k: 10 } // 연관 상품 10개
        });
        setRelatedProducts(relatedRes.data);

      } catch (err) {
        setError("상품 정보를 불러오는 데 실패했습니다.");
        console.error(err);
      }
      setLoading(false);
    };

    if (productId) {
      fetchProductData();
    }
  }, [productId]); // (!!!) productId가 바뀔 때마다 이 함수가 재실행됨

  // [수정 4] UI 렌더링
  if (loading) {
    return <p className="status-message">상품 정보를 불러오는 중...</p>;
  }

  if (error) {
    return <p className="status-message error">{error}</p>;
  }

  if (!product) {
    return <p className="status-message">상품이 없습니다.</p>;
  }

  return (
    <div className="product-detail-container">
      {/* --- 1. 메인 상품 정보 --- */}
      <div className="main-product-section">
        <img 
          src={`${API_URL}/static/images/${product.image_file}`} 
          alt={product.product_name}
          className="main-product-image"
        />
        <div className="main-product-info">
          <h2>{product.product_name}</h2>
          <p>{product.description || "상품 상세 설명이 없습니다."}</p>
          <p><strong>상품 ID:</strong> {product.id}</p>
        </div>
      </div>

      <hr />
      
      {/* --- 2. 연관 상품 목록 (아이디어 1) --- */}
      <h3>이 상품과 비슷한 추천 상품</h3>
      
      {/* (HomePage.jsx의 그리드 재활용) */}
      <div className="pinterest-grid">
        {relatedProducts.map((related) => (
          // (Link로 감싸서, 연관 상품을 누르면 그 상품의 상세 페이지로 또 이동)
          <Link 
            to={`/product/${related.id}`} // (!!!) 상세 페이지로 또 이동
            key={related.id} 
            className="result-item" 
            style={{ textDecoration: 'none' }}
          >
            <img 
              src={`${API_URL}/static/images/${related.image_file}`} 
              alt={related.product_name}
            />
            <p><strong>{related.product_name || related.id}</strong></p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default ProductDetailPage;