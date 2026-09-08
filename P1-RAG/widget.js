/* 全屋定制 RAG 网站挂件 — 嵌一行 <script src="HOST/widget.js"></script> 即可
   可选配置（data-* 属性）：
     data-color="#C8102E"   品牌主色，默认 #185FA5
     data-lang="zh"         强制语言 zh / en，默认跟随浏览器
     data-lead="http://…"   留资提交地址，不填则隐藏留资入口
     data-title="…"         自定义聊天窗标题
*/
(function () {
  var S = document.currentScript;
  var HOST = new URL(S.src).origin;
  var MAIN = S.getAttribute('data-color') || '#185FA5';
  var LEAD_URL = S.getAttribute('data-lead') || '';
  var TITLE = S.getAttribute('data-title') || '';
  var LANG = (S.getAttribute('data-lang') ||
              (navigator.language || 'en').toLowerCase()).slice(0, 2);
  if (LANG !== 'zh') LANG = 'en';

  var T = {
    zh: {
      title: '产品咨询助手',
      greet: '你好！关于产品、起订量、认证或运输，都可以问我。',
      ph: '输入你的问题…', send: '发送',
      src: '出处：', thinking: '思考中…', netErr: '网络异常：',
      leadBtn: '留下联系方式，让我们联系你',
      fName: '姓名', fContact: '邮箱 / WhatsApp', fNeed: '你的需求（选填）',
      submit: '提交', cancel: '取消',
      required: '请填写姓名和联系方式',
      thanks: '已收到！我们会尽快通过 {c} 联系你。',
      fail: '提交失败，请稍后再试。'
    },
    en: {
      title: 'Product assistant',
      greet: 'Hello! Ask me about products, MOQ, certifications or shipping.',
      ph: 'Type your question…', send: 'Send',
      src: 'Sources: ', thinking: '…', netErr: 'Network error: ',
      leadBtn: 'Leave your contact for a quote',
      fName: 'Name', fContact: 'Email / WhatsApp', fNeed: 'Your requirement (optional)',
      submit: 'Submit', cancel: 'Cancel',
      required: 'Please fill in name and contact',
      thanks: 'Thanks! We will contact you at {c} shortly.',
      fail: 'Submission failed, please try again later.'
    }
  }[LANG];
  if (TITLE) T.title = TITLE;

  var STYLE = [
    '.qw-btn{position:fixed;right:24px;bottom:24px;width:58px;height:58px;border-radius:50%;',
    'background:var(--qw-main);color:#fff;border:0;cursor:pointer;font-size:24px;z-index:9998;',
    'box-shadow:0 2px 12px rgba(0,0,0,.18)}',
    '.qw-win{position:fixed;right:24px;bottom:92px;width:380px;max-width:calc(100vw - 32px);',
    'height:540px;max-height:calc(100vh - 120px);background:#fff;border:1px solid #e3e3e0;',
    'border-radius:12px;z-index:9999;display:none;flex-direction:column;overflow:hidden;',
    'box-shadow:0 8px 32px rgba(0,0,0,.16);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}',
    '.qw-win.on{display:flex}',
    '.qw-hd{background:var(--qw-main);color:#fff;padding:14px 16px;font-size:15px;font-weight:500;',
    'display:flex;justify-content:space-between;align-items:center}',
    '.qw-x{background:none;border:0;color:#fff;font-size:20px;cursor:pointer;line-height:1}',
    '.qw-body{flex:1;overflow-y:auto;padding:16px;background:#fafaf8}',
    '.qw-msg{margin-bottom:12px;font-size:13px;line-height:1.6;max-width:82%;',
    'padding:10px 12px;border-radius:10px;white-space:pre-wrap;word-break:break-word}',
    '.qw-ai{background:#fff;border:1px solid #e3e3e0;color:#222}',
    '.qw-me{background:var(--qw-main);color:#fff;margin-left:auto}',
    '.qw-src{margin-top:6px;font-size:11px;color:#777}',
    '.qw-src span{display:inline-block;background:#F1EFE8;color:#5F5E5A;',
    'padding:2px 7px;border-radius:4px;margin-right:4px}',
    '.qw-ft{border-top:1px solid #e3e3e0;padding:10px;display:flex;gap:8px;background:#fff}',
    '.qw-in{flex:1;border:1px solid #ddd;border-radius:8px;padding:9px 11px;font-size:13px;',
    'outline:none;font-family:inherit}',
    '.qw-in:focus{border-color:var(--qw-main)}',
    '.qw-send{background:var(--qw-main);color:#fff;border:0;border-radius:8px;padding:0 16px;',
    'cursor:pointer;font-size:13px;font-weight:500}',
    '.qw-send:disabled{opacity:.5;cursor:default}',
    '.qw-lead{border-top:1px solid #e3e3e0;padding:10px;background:#FAEEDA;text-align:center}',
    '.qw-lead button{background:#854F0B;color:#fff;border:0;border-radius:8px;',
    'padding:8px 14px;font-size:13px;cursor:pointer;width:100%}',
    '.qw-form{padding:14px;background:#fff;border-top:1px solid #e3e3e0;display:none}',
    '.qw-form.on{display:block}',
    '.qw-form label{display:block;font-size:12px;color:#666;margin:0 0 4px 2px}',
    '.qw-form input,.qw-form textarea{width:100%;border:1px solid #ddd;border-radius:8px;',
    'padding:8px 10px;font-size:13px;font-family:inherit;margin-bottom:10px;outline:none}',
    '.qw-form input:focus,.qw-form textarea:focus{border-color:var(--qw-main)}',
    '.qw-form textarea{resize:none;height:56px}',
    '.qw-form .row{display:flex;gap:8px}',
    '.qw-form .row button{flex:1;padding:9px;border-radius:8px;font-size:13px;cursor:pointer;border:0}',
    '.qw-ok{background:var(--qw-main);color:#fff}',
    '.qw-no{background:#F1EFE8;color:#5F5E5A}',
    '.qw-err{color:#A32D2D;font-size:12px;margin:-4px 0 8px;display:none}'
  ].join('');

  var st = document.createElement('style');
  st.textContent = STYLE;
  document.head.appendChild(st);
  document.documentElement.style.setProperty('--qw-main', MAIN);

  var btn = document.createElement('button');
  btn.className = 'qw-btn';
  btn.innerHTML = '&#9993;';
  btn.title = T.title;

  var win = document.createElement('div');
  win.className = 'qw-win';
  win.innerHTML =
    '<div class="qw-hd"><span></span><button class="qw-x">&times;</button></div>' +
    '<div class="qw-body"></div>' +
    '<div class="qw-ft"><input class="qw-in"><button class="qw-send"></button></div>' +
    '<div class="qw-lead"><button></button></div>' +
    '<div class="qw-form">' +
      '<div class="qw-err"></div>' +
      '<label></label><input class="f-name">' +
      '<label></label><input class="f-contact">' +
      '<label></label><textarea class="f-need"></textarea>' +
      '<div class="row"><button class="qw-no"></button><button class="qw-ok"></button></div>' +
    '</div>';

  document.body.appendChild(btn);
  document.body.appendChild(win);

  var body = win.querySelector('.qw-body');
  var input = win.querySelector('.qw-in');
  var sendBtn = win.querySelector('.qw-send');
  var leadBar = win.querySelector('.qw-lead');
  var leadBtn = leadBar.querySelector('button');
  var form = win.querySelector('.qw-form');
  var fName = form.querySelector('.f-name');
  var fContact = form.querySelector('.f-contact');
  var fNeed = form.querySelector('.f-need');
  var errBox = form.querySelector('.qw-err');

  win.querySelector('.qw-hd span').textContent = T.title;
  input.placeholder = T.ph;
  sendBtn.textContent = T.send;
  leadBtn.textContent = T.leadBtn;
  form.querySelectorAll('label')[0].textContent = T.fName;
  form.querySelectorAll('label')[1].textContent = T.fContact;
  form.querySelectorAll('label')[2].textContent = T.fNeed;
  form.querySelector('.qw-no').textContent = T.cancel;
  form.querySelector('.qw-ok').textContent = T.submit;
  if (!LEAD_URL) leadBar.style.display = 'none';

  function toggle() {
    win.classList.toggle('on');
    if (win.classList.contains('on')) input.focus();
  }
  btn.onclick = toggle;
  win.querySelector('.qw-x').onclick = function () { win.classList.remove('on'); };

  function push(cls, text, sources) {
    var d = document.createElement('div');
    d.className = 'qw-msg ' + cls;
    d.textContent = text;
    if (sources && sources.length) {
      var s = document.createElement('div');
      s.className = 'qw-src';
      s.textContent = T.src;
      sources.forEach(function (f) {
        var c = document.createElement('span');
        c.textContent = f;
        s.appendChild(c);
      });
      d.appendChild(s);
    }
    body.appendChild(d);
    body.scrollTop = body.scrollHeight;
    return d;
  }
  push('qw-ai', T.greet);

  async function ask() {
    var q = input.value.trim();
    if (!q) return;
    input.value = '';
    push('qw-me', q);
    sendBtn.disabled = true;
    var wait = push('qw-ai', T.thinking);
    try {
      var r = await fetch(HOST + '/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q })
      });
      var d = await r.json();
      wait.textContent = d.answer || '(no answer)';
      if (d.sources && d.sources.length) {
        var s = document.createElement('div');
        s.className = 'qw-src';
        s.textContent = T.src;
        d.sources.forEach(function (f) {
          var c = document.createElement('span');
          c.textContent = f;
          s.appendChild(c);
        });
        wait.appendChild(s);
      }
    } catch (e) {
      wait.textContent = T.netErr + e.message;
    }
    sendBtn.disabled = false;
    body.scrollTop = body.scrollHeight;
  }

  sendBtn.onclick = ask;
  input.onkeydown = function (e) { if (e.key === 'Enter') ask(); };

  leadBtn.onclick = function () {
    form.classList.add('on');
    leadBar.style.display = 'none';
    fName.focus();
  };

  form.querySelector('.qw-no').onclick = function () {
    form.classList.remove('on');
    leadBar.style.display = '';
    errBox.style.display = 'none';
  };

  form.querySelector('.qw-ok').onclick = function () {
    var name = fName.value.trim();
    var contact = fContact.value.trim();
    var need = fNeed.value.trim();
    if (!name || !contact) {
      errBox.textContent = T.required;
      errBox.style.display = 'block';
      return;
    }
    errBox.style.display = 'none';
    var text = 'Website visitor ' + name + ' left contact. Requirement: ' + (need || '(not specified)');
    fetch(LEAD_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: 'Website widget', contact: contact, text: text })
    }).then(function () {
      form.classList.remove('on');
      push('qw-ai', T.thanks.replace('{c}', contact));
    }).catch(function () {
      push('qw-ai', T.fail);
    });
  };
})();
