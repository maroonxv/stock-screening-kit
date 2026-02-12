/**
 * IndustryResearchPage 单元测试
 *
 * Feature: real-service-integration
 * Property 1: 行业认知 API 调用正确性
 * Validates: Requirements 1.1
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import fc from 'fast-check';
import IndustryResearchPage from './IndustryResearchPage';

// Mock intelligenceApi and WebSocket functions
vi.mock('../services/intelligenceApi', () => ({
  intelligenceApi: {
    createIndustryResearch: vi.fn(),
  },
  connectWebSocket: vi.fn().mockResolvedValue(undefined),
  disconnectWebSocket: vi.fn(),
  joinTaskRoom: vi.fn(),
  leaveTaskRoom: vi.fn(),
  onTaskProgress: vi.fn(() => vi.fn()),
  onTaskCompleted: vi.fn(() => vi.fn()),
  onTaskFailed: vi.fn(() => vi.fn()),
}));

import {
  intelligenceApi,
  connectWebSocket,
  joinTaskRoom,
  onTaskCompleted,
  onTaskFailed,
} from '../services/intelligenceApi';

function renderPage() {
  return render(
    <MemoryRouter>
      <IndustryResearchPage />
    </MemoryRouter>
  );
}

describe('IndustryResearchPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('调用真实 API 并获取 task_id', async () => {
    const taskId = 'test-task-id-123';
    intelligenceApi.createIndustryResearch.mockResolvedValue({
      data: { task_id: taskId },
    });

    renderPage();

    const input = screen.getByPlaceholderText(/合成生物学/);
    fireEvent.change(input, { target: { value: '测试行业查询' } });

    const button = screen.getByRole('button', { name: /开始分析/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(intelligenceApi.createIndustryResearch).toHaveBeenCalledWith('测试行业查询');
    });

    await waitFor(() => {
      expect(connectWebSocket).toHaveBeenCalled();
      expect(joinTaskRoom).toHaveBeenCalledWith(taskId);
    });
  });

  it('API 错误时展示错误信息', async () => {
    intelligenceApi.createIndustryResearch.mockRejectedValue({
      response: { data: { error: 'DeepSeek API 密钥未配置' } },
    });

    renderPage();

    const input = screen.getByPlaceholderText(/合成生物学/);
    fireEvent.change(input, { target: { value: '测试查询' } });

    const button = screen.getByRole('button', { name: /开始分析/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/DeepSeek API 密钥未配置/)).toBeInTheDocument();
    });
  });

  it('WebSocket task_completed 事件更新结果', async () => {
    const taskId = 'ws-test-task';
    intelligenceApi.createIndustryResearch.mockResolvedValue({
      data: { task_id: taskId },
    });

    let completedCallback;
    onTaskCompleted.mockImplementation((cb) => {
      completedCallback = cb;
      return vi.fn();
    });

    renderPage();

    const input = screen.getByPlaceholderText(/合成生物学/);
    fireEvent.change(input, { target: { value: '测试' } });
    fireEvent.click(screen.getByRole('button', { name: /开始分析/ }));

    await waitFor(() => {
      expect(onTaskCompleted).toHaveBeenCalled();
    });

    // Simulate task_completed event
    if (completedCallback) {
      completedCallback({
        task_id: taskId,
        result: {
          industry_name: '测试行业',
          summary: '测试总结',
          industry_chain: '上游 → 下游',
          technology_routes: [],
          market_size: '100亿',
          top_stocks: [],
          risk_alerts: [],
          catalysts: [],
          heat_score: 50,
          competitive_landscape: '测试',
        },
      });
    }

    await waitFor(() => {
      expect(screen.getByText(/测试行业/)).toBeInTheDocument();
    });
  });

  it('WebSocket task_failed 事件展示错误', async () => {
    const taskId = 'fail-test-task';
    intelligenceApi.createIndustryResearch.mockResolvedValue({
      data: { task_id: taskId },
    });

    let failedCallback;
    onTaskFailed.mockImplementation((cb) => {
      failedCallback = cb;
      return vi.fn();
    });

    renderPage();

    const input = screen.getByPlaceholderText(/合成生物学/);
    fireEvent.change(input, { target: { value: '测试' } });
    fireEvent.click(screen.getByRole('button', { name: /开始分析/ }));

    await waitFor(() => {
      expect(onTaskFailed).toHaveBeenCalled();
    });

    if (failedCallback) {
      failedCallback({
        task_id: taskId,
        error: 'LLM 调用超时',
      });
    }

    await waitFor(() => {
      expect(screen.getByText(/LLM 调用超时/)).toBeInTheDocument();
    });
  });
});

/**
 * Property 1: 行业认知 API 调用正确性
 * Feature: real-service-integration, Property 1: 行业认知 API 调用正确性
 * Validates: Requirements 1.1
 */
describe('Property 1: 行业认知 API 调用正确性', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('对任意非空查询字符串，应调用 createIndustryResearch 并传入该字符串', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }).filter((s) => s.trim().length > 0),
        async (query) => {
          vi.clearAllMocks();
          cleanup();
          const taskId = `task-${Math.random()}`;
          intelligenceApi.createIndustryResearch.mockResolvedValue({
            data: { task_id: taskId },
          });

          renderPage();

          const input = screen.getByPlaceholderText(/合成生物学/);
          fireEvent.change(input, { target: { value: query } });
          fireEvent.click(screen.getByRole('button', { name: /开始分析/ }));

          await waitFor(() => {
            expect(intelligenceApi.createIndustryResearch).toHaveBeenCalledWith(query.trim());
          });

          cleanup();
        }
      ),
      { numRuns: 15 }
    );
  }, 30000);
});
