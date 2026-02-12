/**
 * 策略执行进度组件
 *
 * 通过 WebSocket 实时显示策略执行进度，支持取消操作。
 *
 * Requirements: 7.3, 7.4, 7.5, 7.6
 */
import { useEffect, useState, useCallback } from 'react';
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

function ExecutionProgress({ taskId, onComplete, onFailed, onCancel }) {
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('');
  const [message, setMessage] = useState('准备执行...');
  const [status, setStatus] = useState('running'); // running | completed | failed | cancelled
  const [error, setError] = useState(null);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
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

    return () => {
      screeningSocket.unsubscribe(taskId);
    };
  }, [taskId, onComplete, onFailed]);

  const handleCancel = useCallback(async () => {
    setCancelling(true);
    try {
      await screeningApi.cancelTask(taskId);
      setStatus('cancelled');
      setMessage('任务已取消');
      onCancel?.();
    } catch (err) {
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
