# -*- coding: utf-8 -*-
"""app.py — AI 数字员工平台主应用（编排层：RAG + CRM 读写）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import os
import requests
import integrations.rag_client as rag_client
import integrations.crm_store as crm_store
import integrations.crm_writer as crm_writer

app = FastAPI(title="AI 数字员工平台")

# 项目2 获客矩阵服务地址（容器内经 host.docker.internal 访问宿主上运行的服务）
ACQUIRE_API_URL = os.getenv("ACQUIRE_API_URL", "http://host.docker.internal:8001")

HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>AI 数字员工平台 · 全屋定制出海</title>
<style>
:root{--bg:#f5f7fb;--panel:#fff;--border:#e5e9f0;--text:#1a2332;--muted:#6b7785;--brand:#1e6fff;--brand-soft:#eaf1ff;--green:#16a34a;--green-soft:#e8f7ee;--amber:#d97706;--amber-soft:#fef3e2;--red:#dc2626;--red-soft:#fde8e8;--gray-soft:#f1f3f5;--shadow:0 1px 3px rgba(0,0,0,.05)}
*{box-sizing:border-box}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;padding:24px;background:var(--bg);color:var(--text);font-size:15px;line-height:1.55}
.container{max-width:1280px;margin:0 auto}
.topbar{display:flex;align-items:center;justify-content:space-between;background:var(--panel);padding:16px 24px;border-radius:12px;box-shadow:var(--shadow);margin-bottom:20px;flex-wrap:wrap;gap:12px}
.brand{font-size:20px;font-weight:700}.brand em{font-style:normal;color:var(--brand);font-weight:600;margin-left:6px;font-size:15px}
.tags{display:flex;gap:8px;flex-wrap:wrap}
.tag{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:var(--gray-soft);border-radius:20px;font-size:12px;color:var(--muted)}
.tag b{color:var(--green);font-weight:600}.tag.brand{background:var(--brand-soft);color:var(--brand)}
.grid{display:grid;grid-template-columns:1fr 1.2fr;gap:20px}
@media (max-width:1000px){.grid{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:22px;box-shadow:var(--shadow)}
.card h2{margin:0 0 14px;font-size:16px;font-weight:700;display:flex;align-items:center;gap:8px}
.card h2::before{content:'';width:4px;height:16px;background:var(--brand);border-radius:2px}
.card-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;gap:12px}
.card-h h2{margin:0}
.btn-dl{padding:7px 14px;font-size:13px;font-weight:600;background:#fff;color:var(--text);
  border:1px solid var(--border);border-radius:7px;cursor:pointer;white-space:nowrap}
.btn-dl:hover{background:var(--panel-2,#f7f7f5);border-color:#9ca3af}
.btn-dl:disabled{opacity:.55;cursor:default}
.qbar{display:flex;gap:8px;margin-bottom:14px}
.qbar input{flex:1;padding:11px 14px;font-size:14px;border:1px solid var(--border);border-radius:8px;outline:none;transition:border-color .15s}
.qbar input:focus{border-color:var(--brand)}
.qbar button{padding:11px 22px;font-size:14px;font-weight:600;background:var(--brand);color:#fff;border:none;border-radius:8px;cursor:pointer;transition:opacity .15s}
.qbar button:hover{opacity:.9}.qbar button:disabled{opacity:.5;cursor:wait}
.answer{background:var(--brand-soft);padding:16px;border-radius:8px;white-space:pre-wrap;min-height:64px;line-height:1.6;font-size:14px}
.answer.loading{color:var(--muted);font-style:italic}
.sources{margin-top:12px;font-size:13px;color:var(--muted);line-height:1.8}
.chip{display:inline-block;padding:3px 10px;margin:2px 4px 0 0;background:var(--gray-soft);color:var(--text);border-radius:12px;font-size:12px;font-family:Menlo,Consolas,monospace}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}
.stat{padding:10px 8px;border-radius:8px;text-align:center;background:var(--gray-soft)}
.stat .n{font-size:20px;font-weight:700;color:var(--text);display:block}
.stat .l{font-size:11px;color:var(--muted);margin-top:2px;letter-spacing:.5px}
.stat.new{background:var(--brand-soft)}.stat.new .n{color:var(--brand)}
.stat.contacted{background:var(--amber-soft)}.stat.contacted .n{color:var(--amber)}
.stat.won{background:var(--green-soft)}.stat.won .n{color:var(--green)}
.stat.lost{background:var(--red-soft)}.stat.lost .n{color:var(--red)}
.tablewrap{overflow-x:auto;max-height:520px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{background:var(--gray-soft);font-weight:600;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.5px;position:sticky;top:0}
tbody tr:hover td{background:#fafbfc}
.badge{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.badge.new{background:var(--brand-soft);color:var(--brand)}
.badge.contacted{background:var(--amber-soft);color:var(--amber)}
.badge.won{background:var(--green-soft);color:var(--green)}
.badge.lost{background:var(--red-soft);color:var(--red)}
select{padding:4px 8px;font-size:12px;border:1px solid var(--border);border-radius:6px;background:#fff;cursor:pointer}
.intent{color:var(--muted);font-size:12px;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle}
.toast{position:fixed;bottom:24px;right:24px;background:var(--green);color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;opacity:0;transition:opacity .2s;box-shadow:0 4px 14px rgba(0,0,0,.15);pointer-events:none}
.toast.show{opacity:1}
.empty{color:var(--muted);font-size:13px;text-align:center;padding:24px 0}
.acq-bar{display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap}
.acq-run{padding:11px 22px;font-size:14px;font-weight:600;background:var(--brand);color:#fff;border:none;border-radius:8px;cursor:pointer}
.acq-run:disabled{opacity:.5;cursor:wait}
.acq-status{font-size:13px;color:var(--muted)}
.acq-posts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:6px 0 4px}
.post{border:1px solid var(--border);border-radius:8px;padding:12px;background:var(--gray-soft)}
.post-h{font-weight:700;color:var(--brand);font-size:13px;margin-bottom:6px}
.post-b{font-size:13px;line-height:1.5}
.acq-leads{margin-top:12px}
.acq-leads table{margin-top:8px}
.draft{font-size:12px;line-height:1.5;max-width:440px}
.acq-hr{border:none;border-top:1px solid var(--border);margin:18px 0}
.acq-inbox-h{font-weight:600;font-size:13px;margin-bottom:8px}
.acq-inbox-row{display:flex;gap:8px;flex-wrap:wrap}
.acq-inbox-row input{padding:9px 12px;font-size:13px;border:1px solid var(--border);border-radius:8px;outline:none}
.acq-inbox-row input:nth-child(3){flex:1;min-width:240px}
@media (max-width:1000px){.acq-posts{grid-template-columns:1fr}}
.crawl-bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.crawl-bar input{padding:9px 12px;font-size:13px;border:1px solid var(--border);border-radius:8px;outline:none}
.crawl-bar input.query{flex:1;min-width:200px}
.crawl-bar input.limit{width:80px}
.crawl-run{padding:9px 18px;font-size:13px;font-weight:600;background:#7c3aed;color:#fff;border:none;border-radius:8px;cursor:pointer}
.crawl-run:disabled{opacity:.5;cursor:wait}
.crawl-status{font-size:12px;color:var(--muted)}
.crawl-sources{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:12px}
.crawl-chip{padding:4px 10px;border-radius:12px;background:var(--gray-soft);color:var(--muted)}
.crawl-chip.on{background:#ede9fe;color:#6d28d9;font-weight:600}
.crawl-chip.off{background:#fef2f2;color:#b91c1c}
.crawl-fetched{border:1px solid var(--border);border-radius:8px;padding:12px;background:#faf8ff;margin-top:10px}
.crawl-fetched-h{font-weight:700;color:#6d28d9;font-size:13px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}
.crawl-fetched table{font-size:12px}
.crawl-fetched th{font-size:10px}
.crawl-fetched td{padding:6px 8px}
.crawl-src{display:inline-block;padding:2px 7px;border-radius:8px;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.crawl-src.Apollo\\.io{background:#e0f2fe;color:#0369a1}
.crawl-src.Hunter\\.io{background:#fef3c7;color:#92400e}
.crawl-src.Curated{background:#ede9fe;color:#6d28d9}
</style>
</head>
<body>
<div class="container">
  <div class="topbar">
    <div class="brand">🚢 AI 数字员工平台<em>全屋定制出海</em></div>
    <div class="tags">
      <span class="tag brand">📦 Docker 运行中</span>
      <span class="tag">📚 RAG <b>已连接</b></span>
      <span class="tag">📊 线索 <b id="leadCount">-</b></span>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>知识库问答</h2>
      <div class="qbar">
        <input id="q" placeholder="输入问题，如 What is your MOQ?" />
        <button id="askBtn" onclick="ask()">提问</button>
      </div>
      <div id="answer" class="answer">回答会显示在这里…</div>
      <div id="sources" class="sources"></div>
    </div>

    <div class="card">
      <div class="card-h">
        <h2>CRM 看板 · 海外线索实时</h2>
        <button id="dlBtn" class="btn-dl" onclick="exportCsv()">导出 CSV</button>
      </div>
      <div class="stats">
        <div class="stat new"><span class="n" id="c-new">0</span><span class="l">New</span></div>
        <div class="stat contacted"><span class="n" id="c-contacted">0</span><span class="l">Contacted</span></div>
        <div class="stat won"><span class="n" id="c-won">0</span><span class="l">Won</span></div>
        <div class="stat lost"><span class="n" id="c-lost">0</span><span class="l">Lost</span></div>
      </div>
      <div class="tablewrap">
        <table id="leads">
          <thead><tr><th>来源</th><th>联系人</th><th>公司</th><th>国家</th><th>意向产品</th><th>阶段</th><th>操作</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="card" style="margin-top:20px">
    <h2>获客矩阵智能体 · 自动获客闭环</h2>
    <div class="acq-bar">
      <button id="runBtn" class="acq-run" onclick="runAcquire()">▶ 运行获客闭环</button>
      <span id="acqStatus" class="acq-status">点「运行」触发 内容 → 运营 → 销售 三段式</span>
    </div>
    <div id="acqPosts" class="acq-posts"></div>
    <div id="acqLeads" class="acq-leads"></div>
    <hr class="acq-hr">
    <div class="crawl-section">
      <div class="acq-inbox-h">🕷 自动抓取海外线索（Apollo/Hunter/精选种子）</div>
      <div class="crawl-bar">
        <input id="cq" class="query" placeholder="搜索目标，如 custom wardrobe Texas / Dubai villa developer" />
        <input id="cl" class="limit" type="number" value="3" min="1" max="10" title="抓取条数" />
        <button id="crawlBtn" class="crawl-run" onclick="runCrawl()">🕷 自动抓取并跑闭环</button>
        <span id="crawlStatus" class="crawl-status">点击即触发 真数据源抓取 + 识别 + 接待</span>
      </div>
      <div id="crawlSources" class="crawl-sources">正在加载爬虫配置…</div>
      <div id="crawlFetched" class="crawl-fetched" style="display:none"></div>
    </div>
    <hr class="acq-hr">
    <div class="acq-inbox">
      <div class="acq-inbox-h">粘贴真实社媒消息（系统识别为线索并起草英文接待）</div>
      <div class="acq-inbox-row">
        <input id="ibSource" placeholder="来源，如 LinkedIn DM" />
        <input id="ibContact" placeholder="联系人，如 Omar" />
        <input id="ibText" placeholder="消息正文，如 We need 200 apartment wardrobes" />
        <button onclick="addInbox()">＋ 加入并重跑</button>
      </div>
    </div>
  </div>
</div>

<div id="toast" class="toast"></div>

<script>
async function ask(){
  const q=document.getElementById('q').value.trim(); if(!q) return;
  const btn=document.getElementById('askBtn'), ans=document.getElementById('answer'), src=document.getElementById('sources');
  btn.disabled=true; btn.textContent='思考中…';
  ans.className='answer loading'; ans.textContent='正在调用 RAG 检索…'; src.innerHTML='';
  try{
    const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
    const d=await r.json();
    ans.className='answer'; ans.textContent=d.answer||'(无回答)';
    const ss=d.sources||[];
    src.innerHTML=ss.length?'📎 <b>出处</b>：'+ss.map(s=>`<span class="chip">${s}</span>`).join(''):'';
  }catch(e){ans.className='answer'; ans.textContent='❌ 出错: '+e.message;}
  finally{btn.disabled=false; btn.textContent='提问';}
}

async function advance(id,stage){
  await fetch('/api/leads/advance',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lead_id:id,stage:stage})});
  toast('阶段已更新'); loadLeads();
}

function toast(m){const t=document.getElementById('toast');t.textContent='✅ '+m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),1800);}

function exportCsv(){
  const btn=document.getElementById('dlBtn');
  btn.disabled=true; const old=btn.textContent; btn.textContent='导出中…';
  const a=document.createElement('a');
  a.href='/api/leads/export'; a.download='';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(()=>{btn.disabled=false; btn.textContent=old;},1500);
  toast('CSV 已开始下载');
}

async function loadLeads(){
  try{
    const r=await fetch('/api/leads'); const d=await r.json();
    const ls=d.leads||[], st=d.stats||{};
    document.getElementById('leadCount').textContent=ls.length;
    ['new','contacted','won','lost'].forEach(s=>{document.getElementById('c-'+s).textContent=st[s]||0;});
    const tb=document.querySelector('#leads tbody'); tb.innerHTML='';
    if(!ls.length){tb.innerHTML='<tr><td colspan="7" class="empty">暂无线索</td></tr>'; return;}
    const stages=['new','contacted','won','lost'];
    ls.forEach(l=>{
      const opts=stages.map(s=>`<option value="${s}"${s===l.stage?' selected':''}>${s}</option>`).join('');
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${l.source||''}</td><td>${l.contact||''}</td><td>${l.company||''}</td><td>${l.country||''}</td><td><span class="intent" title="${l.intent||''}">${l.intent||''}</span></td><td><span class="badge ${l.stage}">${l.stage||''}</span></td><td><select onchange="advance('${l.id}',this.value)">${opts}</select></td>`;
      tb.appendChild(tr);
    });
  }catch(e){console.error(e);}
}
loadLeads();
setInterval(loadLeads,30000);

async function runAcquire(){
  const btn=document.getElementById('runBtn'), st=document.getElementById('acqStatus');
  btn.disabled=true; btn.textContent='已派发…(0%)';
  st.textContent='正在派发闭环任务到后台…';
  let taskId=null;
  try{
    // 第 1 步：派发任务，立即拿到 task_id（不应超时）
    const r=await fetch('/api/acquire/run',{method:'POST'});
    const d=await r.json();
    if(d.error){st.textContent='❌ '+d.error; return;}
    taskId=d.task_id;
    st.textContent='🚀 后台已启动，前台每 2 秒轮询…';
    // 第 2 步：每 2 秒轮询一次进度，按钮文字实时反映进度
    for(let pct=0; pct<100; ){
      await new Promise(r=>setTimeout(r,2000));
      let p; try{ p=await (await fetch('/api/acquire/task/'+taskId)).json(); }catch(_){continue;}
      if(!p || p.status==='not found'){st.textContent='❌ 任务丢失'; return;}
      pct=p.progress||0;
      const eta=p.eta_sec==null?'':('· 剩余 ≈ '+p.eta_sec+'s');
      btn.textContent=`运行中…(${pct}%)`;
      st.textContent=`🔄 [${p.step||'?'}] ${p.message||''} ${eta}`;
      if(p.status==='failed'){st.textContent='❌ '+p.error; return;}
      if(p.status==='completed') break;
    }
    // 第 3 步：拉结果
    const rd=await (await fetch('/api/acquire/task/'+taskId+'/result')).json();
    renderPosts(rd.posts||[]); renderAcqLeads(rd.leads||[]);
    st.textContent='✅ 完成：生成 '+((rd.posts||[]).length)+' 帖 / 识别 '+((rd.leads||[]).length)+' 条线索';
  }catch(e){st.textContent='❌ 出错: '+e.message;}
  finally{btn.disabled=false; btn.textContent='▶ 运行获客闭环'; st.classList.remove('spin');}
}
function renderPosts(posts){
  const el=document.getElementById('acqPosts'); el.innerHTML='';
  posts.forEach(p=>{
    const d=document.createElement('div'); d.className='post';
    d.innerHTML='<div class="post-h">'+p.platform+'</div><div class="post-b">'+(p.post||'').replace(/\\n/g,'<br>')+'</div>';
    el.appendChild(d);
  });
}
function renderAcqLeads(leads){
  const el=document.getElementById('acqLeads'); el.innerHTML='';
  if(!leads.length){el.innerHTML='<div class="empty">本次无线索</div>';return;}
  let h='<table><thead><tr><th>联系人</th><th>意图</th><th>阶段</th><th>AI 接待话术</th></tr></thead><tbody>';
  leads.forEach(l=>{
    const dr=(l.draft||'').replace(/\\n/g,'<br>');
    h+='<tr><td>'+(l.contact||'')+'</td><td>'+(l.intent||'')+'</td><td><span class="badge '+(l.stage||'new')+'">'+(l.stage||'')+'</span></td><td class="draft">'+dr+'</td></tr>';
  });
  h+='</tbody></table>'; el.innerHTML=h;
}
async function addInbox(){
  const source=document.getElementById('ibSource').value.trim();
  const contact=document.getElementById('ibContact').value.trim();
  const text=document.getElementById('ibText').value.trim();
  if(!text) return;
  await fetch('/api/acquire/inbox',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:source||'Web form',contact:contact||'anonymous',text:text})});
  document.getElementById('ibText').value='';
  toast('已加入真实消息，重跑中…'); runAcquire();
}

async function loadCrawlers(){
  try{
    const r=await fetch('/api/acquire/crawlers'); const d=await r.json();
    const list=(d.crawlers||[]);
    const html=list.map(c=>{
      const cls=c.enabled?'on':'off';
      const lbl=c.name.toUpperCase()+(c.enabled?'':' (缺 KEY)');
      return `<span class="crawl-chip ${cls}" title="${c.description||''}">${lbl}</span>`;
    }).join('');
    document.getElementById('crawlSources').innerHTML=html;
  }catch(e){document.getElementById('crawlSources').innerHTML='<span class="crawl-chip off">爬虫配置加载失败</span>';}
}

async function runCrawl(){
  const btn=document.getElementById('crawlBtn'), st=document.getElementById('crawlStatus');
  const q=document.getElementById('cq').value.trim();
  const limit=parseInt(document.getElementById('cl').value)||3;
  btn.disabled=true; btn.textContent='抓取中…';
  st.textContent='正在调用爬虫→识别→接待（首次约 60s）…';
  try{
    const r=await fetch('/api/acquire/crawl',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,limit:limit,pipeline:true})});
    const d=await r.json();
    if(d.error){st.textContent='❌ '+d.error; return;}
    renderCrawled(d);
    const crawled=d.crawlers.filter(c=>c.ok).map(c=>c.crawler+'('+c.count+')').join(', ')||'无';
    st.textContent='✅ 完成：爬虫命中 '+crawled+' / 抓取 '+d.fetched_count+' 条 / 入库 '+d.appended_to_inbox+' 条';
    toast('自动抓取完成，请看「运行获客闭环」与 CRM 看板');
    // 顺手刷新 CRM 看板与闭环结果
    loadLeads();
    runAcquire();
  }catch(e){st.textContent='❌ 出错: '+e.message;}
  finally{btn.disabled=false; btn.textContent='🕷 自动抓取并跑闭环';}
}

function renderCrawled(d){
  const el=document.getElementById('crawlFetched'); el.style.display='';
  const all=(d.crawlers||[]).flatMap(c=>(c.leads||[]).map(l=>({...l,_src:c.crawler})));
  if(!all.length){el.innerHTML='<div class="empty">本次未抓到线索。提示：默认无 KEY 时使用精选种子；填入 APOLLO_API_KEY 即接真 Apollo。</div>'; return;}
  let h='<div class="crawl-fetched-h"><span>本次抓到 '+all.length+' 条原始线索（自动分类并已加入 CRM）</span><span style="font-size:11px;color:var(--muted)">来源标注：🟣 Apollo=付费API / 🟠 Hunter=付费API / 🟪 Curated=精选种子</span></div>';
  h+='<table><thead><tr><th>来源</th><th>联系人</th><th>公司 / 国家</th><th>原始消息</th></tr></thead><tbody>';
  all.forEach(l=>{
    const srcKey=l._src.toLowerCase().startsWith('apollo')?'Apollo.io':(l._src.toLowerCase().startsWith('hunter')?'Hunter.io':'Curated');
    h+=`<tr><td><span class="crawl-src ${srcKey}">${srcKey}</span></td><td>${l.contact||''}</td><td>${l.company||''}${l.country?' / '+l.country:''}</td><td style="font-size:12px;color:var(--muted)">${(l.text||'').slice(0,90)}${(l.text||'').length>90?'…':''}</td></tr>`;
  });
  h+='</tbody></table>';
  el.innerHTML=h;
}
loadCrawlers();
</script>
</body>
</html>
"""


