import { useState } from 'react';
import { Select, InputNumber, Input, Button, Space, Card } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const INDICATOR_FIELDS = [
  { value: 'ROE', label: 'ROE (净资产收益率)', type: 'numeric' },
  { value: 'PE', label: 'PE (市盈率)', type: 'numeric' },
  { value: 'PB', label: 'PB (市净率)', type: 'numeric' },
  { value: 'EPS', label: 'EPS (每股收益)', type: 'numeric' },
  { value: 'REVENUE', label: '营业收入', type: 'numeric' },
  { value: 'NET_PROFIT', label: '净利润', type: 'numeric' },
  { value: 'DEBT_RATIO', label: '资产负债率', type: 'numeric' },
  { value: 'MARKET_CAP', label: '总市值', type: 'numeric' },
  { value: 'DIVIDEND_YIELD', label: '股息率', type: 'numeric' },
  { value: 'INDUSTRY', label: '行业', type: 'text' },
  { value: 'ROE_CONTINUOUS_GROWTH_YEARS', label: 'ROE连续增长年数', type: 'numeric' },
  { value: 'REVENUE_CAGR_3Y', label: '营收3年复合增长率', type: 'numeric' },
  { value: 'NET_PROFIT_CAGR_3Y', label: '净利润3年复合增长率', type: 'numeric' },
  { value: 'PE_PB_RATIO', label: 'PE/PB比值', type: 'numeric' },
  { value: 'PEG', label: 'PEG', type: 'numeric' },
];

const NUMERIC_OPERATORS = [
  { value: '>', label: '大于 (>)' },
  { value: '<', label: '小于 (<)' },
  { value: '=', label: '等于 (=)' },
  { value: '>=', label: '大于等于 (>=)' },
  { value: '<=', label: '小于等于 (<=)' },
  { value: '!=', label: '不等于 (!=)' },
];

const TEXT_OPERATORS = [
  { value: '=', label: '等于 (=)' },
  { value: '!=', label: '不等于 (!=)' },
];

function getFieldType(fieldValue) {
  const field = INDICATOR_FIELDS.find((f) => f.value === fieldValue);
  return field ? field.type : 'numeric';
}

function getOperatorsForField(fieldValue) {
  const type = getFieldType(fieldValue);
  return type === 'text' ? TEXT_OPERATORS : NUMERIC_OPERATORS;
}

function FilterConditionBuilder({ value = [], onChange }) {
  const handleAddCondition = () => {
    const newCondition = {
      field: 'ROE',
      operator: '>',
      value: 0,
    };
    onChange([...value, newCondition]);
  };

  const handleRemoveCondition = (index) => {
    const updated = value.filter((_, i) => i !== index);
    onChange(updated);
  };

  const handleConditionChange = (index, key, newVal) => {
    const updated = value.map((cond, i) => {
      if (i !== index) return cond;
      const updatedCond = { ...cond, [key]: newVal };
      // Reset operator and value when field changes
      if (key === 'field') {
        const type = getFieldType(newVal);
        const operators = type === 'text' ? TEXT_OPERATORS : NUMERIC_OPERATORS;
        updatedCond.operator = operators[0].value;
        updatedCond.value = type === 'text' ? '' : 0;
      }
      return updatedCond;
    });
    onChange(updated);
  };

  return (
    <Card size="small" title="筛选条件" style={{ marginBottom: 16 }}>
      {value.map((condition, index) => {
        const fieldType = getFieldType(condition.field);
        const operators = getOperatorsForField(condition.field);
        return (
          <Space
            key={index}
            style={{ display: 'flex', marginBottom: 8 }}
            align="center"
            wrap
          >
            <Select
              style={{ width: 200 }}
              value={condition.field}
              onChange={(val) => handleConditionChange(index, 'field', val)}
              options={INDICATOR_FIELDS}
              placeholder="选择指标"
            />
            <Select
              style={{ width: 140 }}
              value={condition.operator}
              onChange={(val) => handleConditionChange(index, 'operator', val)}
              options={operators}
              placeholder="选择运算符"
            />
            {fieldType === 'text' ? (
              <Input
                style={{ width: 160 }}
                value={condition.value}
                onChange={(e) =>
                  handleConditionChange(index, 'value', e.target.value)
                }
                placeholder="输入值"
              />
            ) : (
              <InputNumber
                style={{ width: 160 }}
                value={condition.value}
                onChange={(val) => handleConditionChange(index, 'value', val)}
                placeholder="输入数值"
                step={0.01}
              />
            )}
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleRemoveCondition(index)}
            />
          </Space>
        );
      })}
      <Button
        type="dashed"
        onClick={handleAddCondition}
        icon={<PlusOutlined />}
        style={{ width: '100%' }}
      >
        添加条件
      </Button>
    </Card>
  );
}

export default FilterConditionBuilder;
