import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion'; // 애니메이션 라이브러리
import { Mail, Lock, Loader2 } from 'lucide-react'; // 아이콘

const LoginPage = () => {
  const navigate = useNavigate();
  
  // 상태 관리
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  // 입력값 변경 핸들러
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // 로그인 버튼 클릭 핸들러
  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // [TODO] 실제 백엔드 연동 시 fetch 요청으로 교체
      // const res = await fetch('http://localhost:8000/auth/token', ...);
      
      // 현재는 시뮬레이션 (1초 대기 후 성공 처리)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log("Login Success:", formData);
      navigate('/home'); // 메인 페이지로 이동
    } catch (err) {
      setError("로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-[#050505] text-white overflow-hidden justify-center items-center relative">
      
      {/* [Background Effect] 배경 장식용 그라디언트 */}
      <div className="absolute top-[-20%] left-[-20%] w-[600px] h-[600px] bg-purple-600/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-pink-600/10 rounded-full blur-[100px]" />

      {/* [Main Card] 로그인 폼 컨테이너 */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md bg-white/5 p-10 rounded-3xl border border-white/10 backdrop-blur-xl shadow-2xl z-10"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tighter mb-2 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-500 to-red-500">
            Modify
          </h1>
          <p className="text-gray-400 text-sm">AI Fashion Engine Login</p>
        </div>

        {/* Form */}
        <form className="space-y-6" onSubmit={handleLogin}>
          
          {/* Email Input */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-500 group-focus-within:text-purple-500 transition-colors" />
            </div>
            <input 
              name="email" 
              type="email" 
              required 
              value={formData.email} 
              onChange={handleChange} 
              className="block w-full pl-12 pr-3 py-4 border border-gray-700 rounded-xl bg-[#15151a] text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
              placeholder="example@modify.ai" 
            />
          </div>

          {/* Password Input */}
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <Lock className="h-5 w-5 text-gray-500 group-focus-within:text-purple-500 transition-colors" />
            </div>
            <input 
              name="password" 
              type="password" 
              required 
              value={formData.password} 
              onChange={handleChange} 
              className="block w-full pl-12 pr-3 py-4 border border-gray-700 rounded-xl bg-[#15151a] text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all" 
              placeholder="••••••••" 
            />
          </div>

          {/* Error Message */}
          {error && <p className="text-red-400 text-sm text-center animate-pulse">{error}</p>}

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={isLoading} 
            className="w-full py-4 rounded-xl font-bold text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition-opacity shadow-lg shadow-purple-500/20 disabled:opacity-70 flex justify-center items-center"
          >
            {isLoading ? <Loader2 className="animate-spin h-5 w-5" /> : "Sign In"}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          Don't have an account? <span className="text-purple-400 cursor-pointer hover:underline">Sign up</span>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;