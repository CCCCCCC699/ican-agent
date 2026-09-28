// 申城智行前端：聊天 + Agent轨迹 + 图谱可视化
const messages = document.getElementById('messages');
const traceEl = document.getElementById('trace');
const form = document.getElementById('chat-form');
const input = document.getElementById('chat-input');
let network = null;

function addMessage(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function renderTrace(data) {
  traceEl.innerHTML = '';
  const rows = [
    ['意图分类', data.intent === 'route_plan' ? '路线规划' : data.intent === 'info_query' ? '信息查询' : '闲聊'],
    ['生成查询', data.cypher || (data.plan && data.plan.ok ? '图算法路径规划（确定性计算）' : '—')],
    ['图谱证据', data.evidence && data.evidence.length ? data.evidence.length + ' 条记录' : (data.plan && data.plan.ok ? '路线节点 ' + data.plan.path.length + ' 个' : '无')],
  ];
  rows.forEach(([k, v]) => {
    const row = document.createElement('div');
    row.className = 'trace-row';
    row.innerHTML = '<span class="k">' + k + '</span><span class="v">' + v + '</span>';
    traceEl.appendChild(row);
  });
}

function renderGraph(data) {
  if (!data || !data.nodes) return;
  const nodes = data.nodes.map(n => ({ id: n.id, label: n.label, color: lineColor(n.line) }));
  const edges = data.edges.map((e, i) => ({ id: 'e' + i, from: e.from, to: e.to }));
  const container = document.getElementById('graph');
  if (network) network.destroy();
  network = new vis.Network(container, { nodes, edges }, {
    nodes: { shape: 'dot', size: 14, font: { size: 11 } },
    edges: { arrows: 'to' },
  });
}

function lineColor(line) {
  const map = { '1号线': '#E3002B', '2号线': '#94D40B', '3号线': '#FCD600', '4号线': '#5F259F', '5号线': '#944D9A', '6号线': '#D40068', '7号线': '#ED6A00', '8号线': '#0094D8', '9号线': '#87CAED', '10号线': '#C6AFD4', '11号线': '#871E2B', '12号线': '#007B60', '13号线': '#E999C0', '14号线': '#616020', '15号线': '#BBA786', '16号线': '#2CD5C4', '17号线': '#BC796F', '18号线': '#C4984F' };
  return map[line] || '#888888';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  addMessage('user', text);
  const answerDiv = addMessage('assistant', '思考中…');
  try {
    const resp = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    answerDiv.textContent = data.answer || '（无回答）';
    renderTrace(data);
    if (data.plan && data.plan.ok && data.plan.path[0]) {
      fetch('/api/graph/preview?station=' + encodeURIComponent(data.plan.path[0]))
        .then(r => r.json()).then(renderGraph).catch(() => {});
    }
  } catch (err) {
    answerDiv.textContent = '后端连接失败：' + err.message;
  }
});

// 地铁色点装饰
const colors = ['#E3002B', '#94D40B', '#FCD600', '#5F259F', '#0094D8', '#D40068', '#ED6A00', '#007B60'];
colors.forEach(c => {
  const d = document.createElement('span');
  d.className = 'metro-dot';
  d.style.background = c;
  document.getElementById('metro-dots').appendChild(d);
});
