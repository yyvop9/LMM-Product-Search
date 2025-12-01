import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Heart, ShoppingBag, Share2, Sparkles, Loader2, Info } from 'lucide-react';

const ProductDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [product, setProduct] = useState(null);
  const [relatedProducts, setRelatedProducts] = useState([]);
  const [coordination, setCoordination] = useState([]);
  const [isCoordLoading, setIsCoordLoading] = useState(true);
  const [isLiked, setIsLiked] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        window.scrollTo(0, 0);
        // 1. 상품 상세
        const prodRes = await fetch(`http://localhost:8000/product/${id}`);
        if (!prodRes.ok) throw new Error("Product not found");
        setProduct(await prodRes.json());

        // 2. 찜 여부
        const wishRes = await fetch(`http://localhost:8000/wishlist/check/${id}`);
        if (wishRes.ok) setIsLiked((await wishRes.json()).is_in_wishlist);

        // 3. 연관 상품
        const relRes = await fetch(`http://localhost:8000/search/related/${id}?top_k=4`);
        if (relRes.ok) setRelatedProducts(await relRes.json());

        // 4. AI 코디
        fetchCoordination(id);

      } catch (error) {
        console.error(error);
        navigate('/');
      }
    };
    fetchData();
  }, [id, navigate]);

  const fetchCoordination = async (pid) => {
    setIsCoordLoading(true);
    try {
        const res = await fetch(`http://localhost:8000/coordinate/${pid}`);
        if (res.ok) setCoordination(await res.json());
    } catch(e) { console.error(e); } 
    finally { setIsCoordLoading(false); }
  };

  const toggleLike = async () => {
    const prev = isLiked;
    setIsLiked(!prev);
    try {
        await fetch('http://localhost:8000/wishlist/toggle', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ product_id: id })
        });
    } catch(e) { setIsLiked(prev); }
  };

  if (!product) return <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white"><Loader2 className="animate-spin"/></div>;

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-20 selection:bg-violet-500 selection:text-white">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 px-6 py-4 flex justify-between items-center">
        <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
          <ArrowLeft size={24} />
        </button>
        <div className="flex gap-2">
            <button className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white"><Share2 size={20}/></button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 mt-8 grid grid-cols-1 lg:grid-cols-2 gap-12">
        
        {/* Left: Image (Sticky) */}
        <div className="lg:sticky lg:top-24 h-fit">
            <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="rounded-3xl overflow-hidden border border-white/10 bg-[#121212] relative group shadow-2xl"
            >
                <img 
                    src={`http://localhost:8000/static/images/${product.image_file}`} 
                    alt={product.product_name}
                    className="w-full h-auto object-cover"
                    onError={(e) => {e.target.src = "https://via.placeholder.com/600x800?text=No+Image"}}
                />
                <div className="absolute top-4 right-4 z-10">
                    <button 
                        onClick={toggleLike}
                        className="p-3 rounded-full bg-black/30 backdrop-blur-md hover:bg-black/50 transition-all shadow-lg active:scale-95"
                    >
                        <Heart 
                            size={24} 
                            fill={isLiked ? "#ec4899" : "none"} 
                            className={isLiked ? "text-pink-500" : "text-white"} 
                        />
                    </button>
                </div>
            </motion.div>
        </div>

        {/* Right: Info */}
        <div className="space-y-8">
            {/* Header Info */}
            <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                    {product.brand && <span className="px-3 py-1 rounded-full bg-white/10 text-xs font-bold text-gray-200">{product.brand}</span>}
                    {product.season && <span className="px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-xs font-bold text-green-400">{product.season}</span>}
                </div>
                <h1 className="text-4xl font-bold leading-tight">{product.product_name}</h1>
                <p className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-400">
                    {product.price?.toLocaleString()}원
                </p>
                <p className="text-gray-400 leading-relaxed border-t border-white/10 pt-6">
                    {product.description || "이 상품은 상세 설명이 없습니다."}
                </p>
            </div>

            {/* AI Stylist Section (Highlighted) */}
            <div className="relative group rounded-2xl p-[1px] bg-gradient-to-r from-violet-600 via-pink-600 to-orange-500">
                <div className="bg-[#121212] rounded-2xl p-6 h-full">
                    <div className="flex items-center gap-2 mb-4">
                        <Sparkles className="text-violet-500 animate-pulse" />
                        <h3 className="text-lg font-bold text-white">AI Stylist's Pick</h3>
                    </div>

                    {isCoordLoading ? (
                        <div className="flex items-center justify-center h-32 text-gray-500 text-sm gap-2">
                            <Loader2 className="animate-spin"/> Analyzing...
                        </div>
                    ) : coordination.length > 0 ? (
                        <div className="space-y-3">
                            {coordination.map((item, idx) => (
                                <div 
                                    key={idx}
                                    onClick={() => navigate(`/product/${item.recommended_item.id}`)}
                                    className="flex items-center gap-4 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition cursor-pointer border border-white/5"
                                >
                                    <img 
                                        src={`http://localhost:8000/static/images/${item.recommended_item.image_file}`}
                                        className="w-16 h-16 rounded-lg object-cover bg-gray-800"
                                    />
                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-start">
                                            <p className="font-medium text-sm text-gray-200 truncate">{item.recommended_item.product_name}</p>
                                            <span className="text-[10px] font-bold bg-pink-500/20 text-pink-400 px-2 py-0.5 rounded-full ml-2">
                                                {item.match_score}점
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-500 mt-0.5">{item.recommended_item.price?.toLocaleString()}원</p>
                                        <p className="text-xs text-violet-300 mt-1 italic">"{item.ai_comment}"</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center text-sm text-gray-500 py-4">추천 코디가 없습니다.</div>
                    )}
                </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-4 pt-4">
                <button className="flex-1 bg-white text-black font-bold h-14 rounded-full hover:bg-gray-200 transition-transform active:scale-95 flex items-center justify-center gap-2">
                    <ShoppingBag size={20} /> 구매하기
                </button>
            </div>
            
            {/* Related Items */}
            <div className="pt-8 border-t border-white/10">
                <h3 className="text-lg font-bold mb-4">비슷한 스타일</h3>
                <div className="grid grid-cols-4 gap-4">
                    {relatedProducts.map(p => (
                        <div key={p.id} onClick={() => navigate(`/product/${p.id}`)} className="cursor-pointer group">
                             <div className="aspect-[3/4] rounded-xl overflow-hidden bg-gray-800 mb-2">
                                <img src={`http://localhost:8000/static/images/${p.image_file}`} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition"/>
                             </div>
                             <p className="text-xs text-gray-400 truncate group-hover:text-white">{p.product_name}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;