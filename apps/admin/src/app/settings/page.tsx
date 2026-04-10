"use client";

import { Sidebar } from "@/components/sidebar";

export default function SettingsPage() {
  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
        <p className="text-sm text-gray-500 mb-6">Platform configuration</p>

        <div className="space-y-6 max-w-2xl">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">AI Provider</h3>
            <p className="text-sm text-gray-500 mb-3">Configure via environment variables. Current mode is determined by the <code className="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">AI_PROVIDER</code> setting.</p>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">AI_PROVIDER</span>
                <span className="font-mono text-xs px-2 py-1 bg-green-100 text-green-700 rounded">mock</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">OPENAI_MODEL</span>
                <span className="font-mono text-xs text-gray-500">gpt-4o</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">EMBEDDING_DIMENSIONS</span>
                <span className="font-mono text-xs text-gray-500">384</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Storage</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">STORAGE_BACKEND</span>
                <span className="font-mono text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">local</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-gray-700">DATABASE</span>
                <span className="font-mono text-xs text-gray-500">PostgreSQL + pgvector</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Environment Variables</h3>
            <p className="text-sm text-gray-500">
              All configuration is managed via environment variables. See <code className="px-1 py-0.5 bg-gray-100 rounded text-xs font-mono">.env.example</code> for the full list. 
              Key settings include AI provider selection, database URLs, storage backend, and authentication secrets.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
