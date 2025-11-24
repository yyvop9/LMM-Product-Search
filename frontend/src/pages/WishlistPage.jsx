import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Heart, Loader2, Image as ImageIcon } from 'lucide-react';
import { motion } from 'framer-motion';

const WishlistPage = () => {
  const navigate = useNavigate();
  const [wishlist, setWishlist] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // 찜 목록 데이터 불러오기
  const fetchWishlist = async () => {
    try {
      const response = await fetch('http://localhost:8000/wishlist/');
      if (response.ok) {
        const data = await response.json();
        setWishlist(data);
      }
    } catch (error) {
      console.error("Wishlist Fetch Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // 페이지 진입 시 로드
  useEffect(() => {
    fetchWishlist();
  }, []);
  
  // 찜 해제 핸들러
  const handleRemove = async (productId, e) => {
      // 부모 div의 클릭 이벤트(상세페이지 이동)가 발생하지 않도록 중단
      e.stopPropagation();
      
      try {
          // POST 요청은 토글(toggle) 역할을 하므로, 이미 찜한 상태에서 호출하면 삭제됨
          const res = await fetch(`http://localhost:8000/wishlist/${productId}`, { method: 'POST' });
          if (res.ok) {
              // 성공적으로 제거되면 목록을 다시 불러와서 UI 갱신
              fetchWishlist();
          }
      } catch (err) {
          console.error("Remove Error:", err);
      }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button 
            onClick={() => navigate('/home')} 
            className="p-2 mr-4 rounded-full bg-white/10 hover:bg-white/20 transition"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-500 to-purple-600">
            My Wishlist
          </h1>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="flex justify-center mt-20">
            <Loader2 className="animate-spin text-purple-500" size={32} />
          </div>
        ) : wishlist.length > 0 ? (
          // Masonry Grid Layout
          <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
            {wishlist.map((product) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ y: -5 }}
                onClick={() => navigate(`/product/${product.id}`)} // 카드 클릭 시 상세 이동
                className="break-inside-avoid relative group rounded-xl overflow-hidden bg-[#1a1a20] border border-white/5 cursor-pointer"
              >
                <img
                  src={`http://localhost:8000/static/images/${product.image_file}`}
                  alt={product.product_name}
                  className="w-full h-auto object-cover transition-transform duration-500 group-hover:scale-105"
                  onError={(e) => {e.target.src = "https://via.placeholder.com/300x400?text=No+Image"}}
                />
                
                {/* 찜 해제 버튼 (Overlay) */}
                <button
                    onClick={(e) => handleRemove(product.id, e)}
                    className="absolute top-3 right-3 p-2 bg-black/50 rounded-full text-pink-500 backdrop-blur-sm z-10 hover:bg-black/80 transition-colors shadow-lg"
                    title="Remove from wishlist"
                >
                    <Heart size={18} fill="currentColor" />
                </button>
                
                {/* Info */}
                <div className="p-4">
                  <h3 className="font-bold truncate text-gray-200">{product.product_name}</h3>
                  <p className="text-purple-400 text-sm font-medium mt-1">
                    {product.price?.toLocaleString()}원
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          // Empty State
          <div className="text-center text-gray-500 mt-32">
            <ImageIcon size={48} className="mx-auto mb-4 opacity-20" />
            <p className="text-lg">아직 찜한 상품이 없습니다.</p>
            <p className="text-sm mt-2 text-gray-600">
              마음에 드는 스타일을 발견하면 하트를 눌러보세요.
            </p>
            <button 
                onClick={() => navigate('/home')}
                className="mt-6 px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition"
            >
                Go to Search
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WishlistPage;