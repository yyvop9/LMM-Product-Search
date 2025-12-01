import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, ArrowLeft, ShoppingBag } from 'lucide-react';
import { motion } from 'framer-motion';

const WishlistPage = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // 1. 위시리스트 목록 불러오기
  useEffect(() => {
    fetchWishlist();
  }, []);

  const fetchWishlist = async () => {
    try {
      const res = await fetch('http://localhost:8000/wishlist/');
      if (res.ok) {
        const data = await res.json();
        setProducts(data); // 백엔드가 이제 Product 리스트를 바로 줍니다.
      }
    } catch (err) {
      console.error("Failed to fetch wishlist:", err);
    } finally {
      setLoading(false);
    }
  };

  // 2. 찜 삭제 핸들러 (화면에서 바로 사라지게)
  const handleRemove = async (e, productId) => {
    e.stopPropagation(); // 카드 클릭 이벤트 전파 방지
    if (!window.confirm("정말 삭제하시겠습니까?")) return;

    try {
      const res = await fetch('http://localhost:8000/wishlist/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId }),
      });

      if (res.ok) {
        // UI에서 즉시 제거 (새로고침 없이)
        setProducts((prev) => prev.filter((p) => p.id !== productId));
      }
    } catch (err) {
      alert("삭제 실패");
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-20">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 p-4">
        <div className="max-w-6xl mx-auto flex items-center space-x-4">
          <button 
            onClick={() => navigate(-1)} 
            className="p-2 hover:bg-white/10 rounded-full transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Heart className="text-pink-500 fill-pink-500" size={20} />
            My Wishlist
            <span className="text-sm font-normal text-gray-500 ml-2">({products.length})</span>
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 mt-6">
        {loading ? (
          <div className="text-center text-gray-500 mt-20">Loading...</div>
        ) : products.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((product) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => navigate(`/product/${product.id}`)}
                className="relative group bg-[#1a1a20] rounded-xl overflow-hidden border border-white/5 cursor-pointer hover:border-pink-500/30 transition-all"
              >
                {/* 삭제 버튼 */}
                <button
                  onClick={(e) => handleRemove(e, product.id)}
                  className="absolute top-2 right-2 z-10 p-2 bg-black/50 hover:bg-pink-600 rounded-full text-white transition-colors"
                >
                  <Heart size={16} fill="currentColor" />
                </button>

                <img
                  src={`http://localhost:8000/static/images/${product.image_file}`}
                  alt={product.product_name}
                  className="w-full h-64 object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                  onError={(e) => {e.target.src = "https://via.placeholder.com/300?text=No+Image"}}
                />
                <div className="p-3">
                  <h3 className="font-medium text-gray-200 truncate">{product.product_name}</h3>
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-pink-400 text-sm font-bold">
                      {product.price?.toLocaleString()}원
                    </span>
                    <span className="text-[10px] text-gray-500 border border-gray-700 px-1.5 py-0.5 rounded">
                      {product.category || 'Item'}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          // 빈 화면 (Empty State)
          <div className="flex flex-col items-center justify-center h-[60vh] text-gray-500">
            <div className="p-6 bg-gray-900 rounded-full mb-4">
                <ShoppingBag size={48} className="opacity-20" />
            </div>
            <p className="text-lg font-medium">위시리스트가 비어있어요.</p>
            <button 
                onClick={() => navigate('/')}
                className="mt-6 px-6 py-2 bg-white text-black rounded-full font-bold hover:bg-gray-200 transition-colors"
            >
                상품 구경하러 가기
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WishlistPage;