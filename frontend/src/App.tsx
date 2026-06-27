import React, { useState, useEffect } from 'react';
import './App.css';

interface Source {
  contrato: string;
  trecho: string;
  texto_original: string;
}

interface Message {
  sender: 'user' | 'bot';
  text: string;
  sources?: Source[];
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [contracts, setContracts] = useState<string[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>('');
  
  const [question, setQuestion] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const res = await fetch(`${API_URL}/api/contracts`);
      const data = await res.json();
      setContracts(data.contracts || []);
    } catch (error) {
      console.error("Erro ao buscar contratos", error);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setUploadStatus('Selecione um arquivo.');
      return;
    }
    setUploadStatus('Processando e gerando resumo...');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(data.mensagem);
        fetchContracts();
        if (data.resumo) {
            setMessages((prev) => [...prev, { 
                sender: 'bot', 
                text: `✅ Contrato ${file.name} indexado!\n\n**Resumo Automático:**\n${data.resumo}` 
            }]);
        }
      } else {
        setUploadStatus(`Erro: ${data.detail}`);
      }
    } catch (error) {
      setUploadStatus('Falha de comunicação.');
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      await fetch(`${API_URL}/api/contracts/${filename}`, { method: 'DELETE' });
      fetchContracts();
    } catch (error) {
      console.error("Erro ao deletar", error);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;

    const userMessage: Message = { sender: 'user', text: question };
    const currentQuestion = question;
    setQuestion('');
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            question: currentQuestion,
            history: messages.map(m => ({ sender: m.sender, text: m.text })) 
        }),
      });
      
      const data = await res.json();
      if (res.ok) {
        setMessages((prev) => [...prev, { sender: 'bot', text: data.answer, sources: data.sources }]);
      } else {
        setMessages((prev) => [...prev, { sender: 'bot', text: `Erro: ${data.detail}` }]);
      }
    } catch (error) {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Falha de comunicação.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <h2>MNGT RAG Engine</h2>
        <div className="upload-section">
          <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} className="file-input" />
          <button onClick={handleUpload} className="btn-upload">Indexar Contrato</button>
          {uploadStatus && <div className="status-message">{uploadStatus}</div>}
        </div>

        <div className="contract-list" style={{ marginTop: '30px' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '10px', color: '#ccc' }}>Contratos Indexados</h3>
          {contracts.length === 0 && <p style={{fontSize: '0.8rem', color: '#666'}}>Nenhum arquivo.</p>}
          
          {contracts.map(c => (
            <div key={c} style={{ display: 'flex', justifyContent: 'space-between', background: '#1e1e1e', padding: '10px', marginBottom: '8px', borderRadius: '4px', fontSize: '0.9rem', border: '1px solid #333' }}>
              <span style={{overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{c}</span>
              <span onClick={() => handleDelete(c)} style={{ cursor: 'pointer', color: '#ff4444', fontWeight: 'bold', marginLeft: '10px' }}>X</span>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-area">
        <div className="messages-container">
          {messages.length === 0 && <div className="message bot">Sistema inicializado. Base atualizada.</div>}
          
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources-container">
                  <strong>Fontes recuperadas:</strong>
                  {msg.sources.map((source, idx) => (
                    <div key={idx} className="source-item">
                      <em>{source.contrato} ({source.trecho}):</em> {source.texto_original}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
          {isLoading && <div className="message bot">Processando...</div>}
        </div>

        <div className="input-area">
          <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleAsk()} placeholder="Consulte cláusulas ou multas..." className="chat-input" disabled={isLoading} />
          <button onClick={handleAsk} className="btn-send" disabled={isLoading || !question.trim()}>Executar</button>
        </div>
      </main>
    </div>
  );
}

export default App;