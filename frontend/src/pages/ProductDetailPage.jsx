import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import '../App.css';

const API_URL = import.meta.env.VITE_API_BASE_URL;

function ProductDetailPage() {
  const { productId } = useParams();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const pRes = await axios.get(`${API_URL}/product/${productId}`);
        setProduct(pRes.data);
        const rRes = await axios.get(`${API_URL}/search/related/${productId}`, { params: { top_k: 5 } });
        setRelated(rRes.data);
      } catch (err) { console.error(err); }
      setLoading(false);
    };
    if (productId) fetchData();
  }, [productId]);

  if (loading || !product) return <p className="status-message">로딩 중...</p>;

  return (
    <div className="product-detail-container">
      <div className="main-product-section">
        <img src={`${API_URL}/static/images/${product.image_file}`} className="main-product-image" alt={product.product_name} />
        <div className="main-product-info">
          <p className="product-brand">{product.brand || "Brand"}</p>
          <h1>{product.product_name}</h1>
          <p className="product-price">{product.price?.toLocaleString()}원</p>
          <div className="product-meta-box">
             <div className="meta-row"><span className="meta-label">계절</span><span className="meta-value">{product.season}</span></div>
             <div className="meta-row"><span className="meta-label">색상</span><span className="meta-value">{product.color}</span></div>
             <div className="meta-row"><span className="meta-label">사이즈</span><span className="meta-value">{product.size}</span></div>
          </div>
          <div className="product-description">
            <h3>상세 설명</h3>
            <p>{product.description}</p>
          </div>
        </div>
      </div>
      <hr />
      <h3>이 상품과 비슷한 스타일</h3>
      <div className="pinterest-grid">
        {related.map((r) => (
          <Link to={`/product/${r.id}`} key={r.id} className="result-item" style={{ textDecoration: 'none' }}>
             <img src={`${API_URL}/static/images/${r.image_file}`} alt={r.product_name} />
             <div className="card-info">
               <p className="card-brand">{r.brand}</p>
               <p className="card-title"><strong>{r.product_name}</strong></p>
               <p className="card-price">{r.price?.toLocaleString()}원</p>
             </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
export default ProductDetailPage;