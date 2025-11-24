import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShoppingBag, Heart } from 'lucide-react';
import { motion } from 'framer-motion';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  // 상태 관리
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [isLiked, setIsLiked] = useState(false); // 찜 상태
  const [loading, setLoading] = useState(true);

  // 1. 데이터 로드 (상품 정보 + 연관 상품 + 찜 여부)
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // 3개의 API를 동시에 호출 (병렬 처리로 속도 향상)
        const [prodRes, relRes, likeRes] = await Promise.all([
          fetch(`http://localhost:8000/product/${id}`),
          fetch(`http://localhost:8000/search/related/${id}?top_k=6`),
          fetch(`http://localhost:8000/wishlist/check/${id}`)
        ]);

        // 상품 정보 설정
        if (prodRes.ok) {
          setProduct(await prodRes.json());
        }
        
        // 연관 상품 설정
        if (relRes.ok) {
          setRelated(await relRes.json());
        }
        
        // 찜 여부 설정
        if (likeRes.ok) {
          const likeData = await likeRes.json();
          setIsLiked(likeData.is_liked);
        }
      } catch (err) {
        console.error("Data Fetch Error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    window.scrollTo(0, 0); // 페이지 이동 시 스크롤 맨 위로
  }, [id]);

  // 2. 찜하기 버튼 핸들러 (Toggle)
  const toggleLike = async () => {
    try {
      const res = await fetch(`http://localhost:8000/wishlist/${id}`, { 
        method: 'POST' 
      });
      
      if (res.ok) {
        const data = await res.json();
        setIsLiked(data.is_liked); // 서버 응답에 따라 하트 상태 변경
      }
    } catch (err) {
      console.error("Wishlist Toggle Error:", err);
      alert("찜하기 처리 중 오류가 발생했습니다.");
    }
  };

  // 로딩 화면
  if (loading) return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
      <div className="animate-pulse text-purple-500 font-medium">Loading Product...</div>
    </div>
  );
  
  // 상품 없음 화면
  if (!product) return (
    <div className="min-h-screen bg-[#050505] flex flex-col items-center justify-center text-white gap-4">
      <p className="text-lg text-gray-400">Product Not Found</p>
      <button 
        onClick={() => navigate('/home')} 
        className="px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition"
      >
        Go Home
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header (Back Button) */}
      <div className="p-6 sticky top-0 z-10 bg-[#050505]/80 backdrop-blur-sm">
        <button 
          onClick={() => navigate(-1)} 
          className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors"
        >
          <ArrowLeft size={24} />
        </button>
      </div>

      <div className="max-w-6xl mx-auto px-4 pb-20">
        <div className="flex flex-col md:flex-row gap-10">
          
          {/* Left: Main Image */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }} 
            animate={{ opacity: 1, x: 0 }} 
            className="w-full md:w-1/2"
          >
            <div className="rounded-3xl overflow-hidden border border-white/10 bg-[#1a1a20] shadow-2xl">
              <img 
                src={`http://localhost:8000/static/images/${product.image_file}`} 
                alt={product.product_name} 
                className="w-full h-auto object-cover"
                onError={(e) => {e.target.src = "https://via.placeholder.com/500x600?text=No+Image"}}
              />
            </div>
          </motion.div>

          {/* Right: Product Info */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }} 
            animate={{ opacity: 1, x: 0 }} 
            className="w-full md:w-1/2 space-y-6"
          >
            <div>
              <span className="text-purple-400 font-bold tracking-wider text-sm uppercase mb-2 block">
                {product.brand || "Brand Unknown"}
              </span>
              <h1 className="text-4xl md:text-5xl font-bold leading-tight">
                {product.product_name}
              </h1>
            </div>

            <div className="text-3xl font-bold text-white flex items-end gap-2">
              {product.price?.toLocaleString()} 
              <span className="text-lg font-normal text-gray-500 mb-1">KRW</span>
            </div>

            <p className="text-gray-400 leading-relaxed text-lg">
              {product.description || "이 상품에 대한 상세 설명이 없습니다. AI가 스타일과 맥락을 분석하여 추천한 상품입니다."}
            </p>
            
            {/* Detail Grid */}
            <div className="grid grid-cols-2 gap-4 py-6 border-t border-b border-white/10">
                <div>
                  <p className="text-gray-500 text-sm mb-1">Season</p>
                  <p className="font-medium text-lg">{product.season || "All Season"}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-sm mb-1">Color</p>
                  <p className="font-medium text-lg">{product.color || "Mixed"}</p>
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <button className="flex-1 bg-white text-black py-4 rounded-xl font-bold hover:bg-gray-200 transition flex justify-center items-center gap-2 shadow-lg hover:shadow-white/10">
                <ShoppingBag size={20} /> 
                Buy Now
              </button>
              
              {/* 찜 버튼 (상태에 따라 색상 변경) */}
              <button 
                onClick={toggleLike}
                className={`p-4 rounded-xl transition border-2 flex items-center justify-center
                  ${isLiked 
                    ? 'bg-pink-500/10 border-pink-500 text-pink-500' 
                    : 'bg-white/5 border-transparent hover:bg-white/10 text-gray-400 hover:text-white'
                  }`}
              >
                <Heart size={28} fill={isLiked ? "currentColor" : "none"} />
              </button>
            </div>
          </motion.div>
        </div>

        {/* Related Products Section */}
        {related.length > 0 && (
          <div className="mt-24">
            <h2 className="text-2xl font-bold mb-8 border-l-4 border-purple-500 pl-4">
              Similar Styles
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {related.map((item) => (
                <div 
                  key={item.id} 
                  onClick={() => navigate(`/product/${item.id}`)} 
                  className="cursor-pointer group"
                >
                  <div className="rounded-xl overflow-hidden border border-white/5 bg-[#1a1a20] aspect-[3/4] relative">
                    <img 
                      src={`http://localhost:8000/static/images/${item.image_file}`} 
                      alt={item.product_name}
                      className="w-full h-full object-cover transition duration-500 group-hover:scale-110"
                    />
                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors" />
                  </div>
                  <div className="mt-3 px-1">
                    <p className="text-sm font-medium truncate text-gray-300 group-hover:text-white transition-colors">
                      {item.product_name}
                    </p>
                    <p className="text-xs text-purple-400 mt-1">
                      {item.price?.toLocaleString()}원
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductDetailPage;