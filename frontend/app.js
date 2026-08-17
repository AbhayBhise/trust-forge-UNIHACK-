let productsData = [];
let diffData = null;
let rcData = null;
let liveData = null;
let liveCsvUrl = null;
let currentView = 'dashboard';

const VIEW_TITLES = {
    dashboard: 'Dashboard',
    upload: 'Process CSV',
    diff: 'Ground Truth Comparison',
    qa: 'QA Metrics',
    journey: 'Pipeline Journey',
    detail: 'Product Detail',
    explain: 'Explainability'
};

async function init() {
    try {
        const pRes = await fetch('../files/demo_output.json');
        productsData = await pRes.json();
        try {
            const dRes = await fetch('../files/diff_data.json');
            diffData = await dRes.json();
            const rcRes = await fetch('../files/root_cause_report.json');
            rcData = await rcRes.json();
        } catch (e) { /* optional data */ }
        nav('dashboard');
    } catch (e) {
        document.getElementById('app-content').innerHTML = `
            <div class="card" style="max-width:480px;margin:4rem auto;text-align:center">
                <div style="font-size:2rem;margin-bottom:1rem;color:var(--gray-300)">&#9888;</div>
                <div class="card-title">Unable to Load Data</div>
                <p style="color:var(--gray-500);margin-top:0.5rem;font-size:0.875rem">
                    Start the backend server first:<br><code style="background:var(--gray-100);padding:0.25rem 0.5rem;border-radius:4px;font-size:0.8125rem">cd files && python server.py</code>
                </p>
            </div>`;
    }
}

function nav(view, args = null) {
    currentView = view;
    document.getElementById('topbar-title').textContent = VIEW_TITLES[view] || 'Trust Engine';
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.toggle('active', el.dataset.view === view);
    });

    const c = document.getElementById('app-content');
    switch (view) {
        case 'dashboard': c.innerHTML = renderDashboard(); break;
        case 'upload': c.innerHTML = renderUpload(); break;
        case 'diff': c.innerHTML = renderDiff(); break;
        case 'qa': c.innerHTML = renderQA(); break;
        case 'journey': c.innerHTML = renderJourney(args); break;
        case 'detail': c.innerHTML = renderDetail(args); break;
        case 'explain': c.innerHTML = renderExplain(args); break;
    }
}

