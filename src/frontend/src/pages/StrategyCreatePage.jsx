import { useState } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  InputNumber,
  Card,
  Typography,
  Space,
  message,
  Divider,
} from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { screeningApi } from '../services/api';
import FilterConditionBuilder from '../components/FilterConditionBuilder';

const { Title } = Typography;
const { TextArea } = Input;

const WEIGHT_FIELDS = [
  { value: 'ROE', label: 'ROE (净资产收益率)' },
  { value: 'PE', label: 'PE (市盈率)' },
  { value: 'PB', label: 'PB (市净率)' },
  { value: 'EPS', label: 'EPS (每股收益)' },
  { value: 'REVENUE', label: '营业收入' },
  { value: 'NET_PROFIT', label: '净利润' },
  { value: 'DEBT_RATIO', label: '资产负债率' },
  { value: 'MARKET_CAP', label: '总市值' },
  { value: 'DIVIDEND_YIELD', label: '股息率' },
  { value: 'ROE_CONTINUOUS_GROWTH_YEARS', label: 'ROE连续增长年数' },
  { value: 'REVENUE_CAGR_3Y', label: '营收3年复合增长率' },
  { value: 'NET_PROFIT_CAGR_3Y', label: '净利润3年复合增长率' },
  { value: 'PE_PB_RATIO', label: 'PE/PB比值' },
  { value: 'PEG', label: 'PEG' },
];

const NORMALIZATION_METHODS = [
  { value: 'min_max', label: 'Min-Max 归一化' },
];

function buildFilterValue(condition) {
  const textFields = ['INDUSTRY'];
  if (textFields.includes(condition.field)) {
    return { type: 'text', value: condition.value };
  }
  return { type: 'numeric', value: Number(condition.value) };
}

function StrategyCreatePage() {
  const [form] = Form.useForm();
  const [conditions, setConditions] = useState([]);
  const [weights, setWeights] = useState([{ field: 'ROE', weight: 1.0 }]);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleAddWeight = () => {
    // Find a field not already used
    const usedFields = weights.map((w) => w.field);
    const available = WEIGHT_FIELDS.find((f) => !usedFields.includes(f.value));
    if (!available) {
      message.warning('所有指标字段已添加');
      return;
    }
    setWeights([...weights, { field: available.value, weight: 0 }]);
  };

  const handleRemoveWeight = (index) => {
    if (weights.length <= 1) {
      message.warning('至少需要一个评分权重');
      return;
    }
    setWeights(weights.filter((_, i) => i !== index));
  };

  const handleWeightChange = (index, key, val) => {
    setWeights(
      weights.map((w, i) => (i === index ? { ...w, [key]: val } : w))
    );
  };

  const handleSubmit = async (values) => {
    if (conditions.length === 0) {
      message.error('请至少添加一个筛选条件');
      return;
    }

    // Build weights map
    const weightsMap = {};
    for (const w of weights) {
      weightsMap[w.field] = w.weight;
    }

    // Build filters
    const filters = {
      group_id: crypto.randomUUID(),
      operator: 'AND',
      conditions: conditions.map((c) => ({
        field: c.field,
        operator: c.operator,
        value: buildFilterValue(c),
      })),
      sub_groups: [],
    };

    const data = {
      name: values.name,
      description: values.description || '',
      tags: values.tags || [],
      filters,
      scoring_config: {
        weights: weightsMap,
        normalization_method: values.normalization_method || 'min_max',
      },
    };

    setSubmitting(true);
    try {
      await screeningApi.createStrategy(data);
      message.success('策略创建成功');
      navigate('/strategies');
    } catch (err) {
      const errMsg =
        err.response?.data?.error || err.message || '创建策略失败';
      message.error(errMsg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <Title level={2}>创建策略</Title>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          normalization_method: 'min_max',
        }}
        style={{ maxWidth: 800 }}
      >
        <Form.Item
          label="策略名称"
          name="name"
          rules={[{ required: true, message: '请输入策略名称' }]}
        >
          <Input placeholder="请输入策略名称" />
        </Form.Item>

        <Form.Item label="描述" name="description">
          <TextArea rows={3} placeholder="请输入策略描述（可选）" />
        </Form.Item>

        <Form.Item label="标签" name="tags">
          <Select
            mode="tags"
            placeholder="输入标签后按回车添加"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Divider />

        <FilterConditionBuilder value={conditions} onChange={setConditions} />

        <Divider />

        <Card size="small" title="评分权重" style={{ marginBottom: 16 }}>
          {weights.map((w, index) => {
            const usedFields = weights
              .filter((_, i) => i !== index)
              .map((item) => item.field);
            const availableOptions = WEIGHT_FIELDS.filter(
              (f) => !usedFields.includes(f.value) || f.value === w.field
            );
            return (
              <Space
                key={index}
                style={{ display: 'flex', marginBottom: 8 }}
                align="center"
              >
                <Select
                  style={{ width: 220 }}
                  value={w.field}
                  onChange={(val) => handleWeightChange(index, 'field', val)}
                  options={availableOptions}
                  placeholder="选择指标"
                />
                <InputNumber
                  style={{ width: 120 }}
                  value={w.weight}
                  onChange={(val) => handleWeightChange(index, 'weight', val)}
                  min={0}
                  max={1}
                  step={0.1}
                  placeholder="权重"
                />
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleRemoveWeight(index)}
                  disabled={weights.length <= 1}
                />
              </Space>
            );
          })}
          <Button
            type="dashed"
            onClick={handleAddWeight}
            icon={<PlusOutlined />}
            style={{ width: '100%' }}
          >
            添加权重
          </Button>
        </Card>

        <Form.Item label="归一化方法" name="normalization_method">
          <Select
            style={{ width: 220 }}
            options={NORMALIZATION_METHODS}
            placeholder="选择归一化方法"
          />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>
              创建策略
            </Button>
            <Button onClick={() => navigate('/strategies')}>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </div>
  );
}

export default StrategyCreatePage;
