import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom' // (!!!) 1. import
import App from './App.jsx'
import './index.css' // (index.css가 있다면)
// import './App.css' // (App.css는 App.jsx에서 임포트하므로 여기서 지워도 됨)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter> {/* (!!!) 2. <App />을 감싸줌 */}
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)