class AskReq(BaseModel):
    question: str


class AdvanceReq(BaseModel):
    lead_id: str
    stage: str


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML


@app.post("/api/ask")
def api_ask(req: AskReq):
    return rag_client.ask(req.question)


@app.get("/api/leads")
def api_leads():
    return {"leads": crm_store.get_leads(), "stats": crm_store.stats()}


@app.get("/api/leads/export")
def api_export_csv():
    """导出线索为 CSV（带 UTF-8 BOM，Excel 打开中文不乱码）"""
    import csv
    import io
    from datetime import datetime

    leads = crm_store.get_leads()
    cols = ["id", "source", "contact", "company", "country", "intent",
            "stage", "summary", "raw_text", "collected_at", "updated_at"]
    buf = io.StringIO()
    buf.write("\ufeff")                      # Excel 识别 UTF-8 的 BOM
    w = csv.writer(buf)
    w.writerow(cols)
    for l in leads:
        w.writerow([l.get(c, "") if isinstance(l, dict) else getattr(l, c, "")
                    for c in cols])
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="leads-{stamp}.csv"'},
    )


@app.post("/api/leads/advance")
def api_advance(req: AdvanceReq):
    return crm_writer.advance_stage(req.lead_id, req.stage)


class InboxReq(BaseModel):
    source: str = "Web form"
    contact: str = "anonymous"
    text: str


