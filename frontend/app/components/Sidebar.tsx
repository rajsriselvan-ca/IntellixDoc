'use client'

import { FileText, MessageSquare, Upload, Plus, Trash2 } from 'lucide-react'

interface SidebarProps {
  chats: any[]
  documents: any[]
  selectedChat: number | null
  onChatSelect: (chatId: number) => void
  onNewChat: () => void
  onUploadClick: () => void
  onDeleteChat: (chatId: number) => void
  onDeleteDocument: (documentId: number) => void
}

export default function Sidebar({
  chats,
  documents,
  selectedChat,
  onChatSelect,
  onNewChat,
  onUploadClick,
  onDeleteChat,
  onDeleteDocument,
}: SidebarProps) {
  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <button
          onClick={onNewChat}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition flex items-center justify-center gap-2"
        >
          <Plus size={20} />
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <MessageSquare size={16} />
            Chats
          </h2>
          <div className="space-y-1">
            {chats.map((chat) => (
              <div
                key={chat.id}
                className={`group flex items-center justify-between px-3 py-2 rounded-lg text-sm transition ${
                  selectedChat === chat.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <button
                  onClick={() => onChatSelect(chat.id)}
                  className="flex-1 text-left truncate"
                >
                  {chat.title}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteChat(chat.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-600 transition"
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
              <FileText size={16} />
              Documents
            </h2>
            <button
              onClick={onUploadClick}
              className="text-blue-600 hover:text-blue-700"
              title="Upload Document"
            >
              <Upload size={16} />
            </button>
          </div>
          <div className="space-y-1">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="group px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
              >
                <div className="flex items-center justify-between">
                  <span className="truncate flex-1">{doc.filename}</span>
                  <div className="flex items-center gap-1">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        doc.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : doc.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {doc.status}
                    </span>
                    <button
                      onClick={() => onDeleteDocument(doc.id)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded text-gray-400 hover:text-red-600 transition"
                      title="Delete document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

