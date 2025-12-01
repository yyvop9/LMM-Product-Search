import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { 
  Home, 
  Search, 
  Heart, 
  User, 
  LogOut, 
  LogIn, 
  Menu 
} from "lucide-react";
import { motion } from "framer-motion";

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [userInfo, setUserInfo] = useState(null);

  // 메뉴 아이템 정의
  const MENU_ITEMS = [
    { name: "홈", path: "/", icon: <Home size={20} /> },
    { name: "찜한 목록", path: "/wishlist", icon: <Heart size={20} /> },
    { name: "관리자", path: "/admin", icon: <User size={20} /> },
  ];

  // 인증 상태 확인
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("token");
      const email = localStorage.getItem("user_email");
      if (token && email) {
        setUserInfo({ email });
      } else {
        setUserInfo(null);
      }
    };
    
    checkAuth();
    // 스토리지 변경 감지
    window.addEventListener('storage', checkAuth); 
    return () => window.removeEventListener('storage', checkAuth);
  }, [location]);

  const handleLogout = () => {
    if(window.confirm("로그아웃 하시겠습니까?")) {
        localStorage.removeItem("token");
        localStorage.removeItem("user_email");
        setUserInfo(null);
        navigate("/login");
        window.location.reload(); 
    }
  };

  return (
    <>
      {/* 모바일 햄버거 버튼 */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <button 
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 bg-gray-800 text-white rounded-md shadow-lg"
        >
          <Menu size={24} />
        </button>
      </div>

      {/* 사이드바 본체 */}
      <aside 
        className={`
          fixed top-0 left-0 h-full bg-[#121212] text-white border-r border-white/10 z-40 transition-transform duration-300 ease-in-out
          w-64 flex flex-col justify-between
          ${isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:static flex-shrink-0
        `}
      >
        {/* 1. 로고 영역 */}
        <div className="p-6 border-b border-white/10">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-pink-500 flex items-center justify-center font-bold">M</div>
            <span className="text-xl font-bold tracking-tight">Modify</span>
          </Link>
        </div>

        {/* 2. 네비게이션 메뉴 */}
        <nav className="flex-1 overflow-y-auto py-6 px-3">
          <ul className="space-y-2">
            {MENU_ITEMS.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`
                      flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200
                      ${isActive 
                        ? "bg-violet-600 text-white shadow-lg shadow-violet-900/50" 
                        : "text-gray-400 hover:bg-white/5 hover:text-white"
                      }
                    `}
                  >
                    {item.icon}
                    <span className="font-medium">{item.name}</span>
                    {isActive && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="ml-auto w-1.5 h-1.5 rounded-full bg-white"
                      />
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* 3. 하단 유저/로그아웃 */}
        <div className="p-4 border-t border-white/10 bg-[#0a0a0a]">
          {userInfo ? (
            <div className="flex flex-col gap-3">
              <div className="text-xs text-gray-500 px-2 truncate">
                {userInfo.email}
              </div>
              <button 
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
              >
                <LogOut size={18} />
                <span className="text-sm font-medium">로그아웃</span>
              </button>
            </div>
          ) : (
            <Link 
              to="/login"
              className="flex items-center justify-center gap-2 w-full py-3 bg-violet-600 hover:bg-violet-700 text-white rounded-lg transition-colors shadow-lg"
            >
              <LogIn size={18} />
              <span className="font-bold">로그인</span>
            </Link>
          )}
        </div>
      </aside>

      {/* 모바일 오버레이 */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  );
};

export default Sidebar;