import { useMemo, useState } from 'react'
import { api } from '../api'

function renderInline(text) {
  return text.split(/(\*\*.*?\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={index}>{part.slice(2, -2)}</strong>
    }
    return <span key={index}>{part}</span>
  })
}

function CosmoMessage({ text }) {
  return (
    <div className="cosmo-rich-text">
      {text.split('\n').map((line, index) => {
        const trimmed = line.trim()
        if (trimmed.startsWith('### ')) return <h4 key={index}>{renderInline(trimmed.slice(4))}</h4>
        if (trimmed.startsWith('- ')) return <div className="cosmo-bullet" key={index}>• {renderInline(trimmed.slice(2))}</div>
        if (/^\d+\. /.test(trimmed)) return <div className="cosmo-bullet" key={index}>{renderInline(trimmed)}</div>
        return <div key={index} className={trimmed ? '' : 'cosmo-line-break'}>{renderInline(line)}</div>
      })}
    </div>
  )
}

function CosmoAssistant({ anomalyData }) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello. I am COSMO, your component screening assistant. Ask me about risk, DUTs, lots, or 500h projections.' },
  ])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [selectedDut, setSelectedDut] = useState('')

  const dutIds = useMemo(() => (anomalyData || []).map((dut) => dut.dut_id).filter(Boolean), [anomalyData])

  const ask = async (event) => {
    event?.preventDefault()
    const text = question.trim()
    if (!text || busy) return
    setQuestion('')
    setError('')
    setMessages((current) => [...current, { role: 'user', text }])
    setBusy(true)
    try {
      const history = messages
        .filter((message) => message.role === 'user' || message.role === 'assistant')
        .map((message) => message.role === 'user'
          ? { user: message.text }
          : { assistant: message.text })
      const mentionedDut = dutIds.find((dutId) => new RegExp(`(^|[^A-Za-z0-9])${dutId}([^A-Za-z0-9]|$)`, 'i').test(text))
      const contextDut = mentionedDut || selectedDut || null
      const response = await api.askCosmo(text, history, contextDut)
      if (mentionedDut) setSelectedDut(mentionedDut)
      setMessages((current) => [...current, { role: 'assistant', text: response.answer }])
    } catch (err) {
      setError(err.message || 'COSMO is unavailable')
    } finally {
      setBusy(false)
    }
  }

  const resetChat = () => {
    setMessages([{ role: 'assistant', text: 'Conversation cleared. Ask me about risk, DUTs, lots, or 500h projections.' }])
    setQuestion('')
    setError('')
    setSelectedDut('')
  }

  const downloadTranscript = () => {
    const csv = ['Role,Message', ...messages.map((message) => [message.role, message.text].map((value) => `"${String(value).replace(/"/g, '""')}"`).join(','))].join('\r\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'cosmo-conversation.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  const suggestions = anomalyData?.length
    ? ['Can we release this lot?', 'Which DUTs need confirmation?', 'What should I investigate next?', 'Which parameter is weakest?']
    : ['Hello COSMO', 'Summarize the fleet']

  return (
    <div className={`cosmo-assistant ${open ? 'is-open' : ''}`}>
      {open && (
        <section className="cosmo-panel" aria-label="COSMO assistant">
          <header className="cosmo-header">
            <div className="cosmo-mark small"><span>✦</span></div>
            <div><strong>COSMO</strong><span>Component Observation Operator</span></div>
            <div className="cosmo-header-actions">
              <button onClick={downloadTranscript} aria-label="Download conversation" title="Download conversation">↓</button>
              <button onClick={resetChat} aria-label="Clear conversation" title="Clear conversation">↺</button>
            </div>
            <button className="cosmo-close" onClick={() => setOpen(false)} aria-label="Close COSMO">×</button>
          </header>
          <div className="cosmo-messages">
            {messages.map((message, index) => (
              <div className={`cosmo-message ${message.role}`} key={`${message.role}-${index}`}>
                <CosmoMessage text={message.text} />
              </div>
            ))}
            {busy && <div className="cosmo-message assistant">Analyzing current results...</div>}
          </div>
          <div className="cosmo-suggestions">
            {suggestions.map((suggestion) => <button key={suggestion} onClick={() => setQuestion(suggestion)}>{suggestion}</button>)}
          </div>
          {dutIds.length > 0 && (
            <label className="cosmo-context">
              <span>Context DUT</span>
              <select value={selectedDut} onChange={(event) => setSelectedDut(event.target.value)}>
                <option value="">Fleet-wide</option>
                {dutIds.map((dutId) => <option key={dutId} value={dutId}>{dutId}</option>)}
              </select>
            </label>
          )}
          {error && <p className="cosmo-error" role="alert">{error}</p>}
          <form className="cosmo-form" onSubmit={ask}>
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask COSMO..." aria-label="Ask COSMO" />
            <button type="submit" disabled={busy || !question.trim()} aria-label="Send question">➜</button>
          </form>
        </section>
      )}
      <button className="cosmo-launcher" onClick={() => setOpen((current) => !current)} aria-label="Open COSMO assistant" title="Open COSMO assistant">
        <span className="cosmo-orbit orbit-one"></span>
        <span className="cosmo-orbit orbit-two"></span>
        <span className="cosmo-mark"><span>✦</span></span>
      </button>
    </div>
  )
}

export default CosmoAssistant