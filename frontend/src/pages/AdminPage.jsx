import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, Loader2, Image as ImageIcon } from 'lucide-react';

const AdminPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState(null);
  
  // 폼 데이터 상태 관리
  const [formData, setFormData] = useState({
    product_name: '',
    brand: '',
    price: '',
    season: '',
    color: '',
    description: '',
    file: null
  });

  // 텍스트 입력 핸들러
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // 파일 선택 핸들러 (미리보기 생성)
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({ ...prev, file: file }));
      setPreview(URL.createObjectURL(file)); // 미리보기 URL 생성
    }
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 유효성 검사
    if (!formData.file || !formData.product_name) {
      alert("Image and Product Name are required.");
      return;
    }

    setIsLoading(true);

    try {
      // 1. FormData 객체 생성
      const data = new FormData();
      data.append('file', formData.file);
      data.append('product_name', formData.product_name);
      data.append('brand', formData.brand);
      data.append('price', formData.price);
      data.append('season', formData.season);
      data.append('color', formData.color);
      data.append('description', formData.description);

      // 2. 백엔드 API 호출
      const response = await fetch('http://localhost:8000/products', {
        method: 'POST',
        body: data,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      // 3. 성공 시 결과 처리
      const result = await response.json();
      alert(`Product Registered! ID: ${result.id}`);
      navigate(`/product/${result.id}`); // 등록된 상세 페이지로 이동

    } catch (error) {
      console.error("Upload Error:", error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button onClick={() => navigate('/home')} className="p-2 mr-4 rounded-full bg-white/10 hover:bg-white/20 transition">
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            Admin Product Upload
          </h1>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left: Image Upload Area */}
          <div className="space-y-4">
            <div className={`aspect-[3/4] rounded-2xl border-2 border-dashed border-gray-700 flex flex-col items-center justify-center bg-[#1a1a20] relative overflow-hidden group hover:border-purple-500 transition-colors`}>
              
              {preview ? (
                <>
                  <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <p className="text-white font-medium">Click to change</p>
                  </div>
                </>
              ) : (
                <div className="text-center p-6">
                  <ImageIcon size={48} className="mx-auto mb-4 text-gray-500" />
                  <p className="text-gray-400">Click to upload image</p>
                  <p className="text-xs text-gray-600 mt-2">JPG, PNG supported</p>
                </div>
              )}
              
              {/* 숨겨진 파일 입력창 */}
              <input 
                type="file" 
                accept="image/*" 
                onChange={handleFileChange} 
                className="absolute inset-0 opacity-0 cursor-pointer" 
              />
            </div>
          </div>

          {/* Right: Metadata Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Product Name *</label>
              <input
                name="product_name"
                value={formData.product_name}
                onChange={handleChange}
                required
                className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition"
                placeholder="Product Name"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Brand</label>
                <input
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition"
                  placeholder="Brand"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Price (KRW)</label>
                <input
                  name="price"
                  type="number"
                  value={formData.price}
                  onChange={handleChange}
                  className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition"
                  placeholder="Price"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Season</label>
                <select 
                  name="season" 
                  value={formData.season}
                  onChange={handleChange}
                  className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition appearance-none"
                >
                  <option value="">Select</option>
                  <option value="봄">Spring</option>
                  <option value="여름">Summer</option>
                  <option value="가을">Autumn</option>
                  <option value="겨울">Winter</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Color</label>
                <input
                  name="color"
                  value={formData.color}
                  onChange={handleChange}
                  className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition"
                  placeholder="Color"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                className="w-full bg-[#15151a] border border-gray-700 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 transition resize-none"
                placeholder="Description..."
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-gray-200 transition flex justify-center items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" />
                  Embedding & Saving...
                </>
              ) : (
                <>
                  <Upload size={20} />
                  Upload Product
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;