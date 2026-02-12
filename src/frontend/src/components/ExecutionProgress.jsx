/**
 * 策略执行进度组件
 *
 * 通过 WebSocket 实时显示策略执行进度，支持取消操作。
 * 当 WebSocket 不可用时，自动回退到 REST API 轮询。
 *
 * Requirements: 7.3, 7.4, 7.5, 7.6
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { Progress, Card, Typography, Button, Space, Alert } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { screeningSocket } from '../services/screeningSocket';
import { screeningApi } from '../services/api';

const { Text } = Typography;

const PHASE_LABELS = {
  fetch_list: '获取股票列表',
  fetch_data: '获取股票数据',
  filter: '执行筛选',
  score: '计算评分',
  save: '保存结果',
};

const POLL_INTERVAL = 2000; // 轮询间隔 2 秒

function ExecutionProgress({ taskId, onComplete, onFailed, onCancel }) {
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('');
  const [message, setMessage] = useState('准备执行...');
  const [status, setStatus] = useState('running'); // running | completed | failed | cancelled
  const [error, setError] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  const pollTimerRef = useRef(null);
  const statusRef = useRef('running');

  // 保持 statusRef 同步
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  // 轮询任务状态
  const pollTaskStatus = useCallback(async () => {
    if (statusRef.current !== 'running') return;
    try {
      const res = await screeningApi.getTask(taskId);
      const task = res.data;

      if (task.progress !== undefined) setProgress(task.progress);
      if (task.current_step) setPhase(task.current_step);

      if (task.status === 'completed') {
        setProgress(100);
        setStatus('completed');
        setMessage('执行完成');
        onComplete?.(task.result);
      } else if (task.status === 'failed') {
        setStatus('failed');
        setError(task.error_message || '执行失败');
        setMessage(`执行失败: ${task.error_message || '未知错误'}`);
        onFailed?.(task.error_message);
      } else if (task.status === 'cancelled') {
        setStatus('cancelled');
        setMessage('任务已取消');
      } else if (task.status === 'running') {
        const phaseLabel = PHASE_LABELS[task.current_step] || task.current_step || '';
        setMessage(phaseLabel ? `${phaseLabel} (${task.progress}%)` : '执行中...');
      }
    } catch {
      // 轮询失败时静默忽略，下次重试
    }
  }, [taskId, onComplete, onFailed]);

  useEffect(() => {
    // 尝试连接 WebSocket
    screeningSocket.connect();

    screeningSocket.subscribe(taskId, {
      progress: (data) => {
        setProgress(data.progress);
        setPhase(data.phase);
        setMessage(data.message);
      },
      completed: (data) => {
        setProgress(100);
        setStatus('completed');
        setMessage('执行完成');
        onComplete?.(data.result);
      },
      failed: (data) => {
        setStatus('failed');
        setError(data.error);
        setMessage(`执行失败: ${data.error}`);
        onFailed?.(data.error);
      },
      status: (data) => {
        if (data.status === 'cancelled') {
          setStatus('cancelled');
          setMessage('任务已取消');
        }
      },
    });

    // 同时启动轮询作为回退机制
    pollTimerRef.current = setInterval(pollTaskStatus, POLL_INTERVAL);

    return () => {
      screeningSocket.unsubscribe(taskId);
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    };
  }, [taskId, onComplete, onFailed, pollTaskStatus]);

  // 当任务结束时停止轮询
  useEffect(() => {
    if (status !== 'running' && pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, [status]);

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      await screeningApi.cancelTask(taskId);
      setStatus('cancelled');
      setMessage('任务已取消');
      onCancel?.();
    } catch {
      // ignore cancel errors
    } finally {
      setCancelling(false);
    }
  }, [taskId, onCancel]);

  const progressStatus =
    status === 'completed' ? 'success' :
    status === 'failed' ? 'exception' :
    'active';

  const icon =
    status === 'completed' ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> :
    status === 'failed' ? <CloseCircleOutlined style={{ color: '#ff4d4f' }} /> :
    status === 'cancelled' ? <StopOutlined style={{ color: '#faad14' }} /> :
    <LoadingOutlined />;

  return (
    <Card
      title={
        <Space>
          {icon}
          <span>策略执行中</span>
        </Space>
      }
    >
      <Progress
        percent={progress}
        status={progressStatus}
        strokeColor={status === 'cancelled' ? '#faad14' : undefined}
      />
      <div style={{ marginTop: 12 }}>
        {phase && (
          <Text type="secondary" style={{ marginRight: 12 }}>
            阶段: {PHASE_LABELS[phase] || phase}
          </Text>
        )}
        <Text>{message}</Text>
      </div>
      {error && (
        <Alert
          type="error"
          message={error}
          style={{ marginTop: 12 }}
          showIcon
        />
      )}
      {status === 'running' && (
        <div style={{ marginTop: 16 }}>
          <Button
            danger
            icon={<StopOutlined />}
            loading={cancelling}
            onClick={handleCancel}
          >
            取消执行
          </Button>
        </div>
      )}
    </Card>
  );
}

export default ExecutionProgress;
