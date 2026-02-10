import { Layout, Menu } from 'antd';
import {
  UnorderedListOutlined,
  PlusSquareOutlined,
  BarChartOutlined,
  RocketOutlined,
  SafetyCertificateOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const { Sider, Content, Header } = Layout;

const menuItems = [
  {
    key: '/strategies',
    icon: <UnorderedListOutlined />,
    label: '策略列表',
  },
  {
    key: '/strategies/create',
    icon: <PlusSquareOutlined />,
    label: '创建策略',
  },
  {
    key: '/results',
    icon: <BarChartOutlined />,
    label: '筛选结果',
  },
  {
    key: '/intelligence/industry-research',
    icon: <RocketOutlined />,
    label: '快速行业认知',
  },
  {
    key: '/intelligence/credibility-verification',
    icon: <SafetyCertificateOutlined />,
    label: '概念可信度验证',
  },
  {
    key: '/intelligence/task-history',
    icon: <HistoryOutlined />,
    label: '调研任务历史',
  },
];

function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = menuItems
    .map((item) => item.key)
    .filter((key) => location.pathname.startsWith(key))
    .sort((a, b) => b.length - a.length)[0] || '/strategies';

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme="dark">
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: 18,
            fontWeight: 'bold',
          }}
        >
          投研平台
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            fontSize: 16,
            fontWeight: 'bold',
          }}
        >
          股票筛选系统
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: '#fff',
            borderRadius: 8,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}

export default MainLayout;
