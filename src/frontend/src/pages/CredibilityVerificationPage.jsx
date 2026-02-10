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
  Tag,
  Descriptions,
  Space,
  Empty,
  Form,
  message,
  Divider,
} from 'antd';
import {
  SafetyCertificateOutlined,
  SearchOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
  HistoryOutlined,
  NodeIndexOutlined,
} from '@ant-design/icons';
import AgentProgressSteps from '../components/AgentProgressSteps';

const { Title, Text, Paragraph } = Typography;

/**
 * 概念可信度验证页面
 * 
 * 功能：
 * 1. 股票代码 + 概念输入
 * 2. 可信度评分仪表盘
 * 3. 各维度分析详情展示（主营业务匹配度、实质证据分析、历史蹭热点记录、供应链逻辑）
 * 
 * Requirements: 9.4
 */

// 任务状态枚举
const TaskStatus = {
  IDLE: 'idle',           // 空闲，等待用户输入
  PENDING: 'pending',     // 任务已创建，等待执行
  RUNNING: 'running',     // 任务执行中
  COMPLETED: 'completed', // 任务完成
  FAILED: 'failed',       // 任务失败
};

// A股代码格式验证正则：600519.SH 或 000001.SZ
const STOCK_CODE_REGEX = /^\d{6}\.(SH|SZ)$/i;

// 可信度验证的 Agent 定义
const CREDIBILITY_AGENTS = [
  { name: '主营业务分析', description: '分析公司主营业务与概念的匹配度' },
  { name: '证据收集', description: '收集专利、订单、合作伙伴等实质证据' },
  { name: '历史蹭热点检测', description: '检测公司历史上蹭热点的记录' },
  { name: '供应链逻辑验证', description: '验证供应链上下游与概念的逻辑关联' },
];

