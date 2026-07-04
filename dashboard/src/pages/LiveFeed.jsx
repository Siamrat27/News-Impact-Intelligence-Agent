import { useEffect, useState } from 'react'
import { Alert, Button, Card, Space, Table, Tag, Typography, message } from 'antd'
import { PlayCircleOutlined, FireOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import SentimentTag from '../components/SentimentTag.jsx'

export default function LiveFeed() {
  const [items, setItems] = useState([])
  const [spikes, setSpikes] = useState([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  const load = (p = page) => {
    setLoading(true)
    Promise.all([api.recentNews(p, 25), api.spikes()])
      .then(([news, sp]) => {
        setItems(news.items)
        setSpikes(sp.filter((s) => s.is_spike))
      })
      .catch((e) => message.error(String(e)))
      .finally(() => setLoading(false))
  }
  useEffect(() => { load(page) }, [page])

  const runAgent = async () => {
    setRunning(true)
    try {
      const res = await api.runAgent()
      if (res.ran) {
        message.success(`Agent decision #${res.decision_id} created`)
        load()
      } else {
        message.info(res.detail)
      }
    } catch (e) {
      message.error(String(e))
    } finally {
      setRunning(false)
    }
  }

  const columns = [
    {
      title: 'Published', dataIndex: 'published_at', width: 170,
      className: 'num',
      render: (v) => new Date(v).toLocaleString(),
    },
    { title: 'Headline', dataIndex: 'headline', ellipsis: true },
    {
      title: 'Source', dataIndex: 'source', width: 130,
      render: (v) => <Tag>{v}</Tag>,
    },
    {
      title: 'Sentiment', width: 160,
      render: (_, r) => <SentimentTag label={r.sentiment_label} value={r.sentiment} />,
    },
  ]

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      {spikes.length > 0 && (
        <Alert
          type="warning" showIcon icon={<FireOutlined />}
          message={
            <>
              Volume spike detected:{' '}
              {spikes.map((s) => (
                <Tag key={s.entity_id} color="orange">
                  <Link to="/entities">{s.name}</Link>
                  <span className="num"> {Number(s.ratio).toFixed(1)}×</span>
                </Tag>
              ))}
            </>
          }
        />
      )}
      <Card
        title="Live Feed"
        extra={
          <Button
            type="primary" icon={<PlayCircleOutlined />}
            loading={running} onClick={runAgent}
          >
            Run agent cycle
          </Button>
        }
      >
        <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
          Incoming news with model-scored sentiment. “synthetic” rows are
          generated development data.
        </Typography.Paragraph>
        <Table
          size="small" rowKey="id" columns={columns} dataSource={items}
          loading={loading}
          pagination={{ current: page, pageSize: 25, total: 5000, showSizeChanger: false }}
          onChange={(p) => setPage(p.current)}
        />
      </Card>
    </Space>
  )
}
