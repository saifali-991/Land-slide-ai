// NOTE: React.StrictMode is intentionally NOT used here.
// react-leaflet v4 + React 18 StrictMode double-mounts the Leaflet map,
// which breaks map click handlers (useMapEvents) on the Analyze page.
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <App />
  </BrowserRouter>,
)
