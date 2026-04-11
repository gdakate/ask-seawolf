"use client";

import { useQuery } from "@tanstack/react-query";
import { getAdminSettings } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

function Row({ label, value, badge }: { label: string; value?: string | number | boolean | null; badge?: string }) {
  const display = value === true ? "yes" : value === false ? "no" : value ?? "—";
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <span className="text-sm text-gray-700">{label}</span>
      {badge ? (
        <span className={`font-mono text-xs px-2 py-1 rounded ${badge}`}>{display}</span>
      ) : (
        <span className="font-mono text-xs text-gray-500">{String(display)}</span>
      )}
    </div>
  );
}

const PROVIDER_BADGE: Record<string, string> = {
  mock:    "bg-gray-100 text-gray-600",
  openai:  "bg-green-100 text-green-700",
  local:   "bg-blue-100 text-blue-700",
  bedrock: "bg-orange-100 text-orange-700",
};

const ENV_BADGE: Record<string, string> = {
  development: "bg-yellow-100 text-yellow-700",
  staging:     "bg-orange-100 text-orange-700",
  production:  "bg-green-100 text-green-700",
};

export default function SettingsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["admin-settings"], queryFn: getAdminSettings });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8 bg-gray-50 min-h-screen">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Settings</h1>
        <p className="text-sm text-gray-500 mb-6">Live platform configuration</p>

        {isLoading ? (
          <div className="text-gray-400 text-sm">Loading...</div>
        ) : (
          <div className="space-y-6 max-w-2xl">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">AI Provider</h3>
              <div className="space-y-2">
                <Row
                  label="AI_PROVIDER"
                  value={data?.ai_provider}
                  badge={PROVIDER_BADGE[data?.ai_provider] || "bg-gray-100 text-gray-600"}
                />
                {data?.ai_provider === "openai" && (
                  <>
                    <Row label="OPENAI_MODEL" value={data?.openai_model} />
                    <Row label="OPENAI_API_KEY" value={data?.openai_key_set ? "configured" : "not set"}
                      badge={data?.openai_key_set ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"} />
                  </>
                )}
                {data?.ai_provider === "local" && (
                  <Row label="OLLAMA_MODEL" value={data?.ollama_model} />
                )}
                {data?.ai_provider === "bedrock" && (
                  <Row label="BEDROCK_MODEL_ID" value={data?.bedrock_model_id} />
                )}
                <Row label="EMBEDDING_DIMENSIONS" value={data?.embedding_dimensions} />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Storage</h3>
              <div className="space-y-2">
                <Row
                  label="STORAGE_BACKEND"
                  value={data?.storage_backend}
                  badge={data?.storage_backend === "s3" ? "bg-orange-100 text-orange-700" : "bg-blue-100 text-blue-700"}
                />
                <Row label="DATABASE" value="PostgreSQL + pgvector" />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Auth & Session</h3>
              <div className="space-y-2">
                <Row label="JWT_EXPIRE_MINUTES" value={data?.jwt_expire_minutes} />
                <Row label="CORS_ORIGINS" value={data?.cors_origins} />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Environment</h3>
              <div className="space-y-2">
                <Row
                  label="ENVIRONMENT"
                  value={data?.environment}
                  badge={ENV_BADGE[data?.environment] || "bg-gray-100 text-gray-600"}
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