@app.post("/api/acquire/run")
def api_acquire_run():
    """转发到项目2 获客矩阵服务，跑完整闭环"""
    try:
        r = requests.post(ACQUIRE_API_URL + "/api/acquire/run", timeout=180)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/acquire/inbox")
def api_acquire_inbox(req: InboxReq):
    """转发真实社媒消息到项目2"""
    try:
        r = requests.post(ACQUIRE_API_URL + "/api/inbox",
                          json={"source": req.source, "contact": req.contact, "text": req.text},
                          timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


class CrawlReq(BaseModel):
    query: str = ""
    limit: int = 3
    pipeline: bool = True


@app.post("/api/acquire/crawl")
def api_acquire_crawl(req: CrawlReq):
    """转发到项目2：抓取→入库→(可选)识别+接待"""
    try:
        r = requests.post(ACQUIRE_API_URL + "/api/acquire/crawl",
                          json={"query": req.query, "limit": req.limit, "pipeline": req.pipeline},
                          timeout=180)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/acquire/crawlers")
def api_acquire_crawlers():
    """获取爬虫配置状态（UI 展示）"""
    try:
        r = requests.get(ACQUIRE_API_URL + "/api/acquire/crawlers", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/acquire/task/{task_id}")
def api_acquire_task(task_id: str):
    """转发任务进度查询到项目2（前端每 2 秒轮询一次）"""
    try:
        r = requests.get(f"{ACQUIRE_API_URL}/api/acquire/task/{task_id}", timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/acquire/task/{task_id}/result")
def api_acquire_task_result(task_id: str):
    """任务完成后取结果"""
    try:
        r = requests.get(f"{ACQUIRE_API_URL}/api/acquire/task/{task_id}/result", timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
