import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RunsList from './pages/RunsList.jsx';
import RunDetail from './pages/RunDetail.jsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/runs/:id" element={<RunDetail />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
