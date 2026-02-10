import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import StrategyListPage from './pages/StrategyListPage';
import StrategyCreatePage from './pages/StrategyCreatePage';
import ScreeningResultPage from './pages/ScreeningResultPage';
import IndustryResearchPage from './pages/IndustryResearchPage';
import CredibilityVerificationPage from './pages/CredibilityVerificationPage';
import TaskHistoryPage from './pages/TaskHistoryPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/strategies" replace />} />
        <Route path="strategies" element={<StrategyListPage />} />
        <Route path="strategies/create" element={<StrategyCreatePage />} />
        <Route path="results" element={<ScreeningResultPage />} />
        <Route path="results/:sessionId" element={<ScreeningResultPage />} />
        <Route path="intelligence/industry-research" element={<IndustryResearchPage />} />
        <Route path="intelligence/credibility-verification" element={<CredibilityVerificationPage />} />
        <Route path="intelligence/task-history" element={<TaskHistoryPage />} />
      </Route>
    </Routes>
  );
}

export default App;
