import { useState } from 'react'
import { analyzeFile, loadSample, downloadReport } from './api.js'

const fmtMoney = (n, ccy = 'INR') =>
  `${ccy} ${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function Kpi({ label, value }) {
  return (
    <div className="kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

export default function App() {
  const [report, setReport] = useState(null)
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function run(fn) {
    setError('')
    setLoading(true)
    try {
      setReport(await fn())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const onUpload = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    run(() => analyzeFile(f))
  }

  const s = report?.summary
  const maxCat = report ? Math.max(...report.by_category.map((c) => c.total)) : 0

  return (
    <div className="page">
      <header>
        <h1>Spend Analyzer</h1>
        <p className="sub">Upload an expenses CSV to see category, vendor and monthly analytics, duplicate-payment flags and downloadable reports.</p>
      </header>

      <div className="controls">
        <label className="btn primary">
          Upload CSV
          <input type="file" accept=".csv" onChange={onUpload} hidden />
        </label>
        <button className="btn" onClick={() => run(loadSample)}>Load sample data</button>
        {report && file && (
          <>
            <button className="btn" onClick={() => downloadReport(file, 'excel')}>Download Excel</button>
            <button className="btn" onClick={() => downloadReport(file, 'pdf')}>Download PDF</button>
          </>
        )}
      </div>

      {loading && <p className="muted">Analyzing…</p>}
      {error && <p className="error">{error}</p>}

      {report && (
        <>
          <section className="kpis">
            <Kpi label="Total spend" value={fmtMoney(s.total_spend, s.currency)} />
            <Kpi label="Transactions" value={s.transaction_count} />
            <Kpi label="Avg transaction" value={fmtMoney(s.average_transaction, s.currency)} />
            <Kpi label="Potential recovery" value={fmtMoney(report.potential_recovery, s.currency)} />
          </section>

          {report.insights.length > 0 && (
            <section className="card">
              <h2>Insights</h2>
              <ul className="insights">
                {report.insights.map((note, i) => <li key={i}>{note}</li>)}
              </ul>
            </section>
          )}

          <section className="card">
            <h2>Spend by category</h2>
            {report.by_category.map((c) => (
              <div className="bar-row" key={c.category}>
                <span className="bar-label">{c.category}</span>
                <span className="bar-track">
                  <span className="bar-fill" style={{ width: `${(c.total / maxCat) * 100}%` }} />
                </span>
                <span className="bar-value">{fmtMoney(c.total, s.currency)} ({c.share_pct}%)</span>
              </div>
            ))}
          </section>

          <div className="two-col">
            <section className="card">
              <h2>Top vendors</h2>
              <table>
                <thead><tr><th>Vendor</th><th>Total</th><th>#</th></tr></thead>
                <tbody>
                  {report.by_vendor.map((v) => (
                    <tr key={v.vendor}><td>{v.vendor}</td><td>{fmtMoney(v.total, s.currency)}</td><td>{v.count}</td></tr>
                  ))}
                </tbody>
              </table>
            </section>

            <section className="card">
              <h2>Suspected duplicate payments</h2>
              {report.duplicate_suspects.length === 0 ? (
                <p className="muted">None detected.</p>
              ) : (
                <table>
                  <thead><tr><th>Vendor</th><th>Amount</th><th>×</th><th>Recoverable</th></tr></thead>
                  <tbody>
                    {report.duplicate_suspects.map((d, i) => (
                      <tr key={i}><td>{d.vendor}</td><td>{fmtMoney(d.amount, s.currency)}</td><td>{d.occurrences}</td><td>{fmtMoney(d.recoverable, s.currency)}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </div>
        </>
      )}

      {!report && !loading && <p className="muted hint">No data yet — upload a CSV or load the sample.</p>}
    </div>
  )
}
