import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
// (!!!) 아이콘 임포트: 검색, 업로드, AI모드, 로딩, 이미지, 등록, 찜
import { Search, Upload, Sparkles, Loader2, Image as ImageIcon, PlusSquare, Heart } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchMode, setSearchMode] = useState('text'); // 'text' or 'smart'

  // [API] 텍스트 및 AI 스마트 검색 핸들러
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setResults([]);

    try {
      // 모드에 따른 엔드포인트 결정
      const endpoint = searchMode === 'smart' ? '/search/smart' : '/search/text';
      
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query, top_k: 20 }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Search Error:", error);
      alert("검색 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  // [API] 이미지 검색 핸들러 (파일 선택 시 자동 업로드)
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsLoading(true);
    setResults([]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('top_k', 20);

    try {
      const response = await fetch('http://localhost:8000/search/image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Image Search Error:", error);
      alert("이미지 검색 실패");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-20">
      {/* --- Header Section --- */}
      <div className="sticky top-0 z-50 bg-[#050505]/80 backdrop-blur-md border-b border-white/5 pb-6 pt-6 px-4">
        <div className="max-w-6xl mx-auto relative">
          
          {/* [Navigation Buttons] 우측 상단 배치 */}
          <div className="absolute right-0 top-0 hidden md:flex space-x-3">
            {/* 1. 찜 목록 이동 버튼 */}
            <button 
              onClick={() => navigate('/wishlist')}
              className="flex items-center space-x-2 text-pink-400 hover:text-pink-300 transition-colors text-sm font-medium border border-gray-800 hover:border-pink-500/50 rounded-lg px-3 py-2"
            >
              <Heart size={16} fill="currentColor" />
              <span>Wishlist</span>
            </button>

            {/* 2. 상품 등록(Admin) 이동 버튼 */}
            <button 
              onClick={() => navigate('/admin')}
              className="flex items-center space-x-2 text-gray-500 hover:text-purple-400 transition-colors text-sm font-medium border border-gray-800 hover:border-purple-500/50 rounded-lg px-3 py-2"
            >
              <PlusSquare size={16} />
              <span>Add Product</span>
            </button>
          </div>

          <div className="max-w-2xl mx-auto space-y-6">
            {/* Logo & Title */}
            <div className="flex justify-center items-center space-x-2">
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600 tracking-tighter">
                Modify
              </h1>
              <span className="text-gray-500 text-sm font-light">AI Fashion Engine</span>
            </div>

            {/* Search Bar Container */}
            <form onSubmit={handleSearch} className="relative group">
              {/* Background Glow Effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>
              
              <div className="relative flex items-center bg-[#15151a] border border-gray-700 rounded-2xl p-2 shadow-2xl">
                {/* Search Icon */}
                <div className="pl-3 pr-2">
                  <Search className="text-gray-400" size={20} />
                </div>

                {/* Text Input */}
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="원하는 스타일을 입력하세요 (예: 여름 린넨 셔츠)"
                  className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-500 h-10 px-2"
                />

                {/* Mode Toggle Button */}
                <button
                  type="button"
                  onClick={() => setSearchMode(searchMode === 'smart' ? 'text' : 'smart')}
                  className={`flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all mx-2
                    ${searchMode === 'smart' 
                      ? 'bg-purple-500/20 text-purple-300 border border-purple-500/50' 
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  <Sparkles size={14} />
                  <span>{searchMode === 'smart' ? 'AI Mode' : 'Basic'}</span>
                </button>

                {/* Image Upload Button */}
                <label className="cursor-pointer p-2 rounded-xl hover:bg-gray-800 text-gray-400 hover:text-white transition-colors">
                  <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} />
                  <Upload size={20} />
                </label>

                {/* Submit Button */}
                <button
                  type="submit"
                  className="ml-2 px-6 py-2.5 bg-white text-black rounded-xl font-bold hover:bg-gray-200 transition-colors"
                >
                  Search
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* --- Results Grid Section --- */}
      <div className="max-w-7xl mx-auto px-4 mt-8">
        {isLoading ? (
          // Loading State
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <Loader2 className="animate-spin text-purple-500" size={40} />
            <p className="text-gray-400 animate-pulse">AI가 스타일을 분석 중입니다...</p>
          </div>
        ) : (
          <>
            {results.length > 0 ? (
              // Results Grid (Masonry Layout)
              <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
                {results.map((product) => (
                  <motion.div
                    key={product.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ y: -5 }}
                    onClick={() => navigate(`/product/${product.id}`)} // 클릭 시 상세 페이지로 이동
                    className="break-inside-avoid relative group rounded-xl overflow-hidden bg-[#1a1a20] border border-white/5 cursor-pointer"
                  >
                    <img
                      src={`http://localhost:8000/static/images/${product.image_file}`}
                      alt={product.product_name}
                      className="w-full h-auto object-cover transition-transform duration-500 group-hover:scale-105"
                      onError={(e) => {e.target.src = "https://via.placeholder.com/300x400?text=No+Image"}}
                    />
                    
                    {/* Hover Overlay Info */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                      <h3 className="text-white font-semibold text-sm line-clamp-1">{product.product_name || "상품명 없음"}</h3>
                      <div className="flex justify-between items-center mt-1">
                        <span className="text-purple-400 text-xs font-bold">
                          {product.price ? `${product.price.toLocaleString()}원` : "가격 미정"}
                        </span>
                        <span className="text-gray-400 text-[10px] bg-white/10 px-2 py-0.5 rounded-full">
                          {product.brand || "Brand"}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              // Empty State (결과 없음)
              <div className="text-center text-gray-500 mt-20">
                <ImageIcon size={48} className="mx-auto mb-4 opacity-20" />
                <p>검색 결과가 없습니다. <br />스타일 키워드나 이미지로 검색하거나, <br />우측 상단의 <b>Add Product</b> 버튼으로 상품을 등록해보세요.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default HomePage;