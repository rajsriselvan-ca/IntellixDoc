import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'IntellixDoc - RAG Document Q&A',
  description: 'Ask questions about your documents with AI-powered answers',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}

