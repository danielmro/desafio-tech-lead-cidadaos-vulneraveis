"use client";
// Página aprimorada (tema escuro) com filtros e tabela completa de chamados.
// Mantém o fluxo de autenticação mock (login → token em memória) e consome a API paginada.

import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type FiltroState = {
  id_chamado: string;
  data_inicio: string; // YYYY-MM-DD (igualdade)
  data_fim: string; // YYYY-MM-DD (igualdade)
  tipo: string;
  subtipo: string; // habilitado apenas quando tipo preenchido
  status: string;
  situacao: string;
};

export default function HomePage() {
  // Estado de autenticação e dados
  const [token, setToken] = useState<string | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [orderBy, setOrderBy] = useState("data_inicio");
  const [orderDir, setOrderDir] = useState<"asc" | "desc">("desc");

  // Total de páginas calculado a partir do total retornado e do pageSize atual
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

  // Navegação de página
  const goToPage = (p: number) => {
    const target = Math.min(Math.max(1, p), totalPages);
    setPage(target);
  };
  const nextPage = () => goToPage(page + 1);
  const prevPage = () => goToPage(page - 1);

  // Filtros solicitados
  const [filtros, setFiltros] = useState<FiltroState>({
    id_chamado: "",
    data_inicio: "",
    data_fim: "",
    tipo: "",
    subtipo: "",
    status: "",
    situacao: "",
  });

  // Autenticação mock
  async function doLogin() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: "demo", role: "operador" }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setToken(data.access_token);
    } catch (e: any) {
      setError(`Erro no login: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  // Monta a query string com paginação, ordenação e filtros
  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(pageSize));
    params.set("order_by", orderBy);
    params.set("order_dir", orderDir);

    if (filtros.id_chamado) params.set("id_chamado", filtros.id_chamado.trim());
    if (filtros.data_inicio) params.set("data_inicio", filtros.data_inicio);
    if (filtros.data_fim) params.set("data_fim", filtros.data_fim);
    if (filtros.tipo) params.set("tipo", filtros.tipo);
    if (filtros.tipo && filtros.subtipo) params.set("subtipo", filtros.subtipo);
    if (filtros.status) params.set("status", filtros.status);
    if (filtros.situacao) params.set("situacao", filtros.situacao);

    return params.toString();
  }, [page, pageSize, orderBy, orderDir, filtros]);

  // Carrega a página de chamados usando o token
  async function loadChamados() {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/chamados?${queryString}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Exporta CSV respeitando os mesmos filtros (autenticado)
  async function exportCsv() {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/export?${queryString}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chamados.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(`Falha na exportação: ${e.message}`);
    }
  }

  // Atualiza itens quando token ou filtros/pagina/ordem mudarem
  useEffect(() => {
    if (token) loadChamados();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, queryString]);

  // Reseta subtipo se tipo ficar vazio
  useEffect(() => {
    if (!filtros.tipo && filtros.subtipo) {
      setFiltros((f) => ({ ...f, subtipo: "" }));
    }
  }, [filtros.tipo]);

  // Estilos simples de tema escuro (sem dependências externas)
  const darkStyles: React.CSSProperties = {
    background: "#0f172a", // slate-900
    color: "#e2e8f0", // slate-200
    minHeight: "100vh",
    fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
  };
  const panel: React.CSSProperties = {
    background: "#111827", // gray-900
    border: "1px solid #1f2937", // gray-800
    borderRadius: 8,
    padding: 16,
  };
  const input: React.CSSProperties = {
    background: "#0b1220",
    color: "#e5e7eb",
    border: "1px solid #374151",
    padding: "6px 10px",
    borderRadius: 6,
  };
  const label: React.CSSProperties = { fontSize: 12, color: "#94a3b8" };
  const button: React.CSSProperties = { background: "#2563eb", color: "#fff", padding: "8px 12px", borderRadius: 6 };
  const btnGhost: React.CSSProperties = { background: "transparent", color: "#e5e7eb", padding: "8px 12px", borderRadius: 6, border: "1px solid #374151" };

  return (
    <main style={darkStyles} className="p-6 space-y-4">
      <h1 className="text-2xl font-bold">APP 1746 — Consulta de Chamados</h1>

      {!token ? (
        <div style={panel} className="space-y-3">
          <p>Faça login para consultar.</p>
          <button style={button} onClick={doLogin} disabled={loading}>
            {loading ? "Carregando..." : "Fazer login (mock)"}
          </button>
          {error && <div style={{ color: "#fca5a5" }}>Erro: {error}</div>}
        </div>
      ) : (
        <>
          {/* Filtros */}
          <section style={panel} className="space-y-3">
            <h2 className="text-lg font-semibold">Filtros</h2>
            <div className="grid" style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(0, 1fr))", gap: 12 }}>
              <div>
                <div style={label}>id_chamado</div>
                <input style={input} type="number" value={filtros.id_chamado} onChange={(e) => setFiltros({ ...filtros, id_chamado: e.target.value })} placeholder="ex.: 123" />
              </div>
              <div>
                <div style={label}>data_inicio</div>
                <input style={input} type="date" value={filtros.data_inicio} onChange={(e) => setFiltros({ ...filtros, data_inicio: e.target.value })} />
              </div>
              <div>
                <div style={label}>data_fim</div>
                <input style={input} type="date" value={filtros.data_fim} onChange={(e) => setFiltros({ ...filtros, data_fim: e.target.value })} />
              </div>
              <div>
                <div style={label}>status</div>
                <input style={input} type="text" value={filtros.status} onChange={(e) => setFiltros({ ...filtros, status: e.target.value })} placeholder="ex.: ENCERRADO" />
              </div>
              <div>
                <div style={label}>situacao</div>
                <input style={input} type="text" value={filtros.situacao} onChange={(e) => setFiltros({ ...filtros, situacao: e.target.value })} placeholder="ex.: ABERTO" />
              </div>
              <div>
                <div style={label}>tipo</div>
                <input style={input} type="text" value={filtros.tipo} onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })} placeholder="ex.: SAÚDE" />
              </div>
              <div>
                <div style={label}>subtipo</div>
                <input
                  style={{ ...input, opacity: filtros.tipo ? 1 : 0.5 }}
                  type="text"
                  value={filtros.subtipo}
                  onChange={(e) => setFiltros({ ...filtros, subtipo: e.target.value })}
                  placeholder={filtros.tipo ? "ex.: SUBTIPO A" : "Preencha o tipo primeiro"}
                  disabled={!filtros.tipo}
                />
              </div>
            </div>

            <div className="flex" style={{ display: "flex", gap: 8 }}>
              <button style={button} onClick={() => { setPage(1); loadChamados(); }}>Aplicar filtros</button>
              <button style={btnGhost} onClick={() => { setFiltros({ id_chamado: "", data_inicio: "", data_fim: "", tipo: "", subtipo: "", status: "", situacao: "" }); setPage(1); }}>Limpar</button>
            </div>
          </section>

          {/* Resultados */}
          <section style={panel} className="space-y-3">
            <div className="flex" style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center" }}>
              <div>
                <div style={label}>Ordenar por</div>
                <select style={input} value={orderBy} onChange={(e) => setOrderBy(e.target.value)}>
                  <option value="data_inicio">data_inicio</option>
                  <option value="data_fim">data_fim</option>
                  <option value="data_alvo_finalizacao">data_alvo_finalizacao</option>
                  <option value="tipo">tipo</option>
                  <option value="subtipo">subtipo</option>
                  <option value="status">status</option>
                  <option value="situacao">situacao</option>
                  <option value="secretaria">secretaria</option>
                  <option value="data_particao">data_particao</option>
                  <option value="id_chamado">id_chamado</option>
                </select>
                <select style={{ ...input, marginLeft: 8 }} value={orderDir} onChange={(e) => setOrderDir(e.target.value as any)}>
                  <option value="asc">asc</option>
                  <option value="desc">desc</option>
                </select>
              </div>

              <div>
                <div style={label}>Página</div>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <button style={btnGhost} onClick={() => goToPage(1)} disabled={page <= 1}>{"<<"}</button>
                  <button style={btnGhost} onClick={prevPage} disabled={page <= 1}>{"<"}</button>
                  {/* Números de página (janela) */}
                  {(() => {
                    const maxButtons = 7;
                    let start = Math.max(1, page - Math.floor(maxButtons / 2));
                    let end = Math.min(totalPages, start + maxButtons - 1);
                    if (end - start + 1 < maxButtons) {
                      start = Math.max(1, end - maxButtons + 1);
                    }
                    const btns = [] as JSX.Element[];
                    for (let p = start; p <= end; p++) {
                      const isCurrent = p === page;
                      btns.push(
                        <button
                          key={p}
                          style={{
                            ...btnGhost,
                            background: isCurrent ? "#2563eb" : btnGhost.background as any,
                            borderColor: isCurrent ? "#2563eb" : "#374151",
                          }}
                          onClick={() => goToPage(p)}
                          disabled={isCurrent}
                        >
                          {p}
                        </button>
                      );
                    }
                    return btns;
                  })()}
                  <button style={btnGhost} onClick={nextPage} disabled={page >= totalPages}>{">"}</button>
                  <button style={btnGhost} onClick={() => goToPage(totalPages)} disabled={page >= totalPages}>{">>"}</button>
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: "#94a3b8" }}>Página {page} de {totalPages}</div>
                <div style={{ marginTop: 6 }}>
                  <div style={label}>Itens por página</div>
                  <select
                    style={{ ...input, width: 120 }}
                    value={pageSize}
                    onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                  >
                    {[10, 20, 50, 100, 200].map(sz => (
                      <option key={sz} value={sz}>{sz}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex" style={{ display: "flex", gap: 8 }}>
                <button style={button} onClick={loadChamados} disabled={loading}>{loading ? "Carregando..." : "Atualizar"}</button>
                <button style={btnGhost} onClick={exportCsv}>Exportar CSV</button>
              </div>
            </div>

            <div style={{ fontSize: 12, color: "#94a3b8" }}>Total: {total} registros</div>

            {error && <div style={{ color: "#fca5a5" }}>Erro: {error}</div>}

            <div style={{ overflowX: "auto" }}>
              <table className="min-w-full text-sm" style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    {[
                      "id_chamado",
                      "data_inicio",
                      "data_fim",
                      "data_alvo_finalizacao",
                      "tipo",
                      "subtipo",
                      "status",
                      "situacao",
                      "longitude",
                      "latitude",
                      "data_particao",
                      "secretaria",
                    ].map((col) => (
                      <th key={col} style={{ textAlign: "left", borderBottom: "1px solid #1f2937", padding: "8px" }}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {items.map((it, idx) => (
                    <tr key={idx}>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.id_chamado}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.data_inicio}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.data_fim}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.data_alvo_finalizacao}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.tipo}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.subtipo}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.status}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.situacao}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.longitude}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.latitude}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.data_particao}</td>
                      <td style={{ padding: "8px", borderBottom: "1px solid #1f2937" }}>{it.secretaria}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}
