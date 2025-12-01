import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Plus, ArrowLeft, Check, AlertCircle } from 'lucide-react';

const AdminPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  
  // 폼 상태 관리 (필수 데이터 포함)
  const [formData, setFormData] = useState({
    product_name: '',
    price: '',
    brand: '',
    description: '',
    season: 'All',      // 기본값 설정
    gender: 'Unisex',   // 기본값 설정
    category: 'Top',    // 기본값 설정
    file: null
  });
  
  const [preview, setPreview] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({ ...prev, file: file }));
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.file) return alert("이미지를 선택해주세요.");

    setIsLoading(true);
    const data = new FormData();
    // 백엔드 스키마와 키값이 정확히 일치해야 함
    data.append('file', formData.file);
    data.append('product_name', formData.product_name);
    data.append('price', formData.price);
    data.append('brand', formData.brand);
    data.append('description', formData.description);
    data.append('season', formData.season);
    data.append('gender', formData.gender);
    data.append('category', formData.category);

    try {
      const response = await fetch('http://localhost:8000/products', {
        method: 'POST',
        body: data,
      });

      if (!response.ok) throw new Error('등록 실패');
      
      alert("상품이 성공적으로 등록되었습니다!");
      navigate('/'); // 홈으로 이동
    } catch (error) {
      console.error(error);
      alert("오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white p-6">
      <div className="max-w-2xl mx-auto bg-[#1a1a20] rounded-2xl border border-gray-800 p-8">
        
        {/* Header */}
        <div className="flex items-center space-x-4 mb-8">
          <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/10 rounded-full transition">
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            Add New Product
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* 1. 이미지 업로드 */}
          <div className="flex justify-center">
            <label className="relative cursor-pointer group">
              <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} />
              <div className={`w-64 h-80 rounded-xl border-2 border-dashed flex items-center justify-center overflow-hidden transition-all
                ${preview ? 'border-purple-500' : 'border-gray-700 hover:border-gray-500 bg-gray-900'}`}>
                {preview ? (
                  <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                ) : (
                  <div className="flex flex-col items-center text-gray-500">
                    <Upload size={40} className="mb-2" />
                    <span className="text-sm">Click to upload image</span>
                  </div>
                )}
              </div>
            </label>
          </div>

          {/* 2. 필수 정보 입력 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="text-xs text-gray-400 ml-1">상품명</label>
              <input 
                name="product_name" required placeholder="예: 오버핏 니트"
                value={formData.product_name} onChange={handleChange}
                className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:border-purple-500 outline-none transition"
              />
            </div>

            <div>
              <label className="text-xs text-gray-400 ml-1">가격 (원)</label>
              <input 
                name="price" type="number" required placeholder="39000"
                value={formData.price} onChange={handleChange}
                className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:border-purple-500 outline-none transition"
              />
            </div>

            <div>
              <label className="text-xs text-gray-400 ml-1">브랜드</label>
              <input 
                name="brand" placeholder="Nike, Zara..."
                value={formData.brand} onChange={handleChange}
                className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:border-purple-500 outline-none transition"
              />
            </div>
          </div>

          {/* 3. 메타데이터 (성별/계절/카테고리) - 여기가 제일 중요! */}
          <div className="grid grid-cols-3 gap-4 bg-gray-900/50 p-4 rounded-xl border border-gray-800">
            <div>
              <label className="text-xs text-purple-400 font-bold ml-1 mb-1 block">Gender</label>
              <select 
                name="gender" value={formData.gender} onChange={handleChange}
                className="w-full bg-black border border-gray-700 rounded-lg p-2 text-sm text-white focus:border-purple-500 outline-none"
              >
                <option value="Unisex">Unisex</option>
                <option value="Men">Men</option>
                <option value="Women">Women</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-green-400 font-bold ml-1 mb-1 block">Season</label>
              <select 
                name="season" value={formData.season} onChange={handleChange}
                className="w-full bg-black border border-gray-700 rounded-lg p-2 text-sm text-white focus:border-green-500 outline-none"
              >
                <option value="All">All Season</option>
                <option value="봄">봄 (Spring)</option>
                <option value="여름">여름 (Summer)</option>
                <option value="가을">가을 (Autumn)</option>
                <option value="겨울">겨울 (Winter)</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-blue-400 font-bold ml-1 mb-1 block">Category</label>
              <select 
                name="category" value={formData.category} onChange={handleChange}
                className="w-full bg-black border border-gray-700 rounded-lg p-2 text-sm text-white focus:border-blue-500 outline-none"
              >
                <option value="Top">Top</option>
                <option value="Bottom">Bottom</option>
                <option value="Outer">Outer</option>
                <option value="Shoes">Shoes</option>
                <option value="Acc">Acc</option>
              </select>
            </div>
          </div>

          <div className="col-span-2">
              <label className="text-xs text-gray-400 ml-1">설명</label>
              <textarea 
                name="description" rows="3" placeholder="상품에 대한 상세 설명..."
                value={formData.description} onChange={handleChange}
                className="w-full bg-black/50 border border-gray-700 rounded-lg p-3 text-white focus:border-purple-500 outline-none transition resize-none"
              />
          </div>

          {/* Submit Button */}
          <button 
            type="submit" disabled={isLoading}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold py-4 rounded-xl hover:opacity-90 transition transform active:scale-95 disabled:opacity-50"
          >
            {isLoading ? "등록 중..." : "상품 등록하기"}
          </button>

        </form>
      </div>
    </div>
  );
};

export default AdminPage;