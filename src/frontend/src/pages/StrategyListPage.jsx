import { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Popconfirm, message, Tag, Typography, Modal } from 'antd';
import { PlusOutlined, PlayCircleOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { screeningApi } from '../services/api';
import ExecutionProgress from '../components/ExecutionProgress';

const { Title } = Typography;

function StrategyListPage() {
  const [strategies, setStrategies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [executingId, setExecutingId] = useState(null);
  const [executingTaskId, setExecutingTaskId] = useState(null);
  const navigate = useNavigate();

  const fetchStrategies = useCallback(async () => {
    setLoading(true);
    try {
      const response = await screeningApi.getStrategies();
      setStrategies(response.data.strategies || []);
    } catch (err) {
      message.error('获取策略列表失败: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStrategies();
  }, [fetchStrategies]);

  const handleDelete = async (id) => {
    try {
      await screeningApi.deleteStrategy(id);
      message.success('策略已删除');
      fetchStrategies();
    } catch (err) {
      message.error('删除失败: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleExecute = async (id) => {
    setExecutingId(id);
    try {
      const response = await screeningApi.executeStrategy(id);
      const taskId = response.data?.task_id;
      if (taskId) {
        setExecutingTaskId(taskId);
      } else {
        message.warning('未获取到任务 ID');
        setExecutingId(null);
      }
    } catch (err) {
      message.error('执行失败: ' + (err.response?.data?.error || err.message));
      setExecutingId(null);
    }
  };

  const handleExecutionComplete = useCallback((result) => {
    setExecutingTaskId(null);
    setExecutingId(null);
    message.success(`策略执行完成，匹配 ${result?.matched_count ?? 0} 只股票`);
    const sessionId = result?.session_id;
    if (sessionId) {
      navigate(`/results/${sessionId}`);
    }
  }, [navigate]);

  const handleExecutionFailed = useCallback(() => {
    setExecutingTaskId(null);
    setExecutingId(null);
  }, []);

  const handleExecutionCancel = useCallback(() => {
    setExecutingTaskId(null);
    setExecutingId(null);
  }, []);

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'name',
      key: 'name',
      width: 180,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '标签',
      dataIndex: 'tags',
      key: 'tags',
      width: 200,
      render: (tags) =>
        tags && tags.length > 0
          ? tags.map((tag) => (
              <Tag color="blue" key={tag}>
                {tag}
              </Tag>
            ))
          : '-',
    },
    {
      title: '模板',
      dataIndex: 'is_template',
      key: 'is_template',
      width: 80,
      render: (isTemplate) =>
        isTemplate ? <Tag color="green">是</Tag> : <Tag>否</Tag>,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => {
        if (!text) return '-';
        const date = new Date(text);
        return date.toLocaleString('zh-CN');
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="primary"
            size="small"
            icon={<PlayCircleOutlined />}
            loading={executingId === record.strategy_id}
            onClick={() => handleExecute(record.strategy_id)}
          >
            执行
          </Button>
          <Popconfirm
            title="确认删除"
            description="确定要删除这个策略吗？"
            onConfirm={() => handleDelete(record.strategy_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="primary" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Title level={2} style={{ margin: 0 }}>
          策略列表
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/strategies/create')}
        >
          创建策略
        </Button>
      </div>

      <Modal
        title={null}
        open={!!executingTaskId}
        footer={null}
        closable={false}
        maskClosable={false}
        width={520}
        destroyOnClose
      >
        {executingTaskId && (
          <ExecutionProgress
            taskId={executingTaskId}
            onComplete={handleExecutionComplete}
            onFailed={handleExecutionFailed}
            onCancel={handleExecutionCancel}
          />
        )}
      </Modal>

      <Table
        columns={columns}
        dataSource={strategies}
        rowKey="strategy_id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
        locale={{ emptyText: '暂无策略数据' }}
      />
    </div>
  );
}

export default StrategyListPage;
