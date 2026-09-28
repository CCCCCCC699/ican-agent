# 申城智行 · 前端

大模型 × 知识图谱 · 轨道交通出行智能体 —— Web 前端（学生B负责）

## 快速启动（演示模式，后端未就绪也能看效果）

双击 **`start.bat`**，浏览器自动打开 http://localhost:8080

或手动：

```bash
python mock_server.py   # 任意 Python3，零依赖
```

打开后会自动演示第一条问题，可点击欢迎页功能卡片 / 快捷问题体验全部 5 个演示场景。

## 目录结构

```
ican-metro-agent/
├── index.html          # 主页面：聊天 + 图谱可视化 + Agent 过程（单页，零构建）
├── mock_server.py      # 演示服务器（仅标准库）——后端就绪后可删
├── start.bat           # Windows 一键启动
├── lib/
│   └── vis-network.min.js   # 图谱可视化库（本地化，离线可用）
└── README.md
```

## 与后端对接（陈俊西）

前端**自动探测**后端地址：先试同源，再试 `http://localhost:8000`。
后端只需用 FastAPI 实现以下接口并**开启 CORS**：

```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

### API 契约

**POST /api/chat**  （核心接口）

请求：
```json
{ "message": "从虹桥火车站到陆家嘴怎么走最快？" }
```

响应：
```json
{
  "intent": "路线规划",            // 路线规划 | 约束路线规划 | 线路信息查询 | 换乘查询 | 闲聊
  "cypher": "MATCH ... RETURN p",  // 生成的 Cypher（白名单校验后执行）
  "summary": "图查询返回 N 条路径",
  "answer": "推荐路线：2号线……",    // 支持 **加粗** 与换行
  "evidence": [
    { "type": "站点", "name": "虹桥火车站" },
    { "type": "线路", "name": "2号线" },
    { "type": "关系", "name": "NEXT_STATION×5" }
  ],
  "elapsed_ms": 1284,
  "graph": {                        // 可选，有则前端渲染图谱
    "nodes": [{ "id": "虹桥火车站", "label": "虹桥火车站", "line": "2号线", "transfer": true }],
    "edges": [{ "from": "虹桥火车站", "to": "中山公园", "label": "21分钟", "dashes": false }]
  }
}
```

- `graph.nodes.line`：线路名（决定节点颜色，见 index.html 的 LINE_COLORS，未收录线路用默认灰）
- `graph.nodes.transfer`：true 渲染为菱形（换乘站）
- `graph.edges.dashes`：true 渲染为虚线（换乘关系 TRANSFER_TO）

**GET /health** → `{"status": "ok"}`（前端以此判断后端在线）

**GET /api/graph/preview** → `{"nodes": [...], "edges": [...]}`（子图预览）

## 设计语言

- 主色：上海地铁红 `#E4002B`；背景浅灰蓝渐变；卡片圆角 18px、柔和投影
- 用户气泡：红色渐变右对齐；智能体气泡：白底描边左对齐，带 🚇 头像
- 每条智能体回复附 Agent 过程卡片：① 意图分类徽章（按意图配色）② Cypher 深色代码块（可复制）③ 溯源证据标签（点击可高亮图谱节点）
- 右侧面板分段控件：知识图谱 / Agent 过程；响应式适配移动端（≤1000px 上下布局）

## 待办（按 48h 时间表）

- [x] 9/28 上午：聊天界面骨架 + 设计语言
- [x] 9/28 上午：图谱可视化组件（vis-network 本地化）
- [ ] 9/28 晚上：与 FastAPI 后端联调、错误兜底
- [ ] 9/29 上午：UI 打磨、移动端适配完善
- [ ] 9/29 下午：截图、录屏（演示 5 场景）
