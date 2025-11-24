/** @type {import('tailwindcss').Config} */
export default {
  // (!!!) 핵심: 스타일을 적용할 파일들의 경로 지정
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 여기서 커스텀 컬러나 폰트를 추가할 수 있음
    },
  },
  plugins: [],
}