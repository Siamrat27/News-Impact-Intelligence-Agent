import { Layout, Menu, Typography } from 'antd'
import {
  ThunderboltOutlined, LineChartOutlined,
  BranchesOutlined, TrophyOutlined,
} from '@ant-design/icons'
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import LiveFeed from './pages/LiveFeed.jsx'
import EntityDetail from './pages/EntityDetail.jsx'
import Decisions from './pages/Decisions.jsx'
import Backtest from './pages/Backtest.jsx'

const { Sider, Content, Footer } = Layout

const MENU = [
  { key: '/feed', icon: <ThunderboltOutlined />, label: 'Live Feed' },
  { key: '/entities', icon: <LineChartOutlined />, label: 'Entity Detail' },
  { key: '/decisions', icon: <BranchesOutlined />, label: 'Reasoning Trace' },
  { key: '/backtest', icon: <TrophyOutlined />, label: 'Backtest' },
]

const DISCLAIMER = 'Educational demo — not investment advice.'

export default function App() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const selected = MENU.find((m) => pathname.startsWith(m.key))?.key ?? '/feed'

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light" width={210}>
        <div style={{ padding: '18px 16px 10px' }}>
          <Typography.Text strong>News Impact</Typography.Text>
          <br />
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            Intelligence Agent
          </Typography.Text>
        </div>
        <Menu
          mode="inline"
          items={MENU}
          selectedKeys={[selected]}
          onClick={({ key }) => navigate(key)}
          style={{ borderInlineEnd: 'none' }}
        />
      </Sider>
      <Layout>
        <div
          style={{
            background: '#fffbe6', borderBottom: '1px solid #ffe58f',
            padding: '6px 24px', fontSize: 13, color: '#52514e',
          }}
        >
          ⚠️ {DISCLAIMER}
        </div>
        <Content style={{ padding: 24 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/feed" replace />} />
            <Route path="/feed" element={<LiveFeed />} />
            <Route path="/entities" element={<EntityDetail />} />
            <Route path="/decisions" element={<Decisions />} />
            <Route path="/decisions/:id" element={<Decisions />} />
            <Route path="/backtest" element={<Backtest />} />
          </Routes>
        </Content>
        <Footer style={{ textAlign: 'center', color: '#898781', fontSize: 12 }}>
          {DISCLAIMER} · Built with LangGraph + pgvector RAG + FastAPI
        </Footer>
      </Layout>
    </Layout>
  )
}
