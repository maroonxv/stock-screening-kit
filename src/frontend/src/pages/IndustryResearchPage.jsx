import { useState, useCallback } from 'react';
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
  const [, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [agentSteps, setAgentSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 模拟任务执行进度（临时实现，实际将通过 WebSocket 接收）
  const simulateTaskProgress = useCallback(() => {
    const agents = [
      '行业背景速览',
      '市场热度分析',
      '标的快速筛选',
      '真实性批量验证',
      '竞争格局速览',
    ];

    let currentIndex = 0;
    const steps = [];

    const runNextAgent = () => {
      if (currentIndex >= agents.length) {
        // 所有 Agent 完成，生成模拟结果
        setProgress(100);
        setResult(getMockResult());
        setTaskStatus(TaskStatus.COMPLETED);
        return;
      }

      const agentName = agents[currentIndex];
      
      // 设置当前 Agent 为 running
      steps.push({
        agent_name: agentName,
        status: 'running',
        started_at: new Date().toISOString(),
      });
      setAgentSteps([...steps]);
      setProgress(Math.round((currentIndex / agents.length) * 100));

      // 模拟执行时间
      setTimeout(() => {
        // 更新当前 Agent 为 completed
        steps[steps.length - 1] = {
          ...steps[steps.length - 1],
          status: 'completed',
          completed_at: new Date().toISOString(),
          output_summary: `${agentName}分析完成`,
        };
        setAgentSteps([...steps]);
        
        currentIndex++;
        runNextAgent();
      }, 1500);
    };

    runNextAgent();
  }, []);

  // 提交查询
  const handleSubmit = useCallback((value) => {
    const trimmedQuery = value?.trim() || query.trim();
    if (!trimmedQuery) {
      message.warning('请输入查询内容');
      return;
    }

    // 重置状态
    setTaskStatus(TaskStatus.PENDING);
    setProgress(0);
    setAgentSteps([]);
    setResult(null);
    setError(null);

    try {
      // TODO: 实际 API 调用将在 Task 13.4 中实现
      // const response = await intelligenceApi.createIndustryResearch({ query: trimmedQuery });
      // setTaskId(response.data.task_id);
      
      // 模拟任务创建
      const mockTaskId = `task-${Date.now()}`;
      setTaskId(mockTaskId);
      setTaskStatus(TaskStatus.RUNNING);
      
      // 模拟任务执行进度（实际将通过 WebSocket 接收）
      simulateTaskProgress();
      
    } catch (err) {
      setError(err.response?.data?.error || err.message || '创建任务失败');
      setTaskStatus(TaskStatus.FAILED);
    }
  }, [query, simulateTaskProgress]);

  // 模拟结果数据
  const getMockResult = () => ({
    industry_name: '合成生物学',
    summary: '合成生物学是一门融合生物学、工程学和计算机科学的新兴交叉学科，通过设计和构建新的生物系统或改造现有生物系统来实现特定功能。该行业正处于快速发展期，技术突破不断涌现，商业化应用逐步落地。',
    industry_chain: '上游：基因合成、测序设备 → 中游：菌株构建、发酵工程 → 下游：医药、农业、化工、食品',
    technology_routes: ['基因编辑技术', '代谢工程', '蛋白质设计', '细胞工厂', 'AI辅助设计'],
    market_size: '全球市场规模约500亿美元，预计2030年将达到1500亿美元，年复合增长率约15%',
    top_stocks: [
      {
        stock_code: '688399.SH',
        stock_name: '硕世生物',
        credibility_score: { score: 85, level: '高可信度' },
        relevance_summary: '主营业务与合成生物学高度相关，拥有核心技术专利',
      },
      {
        stock_code: '688185.SH',
        stock_name: '康希诺',
        credibility_score: { score: 78, level: '中可信度' },
        relevance_summary: '疫苗研发涉及合成生物学技术应用',
      },
      {
        stock_code: '300601.SZ',
        stock_name: '康泰生物',
        credibility_score: { score: 72, level: '中可信度' },
        relevance_summary: '生物制品研发中应用合成生物学方法',
      },
    ],
    risk_alerts: [
      '行业处于早期阶段，商业化路径不确定',
      '技术迭代快，研发投入大',
      '监管政策存在不确定性',
      '部分概念股存在蹭热点风险',
    ],
    catalysts: [
      '国家政策支持生物经济发展',
      '技术突破带来成本下降',
      '下游应用场景持续拓展',
      '头部企业产品获批上市',
    ],
    heat_score: 75,
    competitive_landscape: '行业集中度较低，竞争格局分散。国内企业以中小型为主，头部企业正在形成。国际巨头如Ginkgo Bioworks、Zymergen等具有先发优势，国内企业在特定细分领域具有竞争力。',
  });

  // 重新开始
  const handleReset = () => {
    setQuery('');
    setTaskStatus(TaskStatus.IDLE);
    setTaskId(null);
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
