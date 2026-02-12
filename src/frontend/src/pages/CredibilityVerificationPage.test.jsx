/**
 * CredibilityVerificationPage 单元测试
 *
 * Feature: real-service-integration
 * Property 2: 可信度验证 API 调用正确性
 * Validates: Requirements 2.1
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import fc from 'fast-check';
import CredibilityVerificationPage from './CredibilityVerificationPage';

// Mock intelligenceApi and WebSocket functions
vi.mock('../services/intelligenceApi', () => ({
  intelligenceApi: {
    createCredibilityVerification: vi.fn(),
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
      <CredibilityVerificationPage />
    </MemoryRouter>
  );
}

describe('CredibilityVerificationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('调用真实 API 并获取 task_id', async () => {
    const taskId = 'cred-task-123';
    intelligenceApi.createCredibilityVerification.mockResolvedValue({
      data: { task_id: taskId },
    });

    renderPage();

    const stockInput = screen.getByPlaceholderText(/600519/);
    const conceptInput = screen.getByPlaceholderText(/AI\+白酒/);
    fireEvent.change(stockInput, { target: { value: '600519.SH' } });
    fireEvent.change(conceptInput, { target: { value: 'AI+白酒' } });

    const button = screen.getByRole('button', { name: /开始验证/ });
    fireEvent.click(button);

    await waitFor(() => {
      expect(intelligenceApi.createCredibilityVerification).toHaveBeenCalledWith(
        '600519.SH',
        'AI+白酒'
      );
    });

    await waitFor(() => {
      expect(connectWebSocket).toHaveBeenCalled();
      expect(joinTaskRoom).toHaveBeenCalledWith(taskId);
    });
  });

  it('API 错误时展示错误信息', async () => {
    intelligenceApi.createCredibilityVerification.mockRejectedValue({
      response: { data: { error: 'API 密钥未配置' } },
    });

    renderPage();

    const stockInput = screen.getByPlaceholderText(/600519/);
    const conceptInput = screen.getByPlaceholderText(/AI\+白酒/);
    fireEvent.change(stockInput, { target: { value: '600519.SH' } });
    fireEvent.change(conceptInput, { target: { value: '测试概念' } });

    fireEvent.click(screen.getByRole('button', { name: /开始验证/ }));

    await waitFor(() => {
      expect(screen.getByText(/API 密钥未配置/)).toBeInTheDocument();
    });
  });

  it('WebSocket task_completed 事件更新结果', async () => {
    const taskId = 'ws-cred-task';
    intelligenceApi.createCredibilityVerification.mockResolvedValue({
      data: { task_id: taskId },
    });

    let completedCallback;
    onTaskCompleted.mockImplementation((cb) => {
      completedCallback = cb;
      return vi.fn();
    });

    renderPage();

    fireEvent.change(screen.getByPlaceholderText(/600519/), {
      target: { value: '600519.SH' },
    });
    fireEvent.change(screen.getByPlaceholderText(/AI\+白酒/), {
      target: { value: '测试概念' },
    });
    fireEvent.click(screen.getByRole('button', { name: /开始验证/ }));

    await waitFor(() => {
      expect(onTaskCompleted).toHaveBeenCalled();
    });

    if (completedCallback) {
      completedCallback({
        task_id: taskId,
        result: {
          stock_code: '600519.SH',
          stock_name: '贵州茅台',
          concept: '测试概念',
          overall_score: { score: 30, level: '低可信度' },
          main_business_match: { score: 10, main_business_description: '白酒', match_analysis: '不匹配' },
          evidence: { score: 10, patents: [], orders: [], partnerships: [], analysis: '无' },
          hype_history: { score: 40, past_concepts: [], analysis: '无' },
          supply_chain_logic: { score: 10, upstream: [], downstream: [], analysis: '无' },
          risk_labels: [],
          conclusion: '测试结论',
        },
      });
    }

    await waitFor(() => {
      expect(screen.getByText(/贵州茅台/)).toBeInTheDocument();
    });
  });

  it('WebSocket task_failed 事件展示错误', async () => {
    const taskId = 'fail-cred-task';
    intelligenceApi.createCredibilityVerification.mockResolvedValue({
      data: { task_id: taskId },
    });

    let failedCallback;
    onTaskFailed.mockImplementation((cb) => {
      failedCallback = cb;
      return vi.fn();
    });

    renderPage();

    fireEvent.change(screen.getByPlaceholderText(/600519/), {
      target: { value: '600519.SH' },
    });
    fireEvent.change(screen.getByPlaceholderText(/AI\+白酒/), {
      target: { value: '测试' },
    });
    fireEvent.click(screen.getByRole('button', { name: /开始验证/ }));

    await waitFor(() => {
      expect(onTaskFailed).toHaveBeenCalled();
    });

    if (failedCallback) {
      failedCallback({
        task_id: taskId,
        error: '工作流执行失败',
      });
    }

    await waitFor(() => {
      expect(screen.getByText(/工作流执行失败/)).toBeInTheDocument();
    });
  });
});

/**
 * Property 2: 可信度验证 API 调用正确性
 * Feature: real-service-integration, Property 2: 可信度验证 API 调用正确性
 * Validates: Requirements 2.1
 */
describe('Property 2: 可信度验证 API 调用正确性', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('对任意有效股票代码和非空概念，应调用 createCredibilityVerification', async () => {
    // Generate valid A-share stock codes that pass the regex ^\d{6}\.(SH|SZ)$/i
    const stockCodeArb = fc.oneof(
      fc.integer({ min: 600000, max: 699999 }).map((n) => `${n}.SH`),
      fc.integer({ min: 0, max: 399999 }).map((n) => `${String(n).padStart(6, '0')}.SZ`)
    );
    // Use simple alphanumeric concepts to avoid Antd form issues with special chars
    const conceptArb = fc.stringMatching(/^[\u4e00-\u9fa5A-Za-z0-9+]{1,20}$/);

    await fc.assert(
      fc.asyncProperty(stockCodeArb, conceptArb, async (stockCode, concept) => {
        vi.clearAllMocks();
        cleanup();
        const taskId = `task-${Math.random()}`;
        intelligenceApi.createCredibilityVerification.mockResolvedValue({
          data: { task_id: taskId },
        });

        renderPage();

        fireEvent.change(screen.getByPlaceholderText(/600519/), {
          target: { value: stockCode },
        });
        fireEvent.change(screen.getByPlaceholderText(/AI\+白酒/), {
          target: { value: concept },
        });
        fireEvent.click(screen.getByRole('button', { name: /开始验证/ }));

        await waitFor(() => {
          expect(intelligenceApi.createCredibilityVerification).toHaveBeenCalledWith(
            stockCode,
            concept
          );
        });

        cleanup();
      }),
      { numRuns: 10 }
    );
  }, 30000);
});
