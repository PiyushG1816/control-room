import { BrowserRouter, Routes, Route } from 'react-router-dom';
import RunsList from './pages/RunsList.jsx';
import RunDetail from './pages/RunDetail.jsx';
import Compare from './pages/Compare.jsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/compare" element={<Compare />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
