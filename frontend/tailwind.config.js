/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 1. 폰트 설정 (없으면 시스템 폰트 사용됨)
      fontFamily: {
        sans: ['Pretendard', 'Inter', 'sans-serif'],
      },
      // 2. 애니메이션 정의
      animation: {
        'gradient': 'gradient 8s linear infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      // 3. 키프레임 (움직임 동작)
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center'
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center'
          },
        },
      },
      // 4. 커스텀 컬러 (필요 시)
      colors: {
        dark: {
          DEFAULT: '#050505', // 메인 배경색
          100: '#121212',     // 카드 배경색
          200: '#1a1a1a',     // 옅은 배경색
        }
      }
    },
  },
  plugins: [],
}