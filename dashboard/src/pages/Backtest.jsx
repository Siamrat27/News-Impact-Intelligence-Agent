import { useEffect, useMemo, useState } from 'react'
import { Card, Col, Row, Statistic, Table, Typography, message } from 'antd'
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip,
  XAxis, YAxis, LabelList,
} from 'recharts'
import { api } from '../api.js'
import { viz } from '../theme.js'

export default function Backtest() {
  const [rows, setRows] = useState([])

  useEffect(() => {
    api.winrate().then(setRows).catch((e) => message.error(String(e)))
  }, [])

  const overall = rows.find((r) => r.entity === 'ALL')
  const perEntity = useMemo(() =>
    rows
      .filter((r) => r.entity !== 'ALL' && r.win_rate_pct != null)
      .map((r) => ({ ...r, pct: Number(r.win_rate_pct) }))
      .sort((a, b) => b.pct - a.pct),
    [rows])

  const columns = [
    { title: 'Entity', dataIndex: 'entity' },
    { title: 'Evaluated', dataIndex: 'evaluated', className: 'num', align: 'right' },
    { title: 'Wins', dataIndex: 'wins', className: 'num', align: 'right' },
    {
      title: 'Win rate', dataIndex: 'win_rate_pct', className: 'num',
      align: 'right', render: (v) => (v == null ? '—' : `${v}%`),
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={8}>
        <Card>
          <Statistic
            title="Overall win rate (direction match, 24h follow-up)"
            value={overall ? Number(overall.win_rate_pct) : '—'}
            suffix="%" precision={1}
          />
          <Typography.Text type="secondary">
            {overall
              ? `${overall.wins} of ${overall.evaluated} evaluated decisions`
              : 'no evaluations yet'}
          </Typography.Text>
        </Card>
        <Card title="Per-entity summary" style={{ marginTop: 16 }} size="small">
          <Table
            size="small" rowKey="entity" columns={columns}
            dataSource={perEntity} pagination={false}
          />
        </Card>
      </Col>
      <Col xs={24} md={16}>
        <Card title="Win rate by entity (%)">
          <ResponsiveContainer width="100%" height={Math.max(260, perEntity.length * 42)}>
            <BarChart
              data={perEntity} layout="vertical"
              margin={{ left: 24, right: 32 }}
              style={{ background: viz.surface }}
            >
              <CartesianGrid stroke={viz.grid} horizontal={false} />
              <XAxis
                type="number" domain={[0, 100]} stroke={viz.baseline}
                tick={{ fill: viz.muted, fontSize: 12 }}
              />
              <YAxis
                type="category" dataKey="entity" width={110}
                stroke={viz.baseline} tick={{ fill: viz.inkSecondary, fontSize: 12 }}
              />
              <Tooltip formatter={(v) => [`${v}%`, 'win rate']} />
              <Bar dataKey="pct" fill={viz.series1} radius={[0, 4, 4, 0]} barSize={18}>
                <LabelList
                  dataKey="pct" position="right"
                  formatter={(v) => `${v.toFixed(0)}%`}
                  style={{ fill: viz.inkSecondary, fontSize: 12 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>
  )
}