function CredibilityVerificationPage() {
  const [form] = Form.useForm();
  
  // 状态管理
  const [taskStatus, setTaskStatus] = useState(TaskStatus.IDLE);
  const [, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [agentSteps, setAgentSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // 验证股票代码格式
  const validateStockCode = (_, value) => {
    if (!value) {
      return Promise.reject(new Error('请输入股票代码'));
    }
    if (!STOCK_CODE_REGEX.test(value)) {
      return Promise.reject(new Error('股票代码格式错误，请输入如 600519.SH 或 000001.SZ'));
    }
    return Promise.resolve();
  };

  // 模拟任务执行进度（临时实现，实际将通过 WebSocket 接收）
  const simulateTaskProgress = useCallback(() => {
    let currentIndex = 0;
    const steps = [];

    const runNextAgent = () => {
      if (currentIndex >= CREDIBILITY_AGENTS.length) {
        // 所有 Agent 完成，生成模拟结果
        setProgress(100);
        setResult(getMockResult(form.getFieldValue('stockCode'), form.getFieldValue('concept')));
        setTaskStatus(TaskStatus.COMPLETED);
        return;
      }

      const agentName = CREDIBILITY_AGENTS[currentIndex].name;
      
      // 设置当前 Agent 为 running
      steps.push({
        agent_name: agentName,
        status: 'running',
        started_at: new Date().toISOString(),
      });
      setAgentSteps([...steps]);
      setProgress(Math.round((currentIndex / CREDIBILITY_AGENTS.length) * 100));

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
  }, [form]);

  // 提交验证
  const handleSubmit = useCallback(async (values) => {
    const { stockCode, concept } = values;

    // 重置状态
    setTaskStatus(TaskStatus.PENDING);
    setProgress(0);
    setAgentSteps([]);
    setResult(null);
    setError(null);

    try {
      // TODO: 实际 API 调用将在 Task 13.4 中实现
      // const response = await intelligenceApi.createCredibilityVerification({ 
      //   stock_code: stockCode, 
      //   concept 
      // });
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
  }, [simulateTaskProgress]);

  // 模拟结果数据
  const getMockResult = (stockCode, concept) => ({
    stock_code: stockCode || '600519.SH',
    stock_name: '贵州茅台',
    concept: concept || 'AI+白酒',
    overall_score: { score: 15, level: '低可信度' },
    main_business_match: {
      score: 5,
      main_business_description: '白酒生产与销售，主要产品为茅台酒系列',
      match_analysis: '公司主营业务为白酒生产与销售，与 AI 技术无直接关联。虽然公司可能在生产管理中使用信息化系统，但这并不构成 AI 概念的实质性业务。',
    },
    evidence: {
      score: 10,
      patents: [],
      orders: [],
      partnerships: [],
      analysis: '未发现公司在 AI 领域的专利申请、订单或战略合作。公司公告和年报中未提及 AI 相关业务布局。',
    },
    hype_history: {
      score: 30,
      past_concepts: ['元宇宙', '区块链', '大数据'],
      analysis: '公司历史上曾被市场关联过多个热点概念，包括元宇宙、区块链等，但均未有实质性业务落地。存在一定的蹭热点历史。',
    },
    supply_chain_logic: {
      score: 5,
      upstream: ['高粱', '小麦', '包装材料'],
      downstream: ['经销商', '零售终端', '电商平台'],
      analysis: '公司供应链主要涉及农产品原料和消费品销售渠道，与 AI 技术的供应链（芯片、算力、数据）无逻辑关联。',
    },
    risk_labels: ['pure_hype', 'business_mismatch', 'weak_evidence'],
    conclusion: '综合分析显示，该公司声称的 AI+白酒 概念可信度极低。公司主营业务与 AI 无关，未发现实质性证据支持，且存在历史蹭热点记录。投资者应警惕此类概念炒作风险。',
  });

  // 重新开始
  const handleReset = () => {
    form.resetFields();
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
        <SafetyCertificateOutlined style={{ marginRight: 8 }} />
        概念可信度验证
      </Title>
      <Text type="secondary">
        输入股票代码和概念，AI 将从多个维度验证该股票与概念的真实关联度
      </Text>

      {/* 输入表单区域 */}
      <Card style={{ marginTop: 24, marginBottom: 24 }}>
        <Form
          form={form}
          layout="inline"
          onFinish={handleSubmit}
          style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}
        >
          <Form.Item
            name="stockCode"
            rules={[{ validator: validateStockCode }]}
            style={{ marginBottom: 0 }}
          >
            <Input
              placeholder="股票代码，如 600519.SH"
              style={{ width: 200 }}
              disabled={taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING}
            />
          </Form.Item>
          <Form.Item
            name="concept"
            rules={[{ required: true, message: '请输入要验证的概念' }]}
            style={{ marginBottom: 0 }}
          >
            <Input
              placeholder="概念，如 AI+白酒"
              style={{ width: 200 }}
              disabled={taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SearchOutlined />}
              loading={taskStatus === TaskStatus.PENDING}
              disabled={taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING}
            >
              开始验证
            </Button>
          </Form.Item>
        </Form>
        {(taskStatus === TaskStatus.COMPLETED || taskStatus === TaskStatus.FAILED) && (
          <Button
            type="link"
            onClick={handleReset}
            style={{ marginTop: 8, padding: 0 }}
          >
            重新开始
          </Button>
        )}
      </Card>

      {/* 错误提示 */}
      {error && (
        <Alert
          type="error"
          message="验证失败"
          description={error}
          showIcon
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 任务进度展示 */}
      {(taskStatus === TaskStatus.RUNNING || taskStatus === TaskStatus.PENDING) && (
        <Card title="验证进度" style={{ marginBottom: 24 }}>
          <Progress
            percent={progress}
            status={taskStatus === TaskStatus.RUNNING ? 'active' : 'normal'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <CredibilityAgentSteps agentSteps={agentSteps} />
        </Card>
      )}

      {/* 结果展示 */}
      {taskStatus === TaskStatus.COMPLETED && result && (
        <CredibilityReportResult result={result} />
      )}

      {/* 空状态 */}
      {taskStatus === TaskStatus.IDLE && (
        <Card>
          <Empty
            description="输入股票代码和概念开始验证"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </Card>
      )}
    </div>
  );
}

/**
 * 可信度验证 Agent 进度展示组件
 * 复用 AgentProgressSteps 的逻辑，但使用可信度验证的 Agent 定义
 */
function CredibilityAgentSteps({ agentSteps = [] }) {
  // 将 agentSteps 数组转换为以 agent_name 为 key 的 Map
  const stepMap = new Map();
  agentSteps.forEach((step) => {
    stepMap.set(step.agent_name, step);
  });

  // 构建 Steps 的 items
  const items = CREDIBILITY_AGENTS.map((agent) => {
    const step = stepMap.get(agent.name);
    const status = step?.status || 'pending';
    
    return {
      agent_name: agent.name,
      status: status,
      output_summary: step?.output_summary,
      error_message: step?.error_message,
    };
  });

  return <AgentProgressSteps agentSteps={items} />;
}

/**
 * 可信度报告结果展示组件
 */
function CredibilityReportResult({ result }) {
  const overallScore = result.overall_score?.score || 0;
  
  return (
    <div>
      {/* 总体可信度评分仪表盘 */}
      <Card
        title={
          <span>
            <SafetyCertificateOutlined style={{ marginRight: 8 }} />
            {result.stock_name}（{result.stock_code}）- {result.concept} 可信度验证
          </span>
        }
        style={{ marginBottom: 24 }}
      >
        <Row gutter={24} align="middle">
          <Col span={8} style={{ textAlign: 'center' }}>
            <Progress
              type="dashboard"
              percent={overallScore}
              strokeColor={getScoreColor(overallScore)}
              format={(percent) => (
                <div>
                  <div style={{ fontSize: 32, fontWeight: 'bold' }}>{percent}</div>
                  <div style={{ fontSize: 14, color: '#666' }}>可信度评分</div>
                </div>
              )}
              size={180}
            />
            <div style={{ marginTop: 16 }}>
              <Tag 
                color={getScoreLevelColor(result.overall_score?.level)} 
                style={{ fontSize: 16, padding: '4px 16px' }}
              >
                {result.overall_score?.level || '-'}
              </Tag>
            </div>
          </Col>
          <Col span={16}>
            <Title level={5}>风险标签</Title>
            <Space wrap style={{ marginBottom: 16 }}>
              {result.risk_labels?.map((label, index) => (
                <Tag 
                  key={index} 
                  color={getRiskLabelColor(label)}
                  icon={<WarningOutlined />}
                >
                  {getRiskLabelText(label)}
                </Tag>
              ))}
              {(!result.risk_labels || result.risk_labels.length === 0) && (
                <Tag color="success" icon={<CheckCircleOutlined />}>
                  无风险标签
                </Tag>
              )}
            </Space>
            <Divider />
            <Title level={5}>总结</Title>
            <Paragraph>{result.conclusion}</Paragraph>
          </Col>
        </Row>
      </Card>

      {/* 四维度分析详情 */}
      <Row gutter={[24, 24]}>
        {/* 主营业务匹配度 */}
        <Col span={12}>
          <DimensionCard
            title="主营业务匹配度"
            icon={<ApartmentOutlined />}
            score={result.main_business_match?.score}
            content={
              <Descriptions column={1} size="small">
                <Descriptions.Item label="主营业务">
                  {result.main_business_match?.main_business_description}
                </Descriptions.Item>
                <Descriptions.Item label="匹配分析">
                  {result.main_business_match?.match_analysis}
                </Descriptions.Item>
              </Descriptions>
            }
          />
        </Col>

        {/* 实质证据分析 */}
        <Col span={12}>
          <DimensionCard
            title="实质证据分析"
            icon={<FileSearchOutlined />}
            score={result.evidence?.score}
            content={
              <div>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="专利">
                    {result.evidence?.patents?.length > 0 
                      ? result.evidence.patents.join('、') 
                      : <Text type="secondary">无相关专利</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="订单">
                    {result.evidence?.orders?.length > 0 
                      ? result.evidence.orders.join('、') 
                      : <Text type="secondary">无相关订单</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="合作伙伴">
                    {result.evidence?.partnerships?.length > 0 
                      ? result.evidence.partnerships.join('、') 
                      : <Text type="secondary">无相关合作</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="分析">
                    {result.evidence?.analysis}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            }
          />
        </Col>

        {/* 历史蹭热点记录 */}
        <Col span={12}>
          <DimensionCard
            title="历史蹭热点记录"
            icon={<HistoryOutlined />}
            score={result.hype_history?.score}
            scoreLabel="可信度（越高越可信）"
            content={
              <div>
                <div style={{ marginBottom: 12 }}>
                  <Text strong>历史关联概念：</Text>
                  <div style={{ marginTop: 8 }}>
                    {result.hype_history?.past_concepts?.length > 0 ? (
                      <Space wrap>
                        {result.hype_history.past_concepts.map((concept, index) => (
                          <Tag key={index} color="orange">{concept}</Tag>
                        ))}
                      </Space>
                    ) : (
                      <Tag color="success">无蹭热点历史</Tag>
                    )}
                  </div>
                </div>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="分析">
                    {result.hype_history?.analysis}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            }
          />
        </Col>

        {/* 供应链逻辑 */}
        <Col span={12}>
          <DimensionCard
            title="供应链逻辑"
            icon={<NodeIndexOutlined />}
            score={result.supply_chain_logic?.score}
            content={
              <div>
                <Row gutter={16} style={{ marginBottom: 12 }}>
                  <Col span={12}>
                    <Text strong>上游：</Text>
                    <div style={{ marginTop: 4 }}>
                      {result.supply_chain_logic?.upstream?.map((item, index) => (
                        <Tag key={index} style={{ marginBottom: 4 }}>{item}</Tag>
                      ))}
                    </div>
                  </Col>
                  <Col span={12}>
                    <Text strong>下游：</Text>
                    <div style={{ marginTop: 4 }}>
                      {result.supply_chain_logic?.downstream?.map((item, index) => (
                        <Tag key={index} style={{ marginBottom: 4 }}>{item}</Tag>
                      ))}
                    </div>
                  </Col>
                </Row>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="分析">
                    {result.supply_chain_logic?.analysis}
                  </Descriptions.Item>
                </Descriptions>
              </div>
            }
          />
        </Col>
      </Row>
    </div>
  );
}

/**
 * 维度分析卡片组件
 */
function DimensionCard({ title, icon, score, scoreLabel = '评分', content }) {
  return (
    <Card
      title={
        <span>
          {icon && <span style={{ marginRight: 8 }}>{icon}</span>}
          {title}
        </span>
      }
      extra={
        <Space>
          <Text type="secondary">{scoreLabel}：</Text>
          <Progress
            type="circle"
            percent={score || 0}
            size={50}
            strokeColor={getScoreColor(score)}
            format={(percent) => percent}
          />
        </Space>
      }
      style={{ height: '100%' }}
    >
      {content}
    </Card>
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

// 风险标签映射
const RISK_LABEL_MAP = {
  pure_hype: { text: '纯蹭热点', color: 'error' },
  weak_evidence: { text: '证据不足', color: 'warning' },
  business_mismatch: { text: '主业不匹配', color: 'error' },
  high_debt: { text: '高负债风险', color: 'warning' },
  frequent_concept_change: { text: '频繁概念切换', color: 'orange' },
  supply_chain_risk: { text: '供应链风险', color: 'warning' },
};

function getRiskLabelText(label) {
  return RISK_LABEL_MAP[label]?.text || label;
}

function getRiskLabelColor(label) {
  return RISK_LABEL_MAP[label]?.color || 'default';
}

export default CredibilityVerificationPage;
