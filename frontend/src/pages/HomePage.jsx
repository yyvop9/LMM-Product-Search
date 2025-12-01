import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, Upload, Sparkles, Loader2, X, Globe, 
  ChevronDown, Heart, PlusSquare 
} from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();
  const searchInputRef = useRef(null);

  // --- 상태 관리 ---
  const [userInfo, setUserInfo] = useState(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [debugInfo, setDebugInfo] = useState(null); // AI 분석 정보 저장
  const [searchMode, setSearchMode] = useState('smart'); // 'smart' or 'text'
  const [isModeOpen, setIsModeOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // 환경 변수 처리 (Docker 환경 대응)
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // 1. 초기 데이터 로드 (로그인 정보)
  useEffect(() => {
    const userEmail = localStorage.getItem('user_email');
    if (userEmail) {
      setUserInfo({ name: userEmail.split('@')[0] });
    }
  }, []);

  // 2. 검색 실행 함수
  const executeSearch = async (searchQuery) => {
    if (!searchQuery.trim()) return;

    setIsLoading(true);
    setShowHistory(false);
    setIsModeOpen(false);
    setQuery(searchQuery);
    setResults([]);
    setDebugInfo(null); // 이전 분석 정보 초기화

    try {
      const endpoint = searchMode === 'smart' ? '/search/smart' : '/search/text';
      
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 20 }),
      });

      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();

      // [중요] 응답 데이터 구조에 따라 분기 처리
      if (Array.isArray(data)) {
        // 일반 텍스트 검색 결과 (리스트만 옴)
        setResults(data);
        setDebugInfo(null);
      } else {
        // 스마트 검색 결과 ({ products: [], debug_info: {} })
        setResults(data.products || []);
        setDebugInfo(data.debug_info || null);
      }

    } catch (error) {
      console.error("Search Error:", error);
      alert("검색 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    executeSearch(query);
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsLoading(true);
    setResults([]);
    setDebugInfo(null);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('top_k', 20);

    try {
      const res = await fetch(`${API_URL}/search/image`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error("Image search failed");
      
      const data = await res.json();
      setResults(Array.isArray(data) ? data : data.products || []);
    } catch (err) { 
        console.error(err);
        alert("이미지 검색 실패"); 
    } finally { 
        setIsLoading(false); 
    }
  };

  return (
    <div 
        className="w-full min-h-full pb-20 relative"
        onClick={() => { setShowHistory(false); setIsModeOpen(false); }}
    >
      
      {/* --- Top Utility Bar (Sticky Header) --- */}
      <div className="flex justify-end items-center gap-4 mb-10 sticky top-0 z-30 p-4 bg-gradient-to-b from-black via-black/90 to-transparent backdrop-blur-sm">
        {userInfo && (
            <span className="text-sm font-bold text-gray-400">
                Hi, <span className="text-white">{userInfo.name}</span>
            </span>
        )}
        <button 
            onClick={() => navigate('/wishlist')} 
            className="p-2 bg-gray-900 rounded-full hover:bg-gray-800 border border-white/10 transition text-gray-400 hover:text-pink-500"
            title="찜한 목록"
        >
            <Heart size={20} />
        </button>
        <button 
            onClick={() => navigate('/admin')} 
            className="p-2 bg-gray-900 rounded-full hover:bg-gray-800 border border-white/10 transition text-gray-400 hover:text-violet-500"
            title="관리자 (상품 등록)"
        >
            <PlusSquare size={20} />
        </button>
      </div>

      {/* --- Main Content --- */}
      <div className="flex flex-col items-center px-4">
        
        {/* Title (결과가 없을 때만 표시) */}
        {results.length === 0 && !isLoading && (
             <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-12 mt-10"
             >
               <h1 className="text-4xl md:text-6xl font-extrabold mb-4">
                 Find Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-pink-500">Vibe</span>
               </h1>
               <p className="text-gray-400 text-lg">AI가 당신이 원하는 스타일을 찾아드립니다.</p>
             </motion.div>
        )}

        {/* --- Search Bar Container --- */}
        <div className={`relative w-full max-w-3xl z-20 transition-all duration-500 ${results.length > 0 ? 'mb-6' : 'mb-20'}`} onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleSearchSubmit} className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-pink-600 rounded-2xl opacity-30 group-hover:opacity-60 transition duration-500 blur"></div>
                <div className="relative flex items-center bg-[#121212] rounded-2xl border border-white/10 shadow-2xl p-2 h-16">
                    
                    {/* Mode Toggle */}
                    <div className="relative border-r border-white/10 pr-2 mr-2">
                        <button
                            type="button"
                            onClick={() => setIsModeOpen(!isModeOpen)}
                            className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white/5 transition-colors text-sm font-medium text-gray-300"
                        >
                            {searchMode === 'smart' ? (
                                <div className="flex items-center gap-2 text-violet-400">
                                    <Sparkles size={18} /> <span className="hidden md:inline">AI Search</span>
                                </div>
                            ) : (
                                <div className="flex items-center gap-2 text-gray-400">
                                    <Globe size={18} /> <span className="hidden md:inline">Keyword</span>
                                </div>
                            )}
                            <ChevronDown size={14} className={`text-gray-500 transition-transform ${isModeOpen ? 'rotate-180' : ''}`} />
                        </button>
                        
                        {/* Mode Dropdown */}
                        {isModeOpen && (
                            <div className="absolute top-full left-0 mt-2 w-40 bg-[#1a1a1a] border border-white/10 rounded-xl shadow-xl overflow-hidden z-30">
                                <button type="button" onClick={() => { setSearchMode('smart'); setIsModeOpen(false); }} className="w-full text-left px-4 py-3 hover:bg-white/5 text-sm text-gray-300 flex items-center gap-2">
                                    <Sparkles size={16} className="text-violet-400"/> AI Search
                                </button>
                                <button type="button" onClick={() => { setSearchMode('text'); setIsModeOpen(false); }} className="w-full text-left px-4 py-3 hover:bg-white/5 text-sm text-gray-300 flex items-center gap-2">
                                    <Globe size={16} className="text-gray-400"/> Keyword
                                </button>
                            </div>
                        )}
                    </div>
                    
                    {/* Input Field */}
                    <input
                        ref={searchInputRef}
                        type="text"
                        value={query}
                        onFocus={() => setShowHistory(true)}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder={searchMode === 'smart' ? "예: 여름 바닷가에서 입을 시원한 원피스 찾아줘" : "상품명, 브랜드 검색"}
                        className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-500 text-lg h-full px-2"
                    />

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                        {query && (
                            <button type="button" onClick={() => {setQuery(''); setResults([]); setDebugInfo(null);}} className="p-2 text-gray-500 hover:text-white transition">
                                <X size={18} />
                            </button>
                        )}
                        <label className="cursor-pointer p-2 hover:bg-white/10 rounded-xl transition text-gray-400 hover:text-white" title="이미지 검색">
                            <input type="file" className="hidden" accept="image/*" onChange={handleImageUpload} />
                            <Upload size={20} />
                        </label>
                        <button type="submit" className="bg-white text-black p-3 rounded-xl hover:bg-gray-200 transition-transform active:scale-95">
                            <Search size={20} />
                        </button>
                    </div>
                </div>
            </form>
        </div>

        {/* --- [Safe] AI Analysis Result (Smart Mode & 결과 있음 & DebugInfo 유효함) --- */}
        {searchMode === 'smart' && results.length > 0 && debugInfo && (
          <motion.div 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-3xl mb-8 p-4 rounded-xl bg-violet-900/20 border border-violet-500/30 backdrop-blur-sm"
          >
            <div className="flex items-start gap-3">
              <Sparkles className="text-violet-400 mt-1 flex-shrink-0" size={18} />
              <div className="text-sm">
                <p className="text-gray-300 mb-2">
                  AI가 <strong>"{debugInfo.query || query}"</strong>를 분석했습니다:
                </p>
                <div className="flex flex-wrap gap-2">
                  {/* 시각적 키워드 (null 체크 필수) */}
                  {debugInfo.visual_keyword && (
                      <span className="px-2 py-1 rounded bg-violet-500/20 text-violet-300 text-xs border border-violet-500/30">
                        🎨 특징: {debugInfo.visual_keyword}
                      </span>
                  )}
                  
                  {/* 필터 정보 (null 체크 필수) */}
                  {debugInfo.filters && Object.entries(debugInfo.filters).map(([key, value]) => (
                    value && (
                      <span key={key} className="px-2 py-1 rounded bg-blue-500/20 text-blue-300 text-xs border border-blue-500/30">
                        {key}: {value}
                      </span>
                    )
                  ))}
                  
                  {/* 검색 모드 표시 */}
                  {debugInfo.mode && (
                      <span className="px-2 py-1 rounded bg-gray-700 text-gray-300 text-xs border border-gray-600">
                        Mode: {debugInfo.mode}
                      </span>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* --- Results Grid (Masonry Layout) --- */}
        <div className="w-full max-w-7xl pb-20">
            {isLoading && (
               <div className="py-20 flex flex-col items-center justify-center text-gray-500">
                   <Loader2 size={40} className="animate-spin text-violet-500 mb-4" />
                   <p className="animate-pulse text-sm">AI가 스타일을 분석 중입니다...</p>
               </div>
            )}
            
            {!isLoading && results.length === 0 && query && (
                <div className="text-center text-gray-500 py-10">
                    <p>검색 결과가 없습니다.</p>
                </div>
            )}
            
            {!isLoading && results.length > 0 && (
               <div className="columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4">
                   {results.map((product) => (
                       <motion.div
                           key={product.id}
                           initial={{ opacity: 0, y: 20 }}
                           animate={{ opacity: 1, y: 0 }}
                           whileHover={{ y: -5 }}
                           onClick={() => navigate(`/product/${product.id}`)}
                           className="break-inside-avoid relative group rounded-2xl overflow-hidden bg-[#121212] border border-white/5 cursor-pointer shadow-lg hover:shadow-violet-900/20 transition-all duration-300"
                       >
                           {/* 이미지 경로: 백엔드 정적 파일 서빙 */}
                           <div className="aspect-[3/4] w-full overflow-hidden bg-gray-800 relative">
                               <img
                                   src={`${API_URL}/static/images/${product.image_file}`}
                                   alt={product.product_name}
                                   loading="lazy"
                                   className="w-full h-full object-cover opacity-90 group-hover:opacity-100 group-hover:scale-105 transition-all duration-500"
                                   onError={(e) => {
                                       e.target.onerror = null; 
                                       e.target.src = "https://via.placeholder.com/300x400?text=No+Image";
                                       e.target.parentElement.classList.add("bg-gray-700"); // 로드 실패 시 배경색 변경
                                   }}
                               />
                           </div>
                           
                           {/* 상품 정보 오버레이 */}
                           <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                               <p className="text-gray-300 text-xs mb-1">{product.category || 'Item'}</p>
                               <h3 className="text-white font-bold text-sm line-clamp-1 mb-1">{product.product_name}</h3>
                               <div className="flex justify-between items-center">
                                   <span className="text-white font-bold">
                                       {product.price ? product.price.toLocaleString() : '가격미정'}원
                                   </span>
                                   <div className="p-1.5 bg-white/20 backdrop-blur-md rounded-full hover:bg-white/40 transition">
                                        <Heart size={14} className="text-white" />
                                   </div>
                               </div>
                           </div>
                       </motion.div>
                   ))}
               </div>
            )}
        </div>
      </div>
    </div>
  );
};

export default HomePage;