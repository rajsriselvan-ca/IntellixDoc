'use client'

import { useState, useEffect, useRef } from 'react'
import ChatInterface from './components/ChatInterface'
import DocumentUpload from './components/DocumentUpload'
import Sidebar from './components/Sidebar'

export default function Home() {
  const [chats, setChats] = useState<any[]>([])
  const [selectedChat, setSelectedChat] = useState<number | null>(null)
  const [documents, setDocuments] = useState<any[]>([])
  const [showUpload, setShowUpload] = useState(false)
  const pollingIntervalsRef = useRef<Set<NodeJS.Timeout>>(new Set())

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  
  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      pollingIntervalsRef.current.forEach(interval => clearInterval(interval))
      pollingIntervalsRef.current.clear()
    }
  }, [])

  useEffect(() => {
    fetchChats()
    fetchDocuments()
  }, [])

  const fetchChats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/chats`)
      const data = await response.json()
      setChats(data)
    } catch (error) {
      console.error('Error fetching chats:', error)
    }
  }

  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents`)
      const data = await response.json()
      setDocuments(data)
    } catch (error) {
      console.error('Error fetching documents:', error)
    }
  }

  const handleNewChat = async () => {
    try {
      const response = await fetch(`${API_URL}/api/chats`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      })
      const newChat = await response.json()
      setChats([newChat, ...chats])
      setSelectedChat(newChat.id)
      setShowUpload(false)
    } catch (error) {
      console.error('Error creating chat:', error)
    }
  }

  const handleChatSelect = (chatId: number) => {
    setSelectedChat(chatId)
    setShowUpload(false)
  }

  const handleDocumentUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }
      
      const document = await response.json()
      setDocuments([document, ...documents])
      setShowUpload(false)
      
      // Poll for document status with cleanup and timeout
      let pollCount = 0
      const maxPolls = 300 // 10 minutes max (300 * 2000ms)
      const pollStatus = setInterval(async () => {
        pollCount++
        
        // Stop polling after max attempts
        if (pollCount > maxPolls) {
          clearInterval(pollStatus)
          pollingIntervalsRef.current.delete(pollStatus)
          console.warn(`Document ${document.id} processing timeout after ${maxPolls * 2} seconds`)
          fetchDocuments() // Refresh to show current status
          return
        }
        
        try {
          const statusResponse = await fetch(`${API_URL}/api/documents/${document.id}`)
          if (!statusResponse.ok) {
            throw new Error(`Status check failed: ${statusResponse.statusText}`)
          }
          
          const updatedDoc = await statusResponse.json()
          if (updatedDoc.status === 'completed' || updatedDoc.status === 'failed') {
            clearInterval(pollStatus)
            pollingIntervalsRef.current.delete(pollStatus)
            fetchDocuments() // Refresh to show final status
          }
        } catch (error) {
          console.error('Error checking document status:', error)
          // Continue polling on error, but log it
        }
      }, 2000)
      
      // Store interval reference for cleanup
      pollingIntervalsRef.current.add(pollStatus)
    } catch (error) {
      console.error('Error uploading document:', error)
      alert('Failed to upload document. Please try again.')
    }
  }

  const handleDeleteChat = async (chatId: number) => {
    if (!confirm('Are you sure you want to delete this chat?')) return
    
    try {
      const response = await fetch(`${API_URL}/api/chats/${chatId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        setChats(chats.filter(chat => chat.id !== chatId))
        if (selectedChat === chatId) {
          setSelectedChat(null)
        }
      }
    } catch (error) {
      console.error('Error deleting chat:', error)
    }
  }

  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return
    
    try {
      const response = await fetch(`${API_URL}/api/documents/${documentId}`, {
        method: 'DELETE',
      })
      if (response.ok) {
        setDocuments(documents.filter(doc => doc.id !== documentId))
      }
    } catch (error) {
      console.error('Error deleting document:', error)
    }
  }

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        chats={chats}
        documents={documents}
        selectedChat={selectedChat}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
        onUploadClick={() => setShowUpload(true)}
        onDeleteChat={handleDeleteChat}
        onDeleteDocument={handleDeleteDocument}
      />
      <main className="flex-1 flex flex-col">
        {showUpload ? (
          <DocumentUpload
            onUpload={handleDocumentUpload}
            onCancel={() => setShowUpload(false)}
          />
        ) : selectedChat ? (
          <ChatInterface chatId={selectedChat} API_URL={API_URL} />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-4xl font-bold mb-4 text-gray-800">IntellixDoc</h1>
              <p className="text-gray-600 mb-8">Upload documents and ask questions</p>
              <button
                onClick={handleNewChat}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
              >
                Start New Chat
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

