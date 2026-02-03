'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, FileText } from 'lucide-react'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  citations?: Citation[]
}

interface Citation {
  id: number
  document_filename: string
  chunk_content: string
  page_number?: number
  relevance_score?: number
}

interface ChatInterfaceProps {
  chatId: number
  API_URL: string
}

export default function ChatInterface({ chatId, API_URL }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showCitations, setShowCitations] = useState<number | null>(null)

  useEffect(() => {
    fetchMessages()
  }, [chatId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchMessages = async () => {
    try {
      const response = await fetch(`${API_URL}/api/chats/${chatId}/messages`)
      const data = await response.json()
      setMessages(data)
    } catch (error) {
      console.error('Error fetching messages:', error)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      content: input,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/chats/${chatId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: input }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const assistantMessage = await response.json()
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">
                Start a conversation
              </h2>
              <p className="text-gray-600">
                Ask questions about your uploaded documents
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-300">
                    <button
                      onClick={() =>
                        setShowCitations(
                          showCitations === message.id ? null : message.id
                        )
                      }
                      className="text-sm text-blue-600 hover:text-blue-700 flex items-center gap-1"
                    >
                      <FileText size={14} />
                      {message.citations.length} citation
                      {message.citations.length > 1 ? 's' : ''}
                    </button>
                    {showCitations === message.id && (
                      <div className="mt-2 space-y-2">
                        {message.citations.map((citation, idx) => (
                          <div
                            key={citation.id}
                            className="text-xs bg-white p-2 rounded border border-gray-200"
                          >
                            <div className="font-semibold text-gray-700">
                              {citation.document_filename}
                              {citation.page_number && ` (Page ${citation.page_number})`}
                            </div>
                            <div className="text-gray-600 mt-1">
                              {citation.chunk_content}
                            </div>
                            {citation.relevance_score && (
                              <div className="text-gray-400 mt-1">
                                Relevance: {(citation.relevance_score * 100).toFixed(1)}%
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 p-4">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 resize-y border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={1}
            style={{ maxHeight: '300px', minHeight: '40px' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

