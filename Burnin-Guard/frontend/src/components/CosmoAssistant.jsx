import { useState } from 'react'
import { api } from '../api'

function CosmoAssistant({ anomalyData }) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello. I am COSMO, your component screening assistant. Ask me about risk, DUTs, lots, or 500h projections.' },
  ])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

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
      const response = await api.askCosmo(text, history)
      setMessages((current) => [...current, { role: 'assistant', text: response.answer }])
    } catch (err) {
      setError(err.message || 'COSMO is unavailable')
    } finally {
      setBusy(false)
    }
  }

  const suggestions = anomalyData?.length
    ? ['Summarize the fleet', 'Which DUT is highest risk?', 'Check the 500h projection']
    : ['Hello COSMO', 'Summarize the fleet']

  return (
    <div className={`cosmo-assistant ${open ? 'is-open' : ''}`}>
      {open && (
        <section className="cosmo-panel" aria-label="COSMO assistant">
          <header className="cosmo-header">
            <div className="cosmo-mark small"><span>✦</span></div>
            <div><strong>COSMO</strong><span>Component Observation Operator</span></div>
            <button className="cosmo-close" onClick={() => setOpen(false)} aria-label="Close COSMO">×</button>
          </header>
          <div className="cosmo-messages">
            {messages.map((message, index) => (
              <div className={`cosmo-message ${message.role}`} key={`${message.role}-${index}`}>
                {message.text}
              </div>
            ))}
            {busy && <div className="cosmo-message assistant">Analyzing current results...</div>}
          </div>
          <div className="cosmo-suggestions">
            {suggestions.map((suggestion) => <button key={suggestion} onClick={() => setQuestion(suggestion)}>{suggestion}</button>)}
          </div>
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