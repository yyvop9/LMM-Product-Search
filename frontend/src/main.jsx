import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// [중요] 여기에 BrowserRouter가 있으면 안 됩니다! 
// App.jsx 안에서 이미 선언했기 때문입니다.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)