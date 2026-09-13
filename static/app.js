const API = '';

// State
let products = [];
let stats = {};
let listings = [];

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const page = link.dataset.page;
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + page).classList.add('active');
  });
});

// Fetch helpers
async function fetchJSON(url) {
  const res = await fetch(API + url);
  return res.json();
}

async function postJSON(url, data = {}) {
  const res = await fetch(API + url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

// Load data
async function loadAll() {
  [products, stats, listings] = await Promise.all([
    fetchJSON('/api/products'),
    fetchJSON('/api/stats'),
    fetchJSON('/api/listings'),
  ]);
  renderStats();
  renderDashboardTable();
  renderProductsTable();
  renderListings();
}

// Stats
function renderStats() {
  document.getElementById('stat-total').textContent = stats.total || 0;
  document.getElementById('stat-approved').textContent =
    (stats.curated_approved || 0) + (stats.copy_ready || 0) + (stats.exported || 0) + (stats.published || 0);
  document.getElementById('stat-rejected').textContent = stats.curated_rejected || 0;
  document.getElementById('stat-published').textContent = (stats.exported || 0) + (stats.published || 0);
}

// Status labels
const STATUS_LABELS = {
  researched: 'Pesquisado',
  curated_approved: 'Aprovado',
  curated_rejected: 'Rejeitado',
  copy_ready: 'Copy Pronta',
  exported: 'Exportado',
  published: 'Publicado',
};

function statusBadge(status) {
  const label = STATUS_LABELS[status] || status;
  return `<span class="badge badge-${status}">${label}</span>`;
}

function scoreBar(score) {
  if (score == null) return '<span class="text-muted">—</span>';
  const color = score >= 60 ? 'var(--green)' : score >= 40 ? 'var(--yellow)' : 'var(--red)';
  return `
    <div class="score-bar">
      <div class="score-track">
        <div class="score-fill" style="width:${score}%; background:${color}"></div>
      </div>
      <span class="score-value" style="color:${color}">${score}</span>
    </div>`;
}

// Link helper
function productLink(url) {
  if (!url) return '<span class="text-muted">—</span>';
  return `<a href="${esc(url)}" target="_blank" rel="noopener" class="product-link" title="${esc(url)}">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
    Amazon
  </a>`;
}

// Dashboard table
function renderDashboardTable() {
  const tbody = document.getElementById('dashboard-table');
  tbody.innerHTML = products.slice(0, 10).map(p => `
    <tr>
      <td><strong>${esc(p.name)}</strong></td>
      <td>${esc(p.category)}</td>
      <td>$${Number(p.price_usd).toFixed(2)}</td>
      <td>${scoreBar(p.curation_score)}</td>
      <td>${statusBadge(p.status)}</td>
    </tr>
  `).join('');
}

// Products table
function renderProductsTable() {
  const tbody = document.getElementById('products-table');
  tbody.innerHTML = products.map(p => `
    <tr>
      <td><strong>${esc(p.name)}</strong></td>
      <td>${esc(p.category)}</td>
      <td>$${Number(p.price_usd).toFixed(2)}</td>
      <td>${p.competitor_reviews}</td>
      <td>${Number(p.competitor_rating).toFixed(1)}</td>
      <td>${p.demand_score}/10</td>
      <td>${scoreBar(p.curation_score)}</td>
      <td>${statusBadge(p.status)}</td>
      <td>${productLink(p.url)}</td>
      <td>
        <div class="actions">
          ${p.copy_data ? `<button class="btn btn-sm btn-ghost" onclick="viewCopy('${esc(p.name)}')">Ver Copy</button>` : ''}
          <button class="btn btn-sm btn-ghost" onclick="resetProduct('${esc(p.name)}')">Reset</button>
          <button class="btn btn-sm btn-danger" onclick="deleteProduct('${esc(p.name)}')">Excluir</button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Listings
function renderListings() {
  const container = document.getElementById('listings-container');
  const empty = document.getElementById('listings-empty');

  if (!listings.length) {
    container.innerHTML = '';
    empty.hidden = false;
    return;
  }

  empty.hidden = true;
  container.innerHTML = listings.map((l, i) => {
    const listing = l.listing || {};
    return `
      <div class="listing-card">
        <div class="listing-card-header" onclick="toggleListing(${i})">
          <h3>${esc(l.product_name)}</h3>
          <div class="listing-meta">
            <span>${esc(l.category)}</span>
            <span>$${Number(l.price_usd).toFixed(2)}</span>
            <span>Score: ${l.curation_score}</span>
          </div>
        </div>
        <div class="listing-body" id="listing-body-${i}" hidden>
          <div class="listing-section">
            <div class="listing-section-label">Título</div>
            <div class="listing-title">${esc(listing.title || '')}</div>
          </div>
          <div class="listing-section">
            <div class="listing-section-label">Bullet Points</div>
            <ul class="listing-bullets">
              ${(listing.bullets || []).map(b => `<li>${esc(b)}</li>`).join('')}
            </ul>
          </div>
          <div class="listing-section">
            <div class="listing-section-label">Descrição</div>
            <div class="listing-description">${esc(listing.description || '')}</div>
          </div>
          <div class="listing-section">
            <div class="listing-section-label">Backend Keywords</div>
            <div class="listing-keywords">${esc(listing.backend_keywords || '')}</div>
          </div>
        </div>
      </div>`;
  }).join('');
}

function toggleListing(i) {
  const el = document.getElementById('listing-body-' + i);
  el.hidden = !el.hidden;
}

// View copy in modal
function viewCopy(name) {
  const product = products.find(p => p.name === name);
  if (!product || !product.copy_data) return;

  const copy = JSON.parse(product.copy_data);
  document.getElementById('modal-title').textContent = name;
  document.getElementById('modal-body').innerHTML = `
    <div class="listing-section">
      <div class="listing-section-label">Título</div>
      <div class="listing-title">${esc(copy.title || '')}</div>
    </div>
    <div class="listing-section">
      <div class="listing-section-label">Bullet Points</div>
      <ul class="listing-bullets">
        ${(copy.bullets || []).map(b => `<li>${esc(b)}</li>`).join('')}
      </ul>
    </div>
    <div class="listing-section">
      <div class="listing-section-label">Descrição</div>
      <div class="listing-description">${esc(copy.description || '')}</div>
    </div>
    <div class="listing-section">
      <div class="listing-section-label">Backend Keywords</div>
      <div class="listing-keywords">${esc(copy.backend_keywords || '')}</div>
    </div>`;
  document.getElementById('modal-overlay').hidden = false;
}

function closeModal() {
  document.getElementById('modal-overlay').hidden = true;
}

document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeModal();
});

// Switch to pipeline page and show console
function showPipelinePage() {
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.querySelector('[data-page="pipeline"]').classList.add('active');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById('page-pipeline').classList.add('active');
}

function renderLog(consoleEl, log) {
  consoleEl.innerHTML = (log || []).map(line => {
    let cls = 'console-line';
    if (line.includes('ERRO')) cls += ' error';
    else if (line.includes('OK:') || line.includes('Conclu')) cls += ' success';
    else if (line.includes('Iniciando') || line.includes('===')) cls += ' info';
    return `<p class="${cls}">${esc(line)}</p>`;
  }).join('');
}

// Filter: research + curation only
async function runFilter() {
  const btn = document.getElementById('btn-filter');
  const consoleEl = document.getElementById('console');
  showPipelinePage();

  btn.disabled = true;
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Filtrando...`;
  consoleEl.innerHTML = '<p class="console-line info">Importando e filtrando produtos...</p>';

  const steps = ['research', 'curation', 'copy', 'publish'];
  steps.forEach(s => document.getElementById('step-' + s).classList.remove('running', 'done'));
  document.getElementById('step-research').classList.add('running');

  try {
    const result = await postJSON('/api/run-filter');

    document.getElementById('step-research').classList.replace('running', 'done');
    document.getElementById('step-curation').classList.add('done');

    renderLog(consoleEl, result.log);
    toast('Filtragem concluída! Revise os produtos e clique em "Gerar Copys".', 'success');
    await loadAll();
  } catch (err) {
    consoleEl.innerHTML += `<p class="console-line error">Erro: ${esc(err.message)}</p>`;
    toast('Erro ao filtrar produtos.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg> Filtrar Produtos`;
  }
}

// Copy generation + export
async function runCopy() {
  const btn = document.getElementById('btn-copy');
  const consoleEl = document.getElementById('console');
  showPipelinePage();

  btn.disabled = true;
  btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Gerando...`;
  consoleEl.innerHTML = '<p class="console-line info">Gerando copys com IA (pode demorar)...</p>';

  const steps = ['research', 'curation', 'copy', 'publish'];
  steps.forEach(s => document.getElementById('step-' + s).classList.remove('running', 'done'));
  document.getElementById('step-research').classList.add('done');
  document.getElementById('step-curation').classList.add('done');
  document.getElementById('step-copy').classList.add('running');

  try {
    const result = await postJSON('/api/run-copy');

    document.getElementById('step-copy').classList.replace('running', 'done');
    document.getElementById('step-publish').classList.add('done');

    renderLog(consoleEl, result.log);
    toast('Copys geradas e exportadas com sucesso!', 'success');
    await loadAll();
  } catch (err) {
    consoleEl.innerHTML += `<p class="console-line error">Erro: ${esc(err.message)}</p>`;
    toast('Erro ao gerar copys.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg> Gerar Copys`;
  }
}

// Reset product
async function resetProduct(name) {
  if (!confirm(`Reprocessar "${name}"? O produto voltará ao status "pesquisado".`)) return;
  await postJSON('/api/reset', { name });
  toast(`"${name}" resetado.`, 'info');
  await loadAll();
}

// Delete product
async function deleteProduct(name) {
  if (!confirm(`Excluir "${name}" permanentemente?`)) return;
  await postJSON('/api/delete', { name });
  toast(`"${name}" excluído.`, 'info');
  await loadAll();
}

// Toast
function toast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// Escape HTML
function esc(str) {
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

// Init
loadAll();
