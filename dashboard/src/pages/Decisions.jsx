import { useEffect, useState } from 'react'
import {
  Card, Col, Descriptions, Empty, List, Row, Space, Steps, Tag,
  Typography, message,
} from 'antd'
import {
  AimOutlined, DatabaseOutlined, FileTextOutlined, SmileOutlined,
} from '@ant-design/icons'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { fmtScore } from '../theme.js'
import SentimentTag from '../components/SentimentTag.jsx'

const { Text, Paragraph } = Typography

export default function Decisions() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [decisions, setDecisions] = useState([])
  const [trace, setTrace] = useState(null)

  useEffect(() => {
    api.recentDecisions(50).then((ds) => {
      setDecisions(ds)
      if (!id && ds.length) navigate(`/decisions/${ds[0].id}`, { replace: true })
    }).catch((e) => message.error(String(e)))
  }, [])

  useEffect(() => {
    if (!id) return
    setTrace(null)
    api.decisionTrace(id).then(setTrace).catch((e) => message.error(String(e)))
  }, [id])

  return (
    <Row gutter={16}>
      <Col xs={24} md={8} lg={7}>
        <Card title="Recent decisions" size="small">
          <List
            size="small" dataSource={decisions}
            renderItem={(d) => (
              <List.Item
                key={d.id}
                style={{
                  cursor: 'pointer', borderRadius: 6, padding: '8px 8px',
                  background: String(d.id) === id ? '#e6f4ff' : undefined,
                }}
                onClick={() => navigate(`/decisions/${d.id}`)}
              >
                <Space direction="vertical" size={0} style={{ width: '100%' }}>
                  <Space>
                    <Text strong>#{d.id}</Text>
                    <Tag color={Number(d.impact_score) >= 0 ? 'blue' : 'red'}>
                      <span className="num">{fmtScore(d.impact_score)}</span>
                    </Tag>
                    <Text type="secondary">{d.entity}</Text>
                  </Space>
                  <Text type="secondary" ellipsis style={{ fontSize: 12 }}>
                    {d.headline}
                  </Text>
                </Space>
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col xs={24} md={16} lg={17}>
        {!trace ? <Card><Empty description="Select a decision" /></Card> : (
          <Card
            title={`Reasoning trace — decision #${trace.id}`}
            extra={<Text type="secondary">{new Date(trace.created_at).toLocaleString()}</Text>}
          >
            <Steps
              direction="vertical"
              current={3}
              items={[
                {
                  title: 'News item',
                  icon: <FileTextOutlined />,
                  description: (
                    <>
                      <Paragraph strong style={{ marginBottom: 4 }}>
                        {trace.headline}
                      </Paragraph>
                      <Space wrap>
                        <Tag>{trace.source}</Tag>
                        <Text type="secondary">
                          {new Date(trace.published_at).toLocaleString()}
                        </Text>
                        <Tag color="blue">{trace.entity}</Tag>
                      </Space>
                      {trace.raw_summary && (
                        <Paragraph type="secondary" style={{ marginTop: 6 }}>
                          {trace.raw_summary}
                        </Paragraph>
                      )}
                    </>
                  ),
                },
                {
                  title: 'Sentiment analysis',
                  icon: <SmileOutlined />,
                  description: (
                    <Space wrap>
                      <SentimentTag
                        label={trace.sentiment_label} value={trace.sentiment}
                      />
                      {trace.sentiment_model && (
                        <Text type="secondary">model: {trace.sentiment_model}</Text>
                      )}
                    </Space>
                  ),
                },
                {
                  title: `Retrieved historical cases (${trace.retrieved_cases.length})`,
                  icon: <DatabaseOutlined />,
                  description: (
                    <List
                      size="small" dataSource={trace.retrieved_cases}
                      renderItem={(c) => (
                        <List.Item key={c.id} style={{ paddingLeft: 0 }}>
                          <Space direction="vertical" size={0}>
                            <Space>
                              <Text strong>{c.title}</Text>
                              <Tag>{c.entity_type}</Tag>
                            </Space>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {c.market_impact}
                            </Text>
                          </Space>
                        </List.Item>
                      )}
                    />
                  ),
                },
                {
                  title: 'Impact assessment',
                  icon: <AimOutlined />,
                  description: (
                    <>
                      <Descriptions size="small" column={3} style={{ maxWidth: 480 }}>
                        <Descriptions.Item label="Impact">
                          <Text strong className="num">
                            {fmtScore(trace.impact_score)}
                          </Text>
                        </Descriptions.Item>
                        <Descriptions.Item label="Confidence">
                          <Text strong className="num">
                            {Number(trace.confidence).toFixed(2)}
                          </Text>
                        </Descriptions.Item>
                        <Descriptions.Item label="Evaluated">
                          {trace.accuracy_flag == null ? 'pending'
                            : trace.accuracy_flag ? '✓ correct' : '✗ wrong'}
                        </Descriptions.Item>
                      </Descriptions>
                      <Paragraph style={{
                        background: '#f9f9f7', borderRadius: 6, padding: 12,
                        marginTop: 8, marginBottom: 0,
                      }}>
                        {trace.reasoning}
                      </Paragraph>
                    </>
                  ),
                },
              ]}
            />
          </Card>
        )}
      </Col>
    </Row>
  )
}
