import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import StrategyListPage from './pages/StrategyListPage';
import StrategyCreatePage from './pages/StrategyCreatePage';
import ScreeningResultPage from './pages/ScreeningResultPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/strategies" replace />} />
        <Route path="strategies" element={<StrategyListPage />} />
        <Route path="strategies/create" element={<StrategyCreatePage />} />
        <Route path="results" element={<ScreeningResultPage />} />
        <Route path="results/:sessionId" element={<ScreeningResultPage />} />
      </Route>
    </Routes>
  );
}

export default App;
