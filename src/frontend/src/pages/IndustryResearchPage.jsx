import { useState, useCallback, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  Row,
  Col,
  Typography,
  Alert,
  Progress,
  Table,
  Tag,
  List,
  Divider,
  Space,
  Empty,
  message,
} from 'antd';
import {
  SearchOutlined,
  RocketOutlined,
  FireOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons';
import AgentProgressSteps from '../components/AgentProgressSteps';
import {
  intelligenceApi,
  connectWebSocket,
  disconnectWebSocket,
  joinTaskRoom,
  leaveTaskRoom,
  onTaskProgress,
  onTaskCompleted,
  onTaskFailed,
} from '../services/intelligenceApi';

const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

/**
 * 快速行业认知页面
 * 
 * 功能：
 * 1. 查询输入框 + 提交按钮
 * 2. 任务进度展示（各 Agent 状态）
 * 3. 结果展示（行业总结、核心标的列表、风险提示、催化剂、热度评分、竞争格局）
 * 
 * Requirements: 9.1, 9.2, 9.3
 */

// 任务状态枚举
const TaskStatus = {
  IDLE: 'idle',           // 空闲，等待用户输入
  PENDING: 'pending',     // 任务已创建，等待执行
  RUNNING: 'running',     // 任务执行中
  COMPLETED: 'completed', // 任务完成
  FAILED: 'failed',       // 任务失败
};

function IndustryResearchPage() {
  // 状态管理
  const [query, setQuery] = useState('');
  const [taskStatus, setTaskStatus] = useState(TaskStatus.IDLE);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [agentSteps, setAgentSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const taskIdRef = useRef(null);

  // 提交查询 — 调用真实后端 API
  const handleSubmit = useCallback(async (value) => {
    const trimmedQuery = value?.trim() || query.trim();
    if (!trimmedQuery) {
      message.warning('请输入查询内容');
      return;
    }

    setTaskStatus(TaskStatus.PENDING);
    setProgress(0);
    setAgentSteps([]);
    setResult(null);
    setError(null);

    try {
      const response = await intelligenceApi.createIndustryResearch(trimmedQuery);
      const newTaskId = response.data.task_id;
      setTaskId(newTaskId);
      taskIdRef.current = newTaskId;
      setTaskStatus(TaskStatus.RUNNING);

      await connectWebSocket();
      joinTaskRoom(newTaskId);
    } catch (err) {
      setError(err.response?.data?.error || err.message || '创建任务失败');
      setTaskStatus(TaskStatus.FAILED);
    }
  }, [query]);

  // WebSocket 事件订阅
  useEffect(() => {
    if (!taskId || taskStatus !== TaskStatus.RUNNING) return;

    const unsubProgress = onTaskProgress((data) => {
      if (data.task_id !== taskIdRef.current) return;
      setProgress(data.progress);
      setAgentSteps((prev) => {
        const updated = [...prev];
        const idx = updated.findIndex((s) => s.agent_name === data.agent_step.agent_name);
        if (idx >= 0) updated[idx] = data.agent_step;
        else updated.push(data.agent_step);
        return updated;
      });
    });

    const unsubCompleted = onTaskCompleted((data) => {
      if (data.task_id !== taskIdRef.current) return;
      setProgress(100);
      setResult(data.result);
      setTaskStatus(TaskStatus.COMPLETED);
      leaveTaskRoom(taskIdRef.current);
    });

    const unsubFailed = onTaskFailed((data) => {
      if (data.task_id !== taskIdRef.current) return;
      setError(data.error);
      setTaskStatus(TaskStatus.FAILED);
      leaveTaskRoom(taskIdRef.current);
    });

    return () => {
      unsubProgress();
      unsubCompleted();
      unsubFailed();
    };
  }, [taskId, taskStatus]);

  // 组件卸载时清理 WebSocket
  useEffect(() => {
    return () => {
      if (taskIdRef.current) {
        leaveTaskRoom(taskIdRef.current);
      }
      disconnectWebSocket();
    };
  }, []);

  // 重新开始
  const handleReset = () => {
    if (taskIdRef.current) {
      leaveTaskRoom(taskIdRef.current);
    }
    setQuery('');
    setTaskStatus(TaskStatus.IDLE);
    setTaskId(null);
    taskIdRef.current = null;
    setProgress(0);
    setAgentSteps([]);
    setResult(null);
    setError(null);
  };

  return (
    <div>
      <Title level={2}>
        <RocketOutlined style={{ marginRight: 8 }} />
        快速行业认知
      </Title>
      <Text type="secondary">
        输入行业或概念关键词，AI 将快速分析行业概况、核心标的、风险与机会
      </Text>

      {/* 查询输入区域 */}
      <Card style={{ marginTop: 24, marginBottom: 24 }}>
        <Search
          placeholder="例如：快速了解合成生物学赛道、分析新能源汽车产业链"
          enterButton={
            <Button type="primary" icon={<SearchOutlined />}>
              开始分析
            </Button>
          }
          size="large"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onSearch={handleSubmit}
          disabled={taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING}
          loading={taskStatus === TaskStatus.PENDING}
        />
        {(taskStatus === TaskStatus.COMPLETED || taskStatus === TaskStatus.FAILED) && (
          <Button
            type="link"
            onClick={handleReset}
            style={{ marginTop: 8 }}
          >
            重新开始
          </Button>
        )}
      </Card>

      {/* 错误提示 */}
      {error && (
        <Alert
          type="error"
          message="分析失败"
          description={error}
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 任务进度展示 */}
      {(taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING) && (
        <Card title="分析进度" style={{ marginBottom: 24 }}>
          <Progress
            percent={progress}
            status={taskStatus === TaskStatus.RUNNING ? 'active' : 'normal'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <AgentProgressSteps agentSteps={agentSteps} />
        </Card>
      )}

      {/* 结果展示 */}
      {taskStatus === TaskStatus.COMPLETED && result && (
        <IndustryInsightResult result={result} />
      )}

      {/* 空状态 */}
      {taskStatus === TaskStatus.IDLE && (
        <Card>
          <Empty
            description="输入行业关键词开始分析"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      )}
    </div>
  );
}

/**
 * 行业认知结果展示组件
 */
function IndustryInsightResult({ result }) {
  // 核心标的表格列定义
  const stockColumns = [
    {
      title: '排名',
      key: 'rank',
      width: 60,
      align: 'center',
      render: (_, __, index) => index + 1,
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 100,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 100,
    },
    {
      title: '可信度评分',
      dataIndex: 'credibility_score',
      key: 'credibility_score',
      width: 120,
      render: (score) => (
        <Space>
          <Progress
            type="circle"
            percent={score?.score || 0}
            width={40}
            strokeColor={getScoreColor(score?.score)}
            format={(percent) => percent}
          />
          <Tag color={getScoreLevelColor(score?.level)}>
            {score?.level || '-'}
          </Tag>
        </Space>
      ),
    },
    {
      title: '相关性摘要',
      dataIndex: 'relevance_summary',
      key: 'relevance_summary',
      ellipsis: true,
    },
  ];

  return (
    <div>
      {/* 行业总结 */}
      <Card
        title={
          <span>
            <RocketOutlined style={{ marginRight: 8 }} />
            {result.industry_name} - 行业总结
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Paragraph>{result.summary}</Paragraph>
        <Divider />
        <Row gutter={24}>
          <Col span={12}>
            <Title level={5}>产业链结构</Title>
            <Paragraph type="secondary">{result.industry_chain}</Paragraph>
          </Col>
          <Col span={12}>
            <Title level={5}>市场规模</Title>
            <Paragraph type="secondary">{result.market_size}</Paragraph>
          </Col>
        </Row>
        <Divider />
        <Title level={5}>技术路线</Title>
        <Space wrap>
          {result.technology_routes?.map((route, index) => (
            <Tag key={index} color="blue">
              {route}
            </Tag>
          ))}
        </Space>
      </Card>

      {/* 热度评分和竞争格局 */}
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card
            title={
              <span>
                <FireOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
                市场热度
              </span>
            }
          >
            <div style={{ textAlign: 'center' }}>
              <Progress
                type="dashboard"
                percent={result.heat_score}
                strokeColor={getHeatColor(result.heat_score)}
                format={(percent) => (
                  <span style={{ fontSize: 24, fontWeight: 'bold' }}>
                    {percent}
                  </span>
                )}
              />
              <div style={{ marginTop: 8 }}>
                <Tag color={getHeatLevelColor(result.heat_score)}>
                  {getHeatLevel(result.heat_score)}
                </Tag>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card
            title={
              <span>
                <TeamOutlined style={{ marginRight: 8 }} />
                竞争格局
              </span>
            }
            style={{ height: '100%' }}
          >
            <Paragraph>{result.competitive_landscape}</Paragraph>
          </Card>
        </Col>
      </Row>

      {/* 核心标的列表 */}
      <Card
        title={
          <span>
            <SafetyCertificateOutlined style={{ marginRight: 8 }} />
            核心标的（含可信度评分）
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={stockColumns}
          dataSource={result.top_stocks || []}
          rowKey="stock_code"
          pagination={false}
          size="middle"
        />
      </Card>

      {/* 风险提示和催化剂 */}
      <Row gutter={24}>
        <Col span={12}>
          <Card
            title={
              <span>
                <WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />
                风险提示
              </span>
            }
          >
            <List
              dataSource={result.risk_alerts || []}
              renderItem={(item, index) => (
                <List.Item>
                  <Text>
                    <Tag color="warning">{index + 1}</Tag>
                    {item}
                  </Text>
                </List.Item>
              )}
              locale={{ emptyText: '暂无风险提示' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title={
              <span>
                <ThunderboltOutlined style={{ marginRight: 8, color: '#52c41a' }} />
                催化剂
              </span>
            }
          >
            <List
              dataSource={result.catalysts || []}
              renderItem={(item, index) => (
                <List.Item>
                  <Text>
                    <Tag color="success">{index + 1}</Tag>
                    {item}
                  </Text>
                </List.Item>
              )}
              locale={{ emptyText: '暂无催化剂' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
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

function getHeatLevelColor(score) {
  if (score >= 80) return 'error';
  if (score >= 60) return 'warning';
  if (score >= 40) return 'processing';
  return 'success';
}

function getHeatLevel(score) {
  if (score >= 80) return '极高热度';
  if (score >= 60) return '较高热度';
  if (score >= 40) return '中等热度';
  return '低热度';
}

export default IndustryResearchPage;
