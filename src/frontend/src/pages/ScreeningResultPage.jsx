import { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Typography, Spin, Table, message, Alert } from 'antd';
import {
  BarChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { screeningApi } from '../services/api';
import ScoredStockTable from '../components/ScoredStockTable';

const { Title } = Typography;

function ScreeningResultPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  if (sessionId) {
    return <SessionDetail sessionId={sessionId} />;
  }
  return <SessionList navigate={navigate} />;
}

function SessionDetail({ sessionId }) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await screeningApi.getSession(sessionId);
      setSession(response.data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0' }}>
        <Spin size="large" tip="加载筛选结果中..." />
      </div>
    );
  }

  if (error) {
    return <Alert type="error" message="加载失败" description={error} showIcon />;
  }

  if (!session) {
    return null;
  }

  const matchRate = session.match_rate != null
    ? (session.match_rate * 100).toFixed(2) + '%'
    : '-';

  return (
    <div>
      <Title level={2}>筛选结果 - {session.strategy_name}</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="策略名称"
              value={session.strategy_name}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="扫描总数"
              value={session.total_scanned}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="匹配数量 / 匹配率"
              value={session.matched_count}
              suffix={`/ ${matchRate}`}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="执行时间"
              value={session.execution_time != null ? session.execution_time.toFixed(2) : '-'}
              suffix="秒"
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title="匹配股票排名" style={{ marginBottom: 24 }}>
        <ScoredStockTable stocks={session.top_stocks || []} />
      </Card>
    </div>
  );
}

function SessionList({ navigate }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await screeningApi.getSessions();
      setSessions(response.data.sessions || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  const columns = [
    {
      title: '策略名称',
      dataIndex: 'strategy_name',
      key: 'strategy_name',
      width: 180,
    },
    {
      title: '执行时间',
      dataIndex: 'executed_at',
      key: 'executed_at',
      width: 180,
      render: (text) => {
        if (!text) return '-';
        return new Date(text).toLocaleString('zh-CN');
      },
    },
    {
      title: '扫描总数',
      dataIndex: 'total_scanned',
      key: 'total_scanned',
      width: 100,
      align: 'right',
    },
    {
      title: '匹配数量',
      dataIndex: 'matched_count',
      key: 'matched_count',
      width: 100,
      align: 'right',
    },
    {
      title: '匹配率',
      dataIndex: 'match_rate',
      key: 'match_rate',
      width: 100,
      align: 'right',
      render: (rate) => (rate != null ? (rate * 100).toFixed(2) + '%' : '-'),
    },
    {
      title: '耗时(秒)',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 100,
      align: 'right',
      render: (time) => (time != null ? time.toFixed(2) : '-'),
    },
  ];

  if (error) {
    return (
      <div>
        <Title level={2}>筛选历史</Title>
        <Alert type="error" message="加载失败" description={error} showIcon />
      </div>
    );
  }

  return (
    <div>
      <Title level={2}>筛选历史</Title>
      <Table
        columns={columns}
        dataSource={sessions}
        rowKey="session_id"
        loading={loading}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
        locale={{ emptyText: '暂无筛选记录' }}
        onRow={(record) => ({
          onClick: () => navigate(`/results/${record.session_id}`),
          style: { cursor: 'pointer' },
        })}
      />
    </div>
  );
}

export default ScreeningResultPage;