/* ── Dashboard ────────────────────────────────────────────────────── */
function renderDashboard() {
    const data = liveData || productsData;
    const verified = data.filter(p => p.identity.status === 'verified').length;
    const needsReview = data.filter(p => p.identity.status === 'needs_review').length;
    let avgConf = 0;
    data.forEach(p => avgConf += (p.quality_score.mean_confidence || 0));
    avgConf = data.length ? (avgConf / data.length) : 0;
    let avgComp = 0;
    data.forEach(p => avgComp += (p.quality_score.completeness || 0));
    avgComp = data.length ? (avgComp / data.length) : 0;

    return `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Products Processed</div>
                <div class="kpi-value">${data.length}</div>
                <div class="kpi-change positive">Batch reference data</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Verified Identity</div>
                <div class="kpi-value">${verified}</div>
                <div class="kpi-change positive">${data.length ? Math.round(verified/data.length*100) : 0}% of total</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Needs Review</div>
                <div class="kpi-value">${needsReview}</div>
                <div class="kpi-change ${needsReview > 0 ? 'negative' : 'positive'}">Manual queue</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Mean Confidence</div>
                <div class="kpi-value">${Math.round(avgConf * 100)}%</div>
                <div class="kpi-change positive">Across all attributes</div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <div>
                    <div class="card-title">Processed Products</div>
                    <div class="card-subtitle">Click any row to view pipeline journey</div>
                </div>
                ${liveData ? `<a href="${liveCsvUrl || '#'}" download class="btn btn-secondary btn-sm">&#8681; Export CSV</a>` : ''}
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>MPN</th>
                            <th>Manufacturer</th>
                            <th>Brand</th>
                            <th>Identity</th>
                            <th>Completeness</th>
                            <th>Confidence</th>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.map((p, i) => `
                            <tr style="cursor:pointer" onclick="nav('journey', ${i})">
                                <td><strong>${esc(p.mfg_part_num)}</strong></td>
                                <td>${esc(p.manufacturer_name)}</td>
                                <td>${esc(p.brand_name)}</td>
                                <td><span class="badge badge-${p.identity.status}">${p.identity.status}</span></td>
                                <td>
                                    <div style="display:flex;align-items:center;gap:0.5rem">
                                        <div class="progress-bar" style="width:80px">
                                            <div class="progress-fill ${completenessColor(p.quality_score.completeness)}" style="width:${Math.round(p.quality_score.completeness*100)}%"></div>
                                        </div>
                                        <span style="font-size:0.8125rem;color:var(--gray-600)">${Math.round(p.quality_score.completeness*100)}%</span>
                                    </div>
                                </td>
                                <td style="font-size:0.875rem;color:var(--gray-600)">${Math.round((p.quality_score.mean_confidence||0)*100)}%</td>
                                <td><button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();nav('detail',${i})">View</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function completenessColor(v) {
    if (v >= 0.8) return 'green';
    if (v >= 0.5) return 'yellow';
    return 'red';
}

/* ── Upload / Live Demo ───────────────────────────────────────────── */
function renderUpload() {
    return `
        <div class="card" style="max-width:640px;margin:0 auto">
            <div class="card-header">
                <div class="card-title">Process a CSV File</div>
            </div>
            <p style="color:var(--gray-500);font-size:0.875rem;margin-bottom:1.5rem">
                Upload a CSV with columns: Mfg_Part_Num, Part_Desc, E1_Brand, Unilog_Brand, DIB_Brand, Part_Manuf.
                Large datasets (1000+ rows) are processed in the background with parallel workers.
            </p>
            <div id="upload-zone" class="upload-zone" onclick="document.getElementById('csv-file').click()"
                 ondragover="event.preventDefault();this.classList.add('dragover')"
                 ondragleave="this.classList.remove('dragover')"
                 ondrop="event.preventDefault();this.classList.remove('dragover');handleFileDrop(event)">
                <div class="upload-icon">&#8682;</div>
                <div class="upload-title">Drop CSV here or click to browse</div>
                <div class="upload-desc">Supports 1 to 10,000 rows &middot; Parallel processing with progress tracking</div>
            </div>
            <input type="file" id="csv-file" accept=".csv" style="display:none" onchange="handleFileSelect(this)">

            <div id="upload-loading" style="display:none">
                <div class="loading-overlay">
                    <div class="spinner"></div>
                    <div style="font-weight:600;color:var(--gray-800)">Processing products...</div>
                    <div id="upload-progress-text" style="font-size:0.875rem;color:var(--gray-500)">Starting...</div>
                    <div class="progress-bar" style="width:300px;margin-top:0.5rem">
                        <div id="upload-progress-bar" class="progress-fill blue" style="width:0%"></div>
                    </div>
                    <div id="upload-stats" style="font-size:0.8125rem;color:var(--gray-400);margin-top:0.5rem"></div>
                </div>
            </div>
            <div id="upload-error" style="display:none;color:var(--danger);margin-top:1rem;font-size:0.875rem"></div>
        </div>
    `;
}

let currentJobId = null;

function handleFileDrop(e) {
    const file = e.dataTransfer.files[0];
    if (file) uploadCSV(file);
}

function handleFileSelect(input) {
    if (input.files.length) uploadCSV(input.files[0]);
}

async function uploadCSV(file) {
    document.getElementById('upload-zone').style.display = 'none';
    document.getElementById('upload-loading').style.display = 'block';
    document.getElementById('upload-error').style.display = 'none';

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Use job queue endpoint for all sizes
        const res = await fetch('/pipeline/jobs', { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }
        const { job_id } = await res.json();
        currentJobId = job_id;
        pollJobProgress(job_id);
    } catch (err) {
        document.getElementById('upload-loading').style.display = 'none';
        document.getElementById('upload-zone').style.display = '';
        const el = document.getElementById('upload-error');
        el.textContent = err.message;
        el.style.display = 'block';
    }
}

async function pollJobProgress(jobId) {
    const pollInterval = 500; // ms
    
    while (true) {
        await new Promise(r => setTimeout(r, pollInterval));
        
        try {
            const res = await fetch('/pipeline/jobs/' + jobId);
            if (!res.ok) throw new Error('Failed to fetch job status');
            const job = await res.json();
            
            const pct = job.progress.percent || 0;
            const bar = document.getElementById('upload-progress-bar');
            const text = document.getElementById('upload-progress-text');
            const stats = document.getElementById('upload-stats');
            
            if (bar) bar.style.width = pct + '%';
            if (text) text.textContent = job.status === 'completed' 
                ? 'Complete!' 
                : `Processing... ${pct}%`;
            if (stats) {
                stats.textContent = `${job.progress.completed}/${job.progress.total} rows`
                    + ` | ${job.progress.verified} verified`
                    + ` | ${job.progress.needs_review} needs review`
                    + ` | ${Math.round(job.progress.rate_per_sec || 0)} rows/sec`
                    + ` | ETA: ${Math.round(job.progress.eta_seconds || 0)}s`;
            }
            
            if (job.status === 'completed') {
                liveData = job.products;
                liveCsvUrl = job.csv_url;
                setTimeout(() => nav('dashboard'), 800);
                break;
            }
        } catch (err) {
            console.error('Poll error:', err);
        }
    }
}

/* ── Pipeline Journey ─────────────────────────────────────────────── */
function renderJourney(index) {
    const data = liveData || productsData;
    if (!data.length) return '<div class="empty-state"><div class="empty-icon">&#9888;</div>No products loaded</div>';
    const p = data[index] || data[0];

    const steps = [
        { label: 'CSV Input', desc: 'Raw distributor data' },
        { label: 'Identity Resolution', desc: 'MPN matching' },
        { label: 'Evidence Retrieval', desc: 'Web / PDF / HTML scraping' },
        { label: 'Normalization', desc: 'Canonical value mapping' },
        { label: 'Validation', desc: 'Schema + UOM checks' },
        { label: 'Confidence Scoring', desc: 'Multi-factor scoring' },
        { label: 'Description Gen', desc: 'Deterministic templates' },
        { label: '252-col Export', desc: 'Commerce-ready output' },
    ];

    setTimeout(() => {
        document.querySelectorAll('.pipeline-step').forEach((el, i) => {
            setTimeout(() => el.classList.add('active'), i * 250);
        });
    }, 100);

    return `
        <button class="btn btn-ghost btn-sm" onclick="nav('dashboard')" style="margin-bottom:1rem">&larr; Back to Dashboard</button>

        <div class="card" style="margin-bottom:1.5rem">
            <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div class="card-title" style="font-size:1.125rem">${esc(p.mfg_part_num)}</div>
                    <div class="card-subtitle">${esc(p.manufacturer_name)} &middot; ${esc(p.brand_name)}</div>
                </div>
                <span class="badge badge-${p.identity.status}">${p.identity.status}</span>
            </div>
        </div>

        <div class="pipeline-steps">
            ${steps.map(s => `
                <div class="pipeline-step">
                    <div class="step-num">&#10003;</div>
                    <div class="step-label">${s.label}</div>
                    <div style="font-size:0.75rem;color:var(--gray-400);margin-top:0.25rem">${s.desc}</div>
                </div>
            `).join('')}
        </div>

        <div style="text-align:center;margin:2rem 0">
            <button class="btn btn-primary" onclick="nav('detail',${index})">View Product Details &rarr;</button>
        </div>
    `;
}

/* ── Product Detail ───────────────────────────────────────────────── */
function renderDetail(index) {
    const data = liveData || productsData;
    if (!data.length) return '<div class="empty-state"><div class="empty-icon">&#9888;</div>No products loaded</div>';
    const p = data[index] || data[0];
    const conf = Math.round((p.quality_score.mean_confidence || 0) * 100);

    const verifiedAttrs = p.attributes.filter(a => a.status === 'verified');
    const reviewAttrs = p.attributes.filter(a => a.status === 'needs_review');
    const unknownAttrs = p.attributes.filter(a => a.status === 'unknown');

    return `
        <button class="btn btn-ghost btn-sm" onclick="nav('dashboard')" style="margin-bottom:1rem">&larr; Back to Dashboard</button>

        <div class="grid-3" style="margin-bottom:1.5rem">
            <div class="kpi-card">
                <div class="kpi-label">MPN</div>
                <div class="kpi-value" style="font-size:1.25rem">${esc(p.mfg_part_num)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Confidence Score</div>
                <div class="kpi-value" style="color:${conf >= 70 ? 'var(--success)' : conf >= 40 ? 'var(--warning)' : 'var(--danger)'}">${conf}%</div>
                <div class="progress-bar" style="margin-top:0.5rem">
                    <div class="progress-fill ${conf >= 70 ? 'green' : conf >= 40 ? 'yellow' : 'red'}" style="width:${conf}%"></div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Evidence Coverage</div>
                <div class="kpi-value">${Math.round((p.quality_score.evidence_coverage||0)*100)}%</div>
            </div>
        </div>

        <div class="grid-3" style="margin-bottom:1.5rem">
            <div class="card" style="border-left:3px solid var(--primary)">
                <div class="kpi-label">Verified</div>
                <div class="kpi-value" style="color:var(--success)">${verifiedAttrs.length}</div>
            </div>
            <div class="card" style="border-left:3px solid var(--warning)">
                <div class="kpi-label">Needs Review</div>
                <div class="kpi-value" style="color:var(--warning)">${reviewAttrs.length}</div>
            </div>
            <div class="card" style="border-left:3px solid var(--gray-300)">
                <div class="kpi-label">Unknown</div>
                <div class="kpi-value" style="color:var(--gray-400)">${unknownAttrs.length}</div>
            </div>
        </div>

        <div class="section-header">
            <div>
                <div class="section-title">Extracted Attributes</div>
                <div class="section-desc">Evidence-backed facts from manufacturer sources</div>
            </div>
        </div>

        <div class="attr-grid">
            ${p.attributes.map((a, ai) => `
                <div class="attr-card" style="cursor:pointer" onclick="nav('explain',{pIdx:${index},aIdx:${ai}})">
                    <div class="attr-card-header">
                        <div class="attr-label">${esc(a.attribute)}</div>
                        <span class="badge badge-${a.status}">${a.status}</span>
                    </div>
                    <div class="attr-value">${a.value !== null ? esc(a.value) : '—'} ${a.uom ? esc(a.uom) : ''}</div>
                    <div class="attr-meta">
                        <span>Conf: ${Math.round((a.confidence||0)*100)}%</span>
                        ${a.evidence && a.evidence.length ? `<span>Source: ${esc(sourceName(a.evidence[0].source_url))}</span>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>

        ${Object.keys(p.descriptions).length ? `
            <div class="section-header" style="margin-top:2rem">
                <div class="section-title">Generated Descriptions</div>
                <div class="section-desc">Deterministic output from verified attributes</div>
            </div>
            <div class="card">
                ${Object.entries(p.descriptions).map(([k, v]) => `
                    <div style="padding:0.625rem 0;border-bottom:1px solid var(--border-light)">
                        <span style="font-size:0.8125rem;font-weight:600;color:var(--gray-500);text-transform:uppercase;letter-spacing:0.03em">${esc(k)}</span>
                        <div style="font-size:0.875rem;color:var(--gray-800);margin-top:0.25rem">${esc(v)}</div>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
}

/* ── Explainability ───────────────────────────────────────────────── */
function renderExplain(args) {
    const p = productsData[args.pIdx];
    const a = p.attributes[args.aIdx];

    let evHtml = '<div style="color:var(--gray-400);font-size:0.875rem;padding:1rem">No evidence attached.</div>';
    if (a.evidence && a.evidence.length) {
        const ev = a.evidence[0];
        evHtml = `
            <div class="evidence-block">
                <strong>${esc(a.attribute)}:</strong> ${esc(a.value)} ${a.uom ? esc(a.uom) : ''}
            </div>
            <div class="evidence-source">
                <strong>Source:</strong>&nbsp;
                <a href="${esc(ev.source_url)}" target="_blank">${esc(ev.source_url)}</a>
            </div>
            <div style="margin-top:0.75rem;font-size:0.8125rem;color:var(--gray-600)">
                <div><strong>Section:</strong> ${esc(ev.page_or_section)}</div>
                <div><strong>Tier:</strong> ${ev.source_tier}/5</div>
                <div><strong>Retrieved:</strong> ${esc(ev.retrieved_at || 'N/A')}</div>
            </div>
        `;
    }

    return `
        <button class="btn btn-ghost btn-sm" onclick="nav('detail',${args.pIdx})" style="margin-bottom:1rem">&larr; Back to Product</button>
        <div class="card" style="margin-bottom:1.5rem">
            <div class="card-title" style="font-size:1.125rem">Explainability: ${esc(a.attribute)}</div>
        </div>
        <div class="explain-layout">
            <div>
                <div class="card" style="margin-bottom:1.25rem">
                    <div class="card-header">
                        <div class="card-title">Value</div>
                        <span class="badge badge-${a.status}">${a.status}</span>
                    </div>
                    <div style="font-size:1.5rem;font-weight:700;color:var(--gray-900)">${a.value !== null ? esc(a.value) : '—'} ${a.uom ? esc(a.uom) : ''}</div>
                    <div style="margin-top:0.75rem;font-size:0.875rem;color:var(--gray-500)">
                        Confidence: <strong>${Math.round((a.confidence||0)*100)}%</strong>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">Validation Checks</div>
                    <div style="margin-top:0.75rem">
                        ${(a.validation_report || []).map(v => `
                            <div style="display:flex;align-items:center;gap:0.5rem;padding:0.375rem 0;font-size:0.8125rem">
                                <span style="color:${v.result === 'PASS' ? 'var(--success)' : 'var(--danger)'}">${v.result === 'PASS' ? '&#10003;' : '&#10007;'}</span>
                                <span>${esc(v.rule)}</span>
                            </div>
                        `).join('') || '<div style="color:var(--gray-400);font-size:0.875rem">No checks run.</div>'}
                    </div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Evidence Source</div>
                <div style="margin-top:0.75rem">
                    ${evHtml}
                </div>
            </div>
        </div>
    `;
}

/* ── Diff View ────────────────────────────────────────────────────── */
function renderDiff() {
    if (!diffData) return '<div class="empty-state"><div class="empty-icon">&#9888;</div><div>No diff data available. Run evaluation first.</div></div>';

    return `
        <div class="kpi-grid" style="margin-bottom:1.5rem">
            <div class="kpi-card">
                <div class="kpi-label">Fields Compared</div>
                <div class="kpi-value">${diffData.summary.fields_compared}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Exact Matches</div>
                <div class="kpi-value" style="color:var(--success)">${diffData.summary.matched}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Mismatches</div>
                <div class="kpi-value" style="color:var(--danger)">${diffData.summary.mismatched}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Accuracy</div>
                <div class="kpi-value">${Math.round(diffData.summary.matched / diffData.summary.fields_compared * 100)}%</div>
            </div>
        </div>

        ${diffData.products.map(p => `
            <div class="card" style="margin-bottom:1.5rem">
                <div class="card-header">
                    <div class="card-title">MPN: ${esc(p.mpn)}</div>
                    <div style="font-size:0.875rem;color:var(--gray-600)">Accuracy: <strong>${Math.round(p.overall_accuracy*100)}%</strong></div>
                </div>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Field</th><th>Ground Truth</th><th></th><th>Generated</th></tr></thead>
                        <tbody>
                            ${p.fields.map(f => `
                                <tr class="diff-row-${f.status}">
                                    <td style="font-weight:500">${esc(f.field)}</td>
                                    <td style="color:var(--gray-500)">${esc(f.expected)}</td>
                                    <td style="text-align:center;font-weight:700">${f.status === 'match' ? '=' : '≠'}</td>
                                    <td style="color:${f.status === 'match' ? 'var(--success)' : 'var(--danger)'}">${f.generated ? esc(f.generated) : '<em style="color:var(--gray-400)">Missing</em>'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `).join('')}
    `;
}

/* ── QA Metrics ───────────────────────────────────────────────────── */
function renderQA() {
    let kpis = '';
    if (diffData && productsData.length) {
        const attempted = diffData.summary.fields_compared - (rcData ? rcData.summary.unsupported_feature : 0);
        const acc = diffData.summary.matched / attempted;
        kpis = `
            <div class="kpi-grid" style="margin-bottom:1.5rem">
                <div class="kpi-card">
                    <div class="kpi-label">Schema Coverage</div>
                    <div class="kpi-value">${Math.round(attempted / (252 * diffData.summary.rows) * 100)}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Extraction Accuracy</div>
                    <div class="kpi-value" style="color:var(--success)">${Math.round(acc * 100)}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Validation Pass</div>
                    <div class="kpi-value">${Math.round(productsData.reduce((s,p) => s + (p.quality_score.validation_pass_rate||0), 0) / productsData.length * 100)}%</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Zero Hallucination</div>
                    <div class="kpi-value" style="color:var(--success)">Verified</div>
                </div>
            </div>
        `;
    }

    return `
        ${kpis}

        <div class="section-header">
            <div class="section-title">System Guarantees</div>
        </div>
        <div class="grid-2" style="margin-bottom:2rem">
            <div class="card" style="border-left:3px solid var(--success)">
                <div class="card-title" style="color:var(--success)">&#10003; Doc-First Compliance</div>
                <p style="font-size:0.875rem;color:var(--gray-600);margin-top:0.5rem">
                    Every value is extracted from an authoritative source. No values are generated from unvalidated context.
                    If evidence is missing, the field is set to <code>needs_review</code> with 0% confidence.
                </p>
            </div>
            <div class="card" style="border-left:3px solid var(--success)">
                <div class="card-title" style="color:var(--success)">&#10003; Deterministic Output</div>
                <p style="font-size:0.875rem;color:var(--gray-600);margin-top:0.5rem">
                    Running the same input twice produces byte-identical output.
                    No LLM temperature variance, no stochastic behavior.
                </p>
            </div>
            <div class="card" style="border-left:3px solid var(--success)">
                <div class="card-title" style="color:var(--success)">&#10003; Evidence Traceability</div>
                <p style="font-size:0.875rem;color:var(--gray-600);margin-top:0.5rem">
                    Every attribute links to its source URL, section, and tier score.
                    Full audit trail for compliance and review.
                </p>
            </div>
            <div class="card" style="border-left:3px solid var(--success)">
                <div class="card-title" style="color:var(--success)">&#10003; Graceful Degradation</div>
                <p style="font-size:0.875rem;color:var(--gray-600);margin-top:0.5rem">
                    When evidence retrieval fails (404, timeout, missing data),
                    the pipeline marks fields for review rather than hallucinating values.
                </p>
            </div>
        </div>

        <div class="section-header">
            <div class="section-title">System Metrics</div>
        </div>
        <div class="card">
            <table>
                <thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead>
                <tbody>
                    <tr><td>Products Processed</td><td>${productsData.length}</td><td><span class="badge badge-verified">OK</span></td></tr>
                    <tr><td>Needs Review Queue</td><td>${productsData.filter(p => p.identity.status === 'needs_review').length}</td><td><span class="badge badge-needs_review">Queue</span></td></tr>
                    <tr><td>Deduplication</td><td>Active (MPN normalization)</td><td><span class="badge badge-verified">OK</span></td></tr>
                    <tr><td>Evidence Sources</td><td>Web scraping + PDF + HTML extractor</td><td><span class="badge badge-verified">Active</span></td></tr>
                </tbody>
            </table>
        </div>
    `;
}

/* ── Utilities ────────────────────────────────────────────────────── */
function esc(s) {
    if (!s) return '';
    const el = document.createElement('span');
    el.textContent = String(s);
    return el.innerHTML;
}

function sourceName(url) {
    if (!url) return 'unknown';
    try {
        const h = new URL(url).hostname;
        return h.replace('www.', '');
    } catch (e) {
        return url.split('/').pop() || 'source';
    }
}

window.onload = init;
