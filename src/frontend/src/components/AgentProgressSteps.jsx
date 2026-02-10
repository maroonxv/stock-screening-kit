import { Steps, Tag } from 'antd';
import {
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  MinusCircleOutlined,
} from '@ant-design/icons';

/**
 * Agent 执行进度展示组件
 * 显示 5 个 Agent 的执行状态：行业背景速览、市场热度分析、标的快速筛选、真实性批量验证、竞争格局速览
 * 
 * @param {Array} agentSteps - Agent 步骤数组，每个元素包含 agent_name, status, output_summary, error_message
 */

// 5 个 Agent 的定义
const AGENTS = [
  { name: '行业背景速览', description: '分析行业概况、产业链结构、技术路线' },
  { name: '市场热度分析', description: '评估市场关注度、新闻热度、资金流向' },
  { name: '标的快速筛选', description: '筛选行业相关核心标的' },
  { name: '真实性批量验证', description: '验证标的与行业的真实关联度' },
  { name: '竞争格局速览', description: '分析行业竞争格局和主要玩家' },
];

// 状态映射
const STATUS_CONFIG = {
  pending: {
    status: 'wait',
    icon: <ClockCircleOutlined />,
    color: 'default',
    text: '等待中',
  },
  running: {
    status: 'process',
    icon: <LoadingOutlined spin />,
    color: 'processing',
    text: '执行中',
  },
  completed: {
    status: 'finish',
    icon: <CheckCircleOutlined />,
    color: 'success',
    text: '已完成',
  },
  failed: {
    status: 'error',
    icon: <CloseCircleOutlined />,
    color: 'error',
    text: '失败',
  },
  skipped: {
    status: 'wait',
    icon: <MinusCircleOutlined />,
    color: 'warning',
    text: '跳过',
  },
};

function AgentProgressSteps({ agentSteps = [] }) {
  // 将 agentSteps 数组转换为以 agent_name 为 key 的 Map
  const stepMap = new Map();
  agentSteps.forEach((step) => {
    stepMap.set(step.agent_name, step);
  });

  // 计算当前执行到哪个 Agent
  const getCurrentStep = () => {
    for (let i = 0; i < AGENTS.length; i++) {
      const step = stepMap.get(AGENTS[i].name);
      if (!step || step.status === 'pending' || step.status === 'running') {
        return i;
      }
    }
    return AGENTS.length; // 全部完成
  };

  const currentStep = getCurrentStep();

  // 构建 Steps 的 items
  const items = AGENTS.map((agent) => {
    const step = stepMap.get(agent.name);
    const status = step?.status || 'pending';
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending;

    return {
      title: (
        <span>
          {agent.name}
          <Tag color={config.color} style={{ marginLeft: 8 }}>
            {config.text}
          </Tag>
        </span>
      ),
      description: (
        <div>
          <div style={{ color: '#666', fontSize: 12 }}>{agent.description}</div>
          {step?.output_summary && (
            <div style={{ color: '#1890ff', fontSize: 12, marginTop: 4 }}>
              {step.output_summary}
            </div>
          )}
          {step?.error_message && (
            <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 4 }}>
              错误: {step.error_message}
            </div>
          )}
        </div>
      ),
      status: config.status,
      icon: config.icon,
    };
  });

  return (
    <Steps
      direction="vertical"
      current={currentStep}
      items={items}
      style={{ padding: '16px 0' }}
    />
  );
}

export default AgentProgressSteps;
