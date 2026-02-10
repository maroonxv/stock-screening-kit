import { useState, useCallback, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Space,
  Button,
  Select,
  Empty,
  Typography,
  Progress,
  Modal,
  Descriptions,
  Divider,
  message,
  Tooltip,
  Row,
  Col,
} from 'antd';
import {
  HistoryOutlined,
  ReloadOutlined,
  EyeOutlined,
  StopOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import AgentProgressSteps from '../components/AgentProgressSteps';

const { Title, Text } = Typography;
const { Option } = Select;

/**
 * 调研任务历史列表页面
 * 
 * 功能：
 * 1. 任务列表（状态、类型、创建时间）
 * 2. WebSocket 实时更新进度
 * 3. 任务类型筛选和状态筛选
 * 4. 点击查看任务详情
 * 
 * Requirements: 9.5, 9.6
 */

// 任务状态枚举
const TaskStatus = {
  PENDING: 'pending',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
};

// 任务类型枚举
const TaskType = {
  INDUSTRY_RESEARCH: 'industry_research',
  CREDIBILITY_VERIFICATION: 'credibility_verification',
};

// 任务状态配置
const STATUS_CONFIG = {
  [TaskStatus.PENDING]: {
    color: 'default',
    text: '等待中',
    icon: <ClockCircleOutlined />,
  },
  [TaskStatus.RUNNING]: {
    color: 'processing',
    text: '执行中',
    icon: <SyncOutlined spin />,
  },
  [TaskStatus.COMPLETED]: {
    color: 'success',
    text: '已完成',
    icon: <CheckCircleOutlined />,
  },
  [TaskStatus.FAILED]: {
    color: 'error',
    text: '失败',
    icon: <CloseCircleOutlined />,
  },
  [TaskStatus.CANCELLED]: {
    color: 'warning',
    text: '已取消',
    icon: <ExclamationCircleOutlined />,
  },
};

// 任务类型配置
const TYPE_CONFIG = {
  [TaskType.INDUSTRY_RESEARCH]: {
    color: 'blue',
    text: '快速行业认知',
    icon: <RocketOutlined />,
  },
  [TaskType.CREDIBILITY_VERIFICATION]: {
    color: 'purple',
    text: '概念可信度验证',
    icon: <SafetyCertificateOutlined />,
  },
};

function TaskHistoryPage() {
  // 状态管理
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState(null);
  const [typeFilter, setTypeFilter] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });

  // 加载任务列表
  const loadTasks = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      // TODO: 实际 API 调用将在 Task 13.4 中实现
      // const response = await intelligenceApi.listTasks({
      //   page,
      //   page_size: pageSize,
      //   status: statusFilter,
      //   task_type: typeFilter,
      // });
      // setTasks(response.data.tasks);
      // setPagination({
      //   current: page,
      //   pageSize,
      //   total: response.data.total,
      // });

      // 模拟数据
      const mockTasks = getMockTasks();
      let filteredTasks = mockTasks;
      
      // 应用筛选
      if (statusFilter) {
        filteredTasks = filteredTasks.filter(t => t.status === statusFilter);
      }
      if (typeFilter) {
        filteredTasks = filteredTasks.filter(t => t.task_type === typeFilter);
      }

      setTasks(filteredTasks);
      setPagination({
        current: page,
        pageSize,
        total: filteredTasks.length,
      });
    } catch (err) {
      message.error(err.response?.data?.error || err.message || '加载任务列表失败');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter]);

  // 初始加载
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  // WebSocket 连接（模拟实现）
  useEffect(() => {
    // TODO: 实际 WebSocket 连接将在 Task 13.4 中实现
    // const socket = io('/intelligence');
    // 
    // socket.on('task_progress', (data) => {
    //   setTasks(prevTasks => 
    //     prevTasks.map(task => 
    //       task.task_id === data.task_id 
    //         ? { ...task, progress: data.progress, agent_steps: data.agent_steps }
    //         : task
    //     )
    //   );
    // });
    // 
    // socket.on('task_completed', (data) => {
    //   setTasks(prevTasks => 
    //     prevTasks.map(task => 
    //       task.task_id === data.task_id 
    //         ? { ...task, status: 'completed', progress: 100, result: data.result }
    //         : task
    //     )
    //   );
    // });
    // 
    // return () => socket.disconnect();

    // 模拟 WebSocket 实时更新
    const interval = setInterval(() => {
      setTasks(prevTasks => 
        prevTasks.map(task => {
          if (task.status === TaskStatus.RUNNING && task.progress < 100) {
            const newProgress = Math.min(task.progress + 10, 100);
            return {
              ...task,
              progress: newProgress,
              status: newProgress >= 100 ? TaskStatus.COMPLETED : TaskStatus.RUNNING,
            };
          }
          return task;
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // 查看任务详情
  const handleViewDetail = useCallback((task) => {
    setSelectedTask(task);
    setDetailModalVisible(true);
  }, []);

  // 取消任务
  const handleCancelTask = useCallback(async (taskId) => {
    try {
      // TODO: 实际 API 调用将在 Task 13.4 中实现
      // await intelligenceApi.cancelTask(taskId);
      
      // 模拟取消
      setTasks(prevTasks =>
        prevTasks.map(task =>
          task.task_id === taskId
            ? { ...task, status: TaskStatus.CANCELLED }
            : task
        )
      );
      message.success('任务已取消');
    } catch (err) {
      message.error(err.response?.data?.error || err.message || '取消任务失败');
    }
  }, []);

  // 刷新列表
  const handleRefresh = useCallback(() => {
    loadTasks(pagination.current, pagination.pageSize);
  }, [loadTasks, pagination.current, pagination.pageSize]);

  // 表格分页变化
  const handleTableChange = useCallback((newPagination) => {
    loadTasks(newPagination.current, newPagination.pageSize);
  }, [loadTasks]);

  // 重置筛选
  const handleResetFilters = useCallback(() => {
    setStatusFilter(null);
    setTypeFilter(null);
  }, []);

  // 表格列定义
  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 120,
      ellipsis: true,
      render: (taskId) => (
        <Tooltip title={taskId}>
          <Text copyable={{ text: taskId }} style={{ fontSize: 12 }}>
            {taskId.substring(0, 8)}...
          </Text>
        </Tooltip>
      ),
    },
    {
      title: '任务类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 150,
      render: (type) => {
        const config = TYPE_CONFIG[type] || { color: 'default', text: type, icon: null };
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '查询内容',
      dataIndex: 'query',
      key: 'query',
      ellipsis: true,
      render: (query) => (
        <Tooltip title={query}>
          <Text>{query}</Text>
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = STATUS_CONFIG[status] || { color: 'default', text: status, icon: null };
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 120,
      render: (progress, record) => (
        <Progress
          percent={progress || 0}
          size="small"
          status={
            record.status === TaskStatus.FAILED
              ? 'exception'
              : record.status === TaskStatus.RUNNING
              ? 'active'
              : undefined
          }
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (createdAt) => formatDateTime(createdAt),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {(record.status === TaskStatus.PENDING || record.status === TaskStatus.RUNNING) && (
            <Button
              type="link"
              size="small"
              danger
              icon={<StopOutlined />}
              onClick={() => handleCancelTask(record.task_id)}
            >
              取消
            </Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>
        <HistoryOutlined style={{ marginRight: 8 }} />
        调研任务历史
      </Title>
      <Text type="secondary">
        查看所有调研任务的执行状态和结果
      </Text>

      {/* 筛选区域 */}
      <Card style={{ marginTop: 24, marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Text>任务类型：</Text>
              <Select
                placeholder="全部类型"
                style={{ width: 180 }}
                allowClear
                value={typeFilter}
                onChange={setTypeFilter}
              >
                <Option value={TaskType.INDUSTRY_RESEARCH}>
                  <Space>
                    <RocketOutlined />
                    快速行业认知
                  </Space>
                </Option>
                <Option value={TaskType.CREDIBILITY_VERIFICATION}>
                  <Space>
                    <SafetyCertificateOutlined />
                    概念可信度验证
                  </Space>
                </Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Space>
              <Text>状态：</Text>
              <Select
                placeholder="全部状态"
                style={{ width: 140 }}
                allowClear
                value={statusFilter}
                onChange={setStatusFilter}
              >
                <Option value={TaskStatus.PENDING}>等待中</Option>
                <Option value={TaskStatus.RUNNING}>执行中</Option>
                <Option value={TaskStatus.COMPLETED}>已完成</Option>
                <Option value={TaskStatus.FAILED}>失败</Option>
                <Option value={TaskStatus.CANCELLED}>已取消</Option>
              </Select>
            </Space>
          </Col>
          <Col flex="auto" style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={handleResetFilters}>重置筛选</Button>
              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={handleRefresh}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 任务列表 */}
      <Card>
        {tasks.length > 0 ? (
          <Table
            columns={columns}
            dataSource={tasks}
            rowKey="task_id"
            loading={loading}
            pagination={{
              ...pagination,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条记录`,
            }}
            onChange={handleTableChange}
            scroll={{ x: 1000 }}
          />
        ) : (
          <Empty
            description="暂无调研任务"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Card>

      {/* 任务详情弹窗 */}
      <TaskDetailModal
        visible={detailModalVisible}
        task={selectedTask}
        onClose={() => {
          setDetailModalVisible(false);
          setSelectedTask(null);
        }}
      />
    </div>
  );
}

/**
 * 任务详情弹窗组件
 */
function TaskDetailModal({ visible, task, onClose }) {
  if (!task) return null;

  const statusConfig = STATUS_CONFIG[task.status] || { color: 'default', text: task.status };
  const typeConfig = TYPE_CONFIG[task.task_type] || { color: 'default', text: task.task_type };

  return (
    <Modal
      title={
        <Space>
          <HistoryOutlined />
          任务详情
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>
          关闭
        </Button>,
      ]}
      width={800}
    >
      {/* 基本信息 */}
      <Descriptions column={2} bordered size="small">
        <Descriptions.Item label="任务ID" span={2}>
          <Text copyable>{task.task_id}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="任务类型">
          <Tag color={typeConfig.color} icon={typeConfig.icon}>
            {typeConfig.text}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={statusConfig.color} icon={statusConfig.icon}>
            {statusConfig.text}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="查询内容" span={2}>
          {task.query}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {formatDateTime(task.created_at)}
        </Descriptions.Item>
        <Descriptions.Item label="完成时间">
          {task.completed_at ? formatDateTime(task.completed_at) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="进度" span={2}>
          <Progress
            percent={task.progress || 0}
            status={
              task.status === TaskStatus.FAILED
                ? 'exception'
                : task.status === TaskStatus.RUNNING
                ? 'active'
                : undefined
            }
          />
        </Descriptions.Item>
      </Descriptions>

      {/* Agent 执行步骤 */}
      {task.agent_steps && task.agent_steps.length > 0 && (
        <>
          <Divider>执行步骤</Divider>
          <AgentProgressSteps agentSteps={task.agent_steps} />
        </>
      )}

      {/* 错误信息 */}
      {task.error_message && (
        <>
          <Divider>错误信息</Divider>
          <Text type="danger">{task.error_message}</Text>
        </>
      )}

      {/* 结果摘要 */}
      {task.result && (
        <>
          <Divider>结果摘要</Divider>
          <TaskResultSummary task={task} />
        </>
      )}
    </Modal>
  );
}

/**
 * 任务结果摘要组件
 */
function TaskResultSummary({ task }) {
  const { task_type, result } = task;

  if (task_type === TaskType.INDUSTRY_RESEARCH && result) {
    return (
      <Descriptions column={1} size="small">
        <Descriptions.Item label="行业名称">
          {result.industry_name}
        </Descriptions.Item>
        <Descriptions.Item label="行业总结">
          <Text ellipsis={{ rows: 3, expandable: true }}>
            {result.summary}
          </Text>
        </Descriptions.Item>
        <Descriptions.Item label="市场热度">
          <Progress
            type="circle"
            percent={result.heat_score || 0}
            size={60}
            strokeColor={getHeatColor(result.heat_score)}
          />
        </Descriptions.Item>
        <Descriptions.Item label="核心标的数量">
          {result.top_stocks?.length || 0} 只
        </Descriptions.Item>
      </Descriptions>
    );
  }

  if (task_type === TaskType.CREDIBILITY_VERIFICATION && result) {
    return (
      <Descriptions column={1} size="small">
        <Descriptions.Item label="股票">
          {result.stock_name}（{result.stock_code}）
        </Descriptions.Item>
        <Descriptions.Item label="验证概念">
          {result.concept}
        </Descriptions.Item>
        <Descriptions.Item label="可信度评分">
          <Space>
            <Progress
              type="circle"
              percent={result.overall_score?.score || 0}
              size={60}
              strokeColor={getScoreColor(result.overall_score?.score)}
            />
            <Tag color={getScoreLevelColor(result.overall_score?.level)}>
              {result.overall_score?.level || '-'}
            </Tag>
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="结论">
          <Text ellipsis={{ rows: 3, expandable: true }}>
            {result.conclusion}
          </Text>
        </Descriptions.Item>
      </Descriptions>
    );
  }

  return <Text type="secondary">暂无结果数据</Text>;
}

// 辅助函数：格式化日期时间
function formatDateTime(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

// 辅助函数：根据评分获取颜色
function getScoreColor(score) {
  if (score >= 80) return '#52c41a';
  if (score >= 50) return '#faad14';
  return '#ff4d4f';
}

function getScoreLevelColor(level) {
  if (level === '高可信度') return 'success';
  if (level === '中可信度') return 'warning';
  return 'error';
}

function getHeatColor(score) {
  if (score >= 80) return '#ff4d4f';
  if (score >= 60) return '#faad14';
  if (score >= 40) return '#1890ff';
  return '#52c41a';
}

// 模拟任务数据
function getMockTasks() {
  return [
    {
      task_id: 'task-001-uuid-1234-5678-abcd',
      task_type: TaskType.INDUSTRY_RESEARCH,
      query: '快速了解合成生物学赛道',
      status: TaskStatus.COMPLETED,
      progress: 100,
      created_at: '2024-01-15T10:30:00Z',
      completed_at: '2024-01-15T10:45:00Z',
      agent_steps: [
        { agent_name: '行业背景速览', status: 'completed', output_summary: '分析完成' },
        { agent_name: '市场热度分析', status: 'completed', output_summary: '分析完成' },
        { agent_name: '标的快速筛选', status: 'completed', output_summary: '分析完成' },
        { agent_name: '真实性批量验证', status: 'completed', output_summary: '分析完成' },
        { agent_name: '竞争格局速览', status: 'completed', output_summary: '分析完成' },
      ],
      result: {
        industry_name: '合成生物学',
        summary: '合成生物学是一门融合生物学、工程学和计算机科学的新兴交叉学科...',
        heat_score: 75,
        top_stocks: [
          { stock_code: '688399.SH', stock_name: '硕世生物' },
          { stock_code: '688185.SH', stock_name: '康希诺' },
        ],
      },
    },
    {
      task_id: 'task-002-uuid-2345-6789-bcde',
      task_type: TaskType.CREDIBILITY_VERIFICATION,
      query: '600519.SH - AI+白酒',
      status: TaskStatus.COMPLETED,
      progress: 100,
      created_at: '2024-01-15T11:00:00Z',
      completed_at: '2024-01-15T11:10:00Z',
      agent_steps: [
        { agent_name: '主营业务分析', status: 'completed', output_summary: '分析完成' },
        { agent_name: '证据收集', status: 'completed', output_summary: '分析完成' },
        { agent_name: '历史蹭热点检测', status: 'completed', output_summary: '分析完成' },
        { agent_name: '供应链逻辑验证', status: 'completed', output_summary: '分析完成' },
      ],
      result: {
        stock_code: '600519.SH',
        stock_name: '贵州茅台',
        concept: 'AI+白酒',
        overall_score: { score: 15, level: '低可信度' },
        conclusion: '综合分析显示，该公司声称的 AI+白酒 概念可信度极低...',
      },
    },
    {
      task_id: 'task-003-uuid-3456-7890-cdef',
      task_type: TaskType.INDUSTRY_RESEARCH,
      query: '分析新能源汽车产业链',
      status: TaskStatus.RUNNING,
      progress: 60,
      created_at: '2024-01-15T12:00:00Z',
      completed_at: null,
      agent_steps: [
        { agent_name: '行业背景速览', status: 'completed', output_summary: '分析完成' },
        { agent_name: '市场热度分析', status: 'completed', output_summary: '分析完成' },
        { agent_name: '标的快速筛选', status: 'running' },
      ],
      result: null,
    },
    {
      task_id: 'task-004-uuid-4567-8901-defg',
      task_type: TaskType.CREDIBILITY_VERIFICATION,
      query: '000001.SZ - 数字货币',
      status: TaskStatus.PENDING,
      progress: 0,
      created_at: '2024-01-15T12:30:00Z',
      completed_at: null,
      agent_steps: [],
      result: null,
    },
    {
      task_id: 'task-005-uuid-5678-9012-efgh',
      task_type: TaskType.INDUSTRY_RESEARCH,
      query: '了解人工智能芯片行业',
      status: TaskStatus.FAILED,
      progress: 40,
      created_at: '2024-01-15T09:00:00Z',
      completed_at: '2024-01-15T09:15:00Z',
      agent_steps: [
        { agent_name: '行业背景速览', status: 'completed', output_summary: '分析完成' },
        { agent_name: '市场热度分析', status: 'failed', error_message: 'LLM 服务超时' },
      ],
      error_message: 'LLM 服务调用超时，请稍后重试',
      result: null,
    },
    {
      task_id: 'task-006-uuid-6789-0123-fghi',
      task_type: TaskType.CREDIBILITY_VERIFICATION,
      query: '300750.SZ - 固态电池',
      status: TaskStatus.CANCELLED,
      progress: 25,
      created_at: '2024-01-15T08:00:00Z',
      completed_at: '2024-01-15T08:05:00Z',
      agent_steps: [
        { agent_name: '主营业务分析', status: 'completed', output_summary: '分析完成' },
      ],
      result: null,
    },
  ];
}

export default TaskHistoryPage;
