import { Table, Tag, Tooltip } from 'antd';

function ScoredStockTable({ stocks }) {
  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 70,
      align: 'center',
      render: (_, __, index) => index + 1,
    },
    {
      title: '股票代码',
      dataIndex: 'stock_code',
      key: 'stock_code',
      width: 120,
    },
    {
      title: '股票名称',
      dataIndex: 'stock_name',
      key: 'stock_name',
      width: 120,
    },
    {
      title: '综合评分',
      dataIndex: 'score',
      key: 'score',
      width: 120,
      align: 'right',
      sorter: (a, b) => a.score - b.score,
      defaultSortOrder: 'descend',
      render: (score) => (
        <span style={{ fontWeight: 'bold', color: '#1890ff' }}>
          {score != null ? score.toFixed(2) : '-'}
        </span>
      ),
    },
    {
      title: '评分明细',
      dataIndex: 'score_breakdown',
      key: 'score_breakdown',
      render: (breakdown) => {
        if (!breakdown || Object.keys(breakdown).length === 0) {
          return '-';
        }
        const entries = Object.entries(breakdown);
        return (
          <Tooltip
            title={
              <div>
                {entries.map(([field, value]) => (
                  <div key={field}>
                    {field}: {typeof value === 'number' ? value.toFixed(4) : value}
                  </div>
                ))}
              </div>
            }
          >
            <span>
              {entries.slice(0, 3).map(([field, value]) => (
                <Tag key={field} color="blue">
                  {field}: {typeof value === 'number' ? value.toFixed(2) : value}
                </Tag>
              ))}
              {entries.length > 3 && <Tag>+{entries.length - 3}</Tag>}
            </span>
          </Tooltip>
        );
      },
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={stocks}
      rowKey="stock_code"
      pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
      locale={{ emptyText: '暂无匹配股票' }}
      size="middle"
    />
  );
}

export default ScoredStockTable;
