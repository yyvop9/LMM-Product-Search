import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Lock, Mail, ArrowRight, Loader2, Sparkles } from 'lucide-react';

const LoginPage = () => {
  const navigate = useNavigate();
  
  // --- 상태 관리 ---
  const [isLoginMode, setIsLoginMode] = useState(true); // true: 로그인, false: 회원가입
  const [isLoading, setIsLoading] = useState(false);
  
  // 폼 데이터
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: ''
  });

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.email || !formData.password) {
      return alert("이메일과 비밀번호를 입력해주세요.");
    }
    if (!isLoginMode && !formData.full_name) {
      return alert("이름을 입력해주세요.");
    }

    setIsLoading(true);
    const endpoint = isLoginMode ? "/auth/login" : "/auth/signup";

    try {
      // [핵심 수정] 백엔드가 JSON을 원하므로 JSON으로 전송합니다.
      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json" 
        },
        // [핵심 수정] username 필드에 email 값을 매핑하여 JSON 문자열로 전송
        body: JSON.stringify({
            // 백엔드가 username 필드를 찾을 가능성이 높으므로 매핑
            // (만약 백엔드가 email 필드를 원한다면 formData 그대로 보내도 됨)
            username: formData.email, 
            email: formData.email,      // 혹시 몰라 둘 다 보냄
            password: formData.password,
            full_name: formData.full_name
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorMessage = "요청 처리 중 오류가 발생했습니다.";
        if (data.detail) {
          if (typeof data.detail === 'string') {
             errorMessage = data.detail;
          } else if (typeof data.detail === 'object') {
             errorMessage = JSON.stringify(data.detail, null, 2);
          }
        }
        throw new Error(errorMessage);
      }

      if (isLoginMode) {
        // [로그인 성공]
        localStorage.setItem("token", data.access_token);
        localStorage.setItem("user_email", formData.email); 
        
        alert(`반가워요, ${formData.email.split('@')[0]}님!`);
        // [성공 후 이동]
        window.location.href = "/"; 
      } else {
        // [회원가입 성공]
        alert("회원가입이 완료되었습니다! 이제 로그인을 해주세요.");
        setIsLoginMode(true); 
        setFormData({ ...formData, password: "" }); 
      }

    } catch (error) {
      console.error("Login Error:", error);
      alert(`⚠️ 로그인 실패:\n${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4 selection:bg-violet-500 selection:text-white">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-violet-600/10 rounded-full blur-[100px] pointer-events-none"></div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-[#121212] border border-white/10 rounded-3xl p-8 shadow-2xl relative z-10"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-pink-500 mb-5 shadow-lg shadow-violet-900/20">
            <Sparkles className="text-white" size={24} />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">
            {isLoginMode ? "Welcome Back" : "Create Account"}
          </h1>
          <p className="text-gray-400 text-sm">
            {isLoginMode ? "AI 패션 검색 엔진, Modify입니다." : "회원가입하고 나만의 AI 스타일리스트를 만나보세요."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <AnimatePresence>
            {!isLoginMode && (
              <motion.div 
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="space-y-1 overflow-hidden"
              >
                <label className="text-xs font-bold text-gray-500 ml-1 uppercase tracking-wider">Full Name</label>
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-violet-400 transition-colors" size={20} />
                  <input 
                    type="text" 
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    placeholder="예: 홍길동"
                    className="w-full bg-[#1a1a1a] border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-white placeholder-gray-600 focus:outline-none focus:border-violet-500/50 focus:bg-[#202025] transition-all"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="space-y-1">
            <label className="text-xs font-bold text-gray-500 ml-1 uppercase tracking-wider">Email Address</label>
            <div className="relative group">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-violet-400 transition-colors" size={20} />
              <input 
                type="email" 
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="name@example.com"
                className="w-full bg-[#1a1a1a] border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-white placeholder-gray-600 focus:outline-none focus:border-violet-500/50 focus:bg-[#202025] transition-all"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-bold text-gray-500 ml-1 uppercase tracking-wider">Password</label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-violet-400 transition-colors" size={20} />
              <input 
                type="password" 
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="w-full bg-[#1a1a1a] border border-white/10 rounded-xl py-3.5 pl-12 pr-4 text-white placeholder-gray-600 focus:outline-none focus:border-violet-500/50 focus:bg-[#202025] transition-all"
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-gray-200 transition-all transform active:scale-95 flex items-center justify-center gap-2 mt-8 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
          >
            {isLoading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                {isLoginMode ? "Sign In" : "Sign Up"}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="mt-8 text-center pt-6 border-t border-white/5">
          <p className="text-sm text-gray-500">
            {isLoginMode ? "계정이 없으신가요?" : "이미 계정이 있으신가요?"}
            <button 
              onClick={() => {
                setIsLoginMode(!isLoginMode);
                setFormData({ full_name: '', email: '', password: '' });
              }}
              className="ml-2 text-violet-400 hover:text-violet-300 font-bold transition-colors"
            >
              {isLoginMode ? "회원가입 하기" : "로그인 하기"}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default LoginPage;