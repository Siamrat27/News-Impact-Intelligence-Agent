import { Tag } from 'antd'
import {
  ArrowUpOutlined, ArrowDownOutlined, MinusOutlined,
} from '@ant-design/icons'

// status color never carries meaning alone: icon + label always ship with it
const STYLES = {
  positive: { color: 'green', icon: <ArrowUpOutlined /> },
  negative: { color: 'red', icon: <ArrowDownOutlined /> },
  neutral: { color: 'default', icon: <MinusOutlined /> },
}

export default function SentimentTag({ label, value }) {
  const s = STYLES[label] ?? STYLES.neutral
  return (
    <Tag color={s.color} icon={s.icon}>
      {label ?? 'unscored'}
      {value != null && (
        <span className="num"> {Number(value).toFixed(2)}</span>
      )}
    </Tag>
  )
}
