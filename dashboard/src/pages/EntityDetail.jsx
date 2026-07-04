import { useEffect, useMemo, useState } from 'react'
import { Card, Empty, List, Select, Space, Tag, Typography, message } from 'antd'
import { Link } from 'react-router-dom'
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { api } from '../api.js'
import { viz, fmtScore } from '../theme.js'

const fmtTime = (t) =>
  new Date(t).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

// keep the line chart responsive: thin dense series to ~400 points
const thin = (arr, cap = 400) => {
  if (arr.length <= cap) return arr
  const step = Math.ceil(arr.length / cap)
  return arr.filter((_, i) => i % step === 0)
}

export default function EntityDetail() {
  const [entities, setEntities] = useState([])
  const [entityId, setEntityId] = useState(null)
  const [trend, setTrend] = useState(null)
  const [decisions, setDecisions] = useState([])

  useEffect(() => {
    api.entities().then((es) => {
      setEntities(es)
      if (es.length && !entityId) setEntityId(es[0].id)
    }).catch((e) => message.error(String(e)))
    api.recentDecisions(100).then(setDecisions).catch(() => {})
  }, [])

  useEffect(() => {
    if (!entityId) return
    setTrend(null)
    api.entityTrend(entityId).then(setTrend)
      .catch((e) => { message.error(String(e)); setTrend({ sentiment: [], volume: [] }) })
  }, [entityId])

  const sentimentData = useMemo(() => thin(
    (trend?.sentiment ?? []).map((r) => ({
      t: new Date(r.published_at).getTime(),
      avg24: Number(r.avg_24h),
      avg7d: Number(r.avg_7d),
    }))), [trend])

  const volumeData = useMemo(() =>
    (trend?.volume ?? []).map((r) => ({
      t: new Date(r.bucket).getTime(),
      items: Number(r.items),
    })), [trend])

  const entityName = entities.find((e) => e.id === entityId)?.name
  const entityDecisions = decisions.filter((d) => d.entity === entityName)

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Card
        title="Entity Detail"
        extra={
          <Select
            style={{ width: 240 }} value={entityId} onChange={setEntityId}
            options={entities.map((e) => ({
              value: e.id,
              label: `${e.name} (${e.news_count} items)`,
            }))}
            showSearch optionFilterProp="label"
          />
        }
      >
        <Typography.Title level={5} style={{ marginTop: 0 }}>
          Rolling sentiment — last 7 days
        </Typography.Title>
        {sentimentData.length === 0 ? <Empty /> : (
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={sentimentData} style={{ background: viz.surface }}>
              <CartesianGrid stroke={viz.grid} vertical={false} />
              <XAxis
                dataKey="t" type="number" domain={['auto', 'auto']}
                tickFormatter={fmtTime} stroke={viz.baseline}
                tick={{ fill: viz.muted, fontSize: 12 }}
              />
              <YAxis
                domain={[-1, 1]} stroke={viz.baseline}
                tick={{ fill: viz.muted, fontSize: 12 }} width={40}
              />
              <Tooltip
                labelFormatter={(t) => new Date(t).toLocaleString()}
                formatter={(v, name) => [Number(v).toFixed(3), name]}
              />
              <Legend />
              <Line
                name="24h avg" dataKey="avg24" stroke={viz.series1}
                strokeWidth={2} dot={false} activeDot={{ r: 4 }}
              />
              <Line
                name="7d avg" dataKey="avg7d" stroke={viz.series2}
                strokeWidth={2} dot={false} activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        <Typography.Title level={5}>News volume — 6h buckets</Typography.Title>
        {volumeData.length === 0 ? <Empty /> : (
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={volumeData} style={{ background: viz.surface }}>
              <CartesianGrid stroke={viz.grid} vertical={false} />
              <XAxis
                dataKey="t" type="number" domain={['auto', 'auto']}
                tickFormatter={fmtTime} stroke={viz.baseline}
                tick={{ fill: viz.muted, fontSize: 12 }}
              />
              <YAxis
                allowDecimals={false} stroke={viz.baseline}
                tick={{ fill: viz.muted, fontSize: 12 }} width={40}
              />
              <Tooltip
                labelFormatter={(t) => new Date(t).toLocaleString()}
                formatter={(v) => [v, 'items']}
              />
              <Bar dataKey="items" fill={viz.series1} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>

      <Card title={`Agent decisions — ${entityName ?? ''}`}>
        {entityDecisions.length === 0 ? (
          <Empty description="No decisions for this entity yet" />
        ) : (
          <List
            itemLayout="vertical" size="small" dataSource={entityDecisions}
            renderItem={(d) => (
              <List.Item key={d.id}>
                <Space wrap>
                  <Link to={`/decisions/${d.id}`}><b>#{d.id}</b></Link>
                  <Tag color={Number(d.impact_score) >= 0 ? 'blue' : 'red'}>
                    impact <span className="num">{fmtScore(d.impact_score)}</span>
                  </Tag>
                  <Tag>
                    confidence <span className="num">{Number(d.confidence).toFixed(2)}</span>
                  </Tag>
                  <Typography.Text type="secondary">
                    {new Date(d.created_at).toLocaleString()}
                  </Typography.Text>
                </Space>
                <div style={{ marginTop: 4 }}>{d.headline}</div>
                <Typography.Text type="secondary">
                  cites {d.retrieved_case_ids.length} historical case(s)
                </Typography.Text>
              </List.Item>
            )}
          />
        )}
      </Card>
    </Space>
  )
}
