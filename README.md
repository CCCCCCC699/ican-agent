# 申城智行 —— 大模型×知识图谱的轨道交通出行智能体

iCAN大学生创新创业大赛 AI应用创新挑战赛（软件赛道）参赛作品。

乘客用自然语言描述出行需求（"从虹桥火车站去陆家嘴，经过徐家汇，避开人民广场"），系统通过**多智能体协作**，基于**自建上海轨道交通知识图谱**，给出可解释、可溯源的出行方案。

## 核心特性

- 🧠 **多智能体协作**：意图路由Agent → Text2Cypher Agent → 答案生成Agent
- 📊 **LLM×KG可控结合**：AI管语义，算法管计算——路线由确定性图算法（Dijkstra）计算，答案由图谱数据驱动，杜绝幻觉
- 🛡️ **安全设计**：LLM生成的Cypher经只读白名单校验后才执行
- 🚇 **复合约束规划**：支持途经点（via）与避让站（avoid）
- 🔌 **双模式推理**：云API（DeepSeek/智谱/硅基流动等）与本地Ollama可插拔切换

## 架构

```
用户(自然语言)
   ↓  Web前端（聊天 + Agent轨迹 + 图谱可视化）
   ↓  FastAPI 后端
   ├─ 意图路由Agent ──→ 分类+槽位提取（含站名模糊匹配）
   ├─ Text2Cypher Agent ──→ 只读Cypher → 白名单校验 → Neo4j
   ├─ 图算法模块 ──→ 多约束最短路（NetworkX, 确定性计算）
   └─ 答案生成Agent ──→ 基于图谱证据合成回答
   ↓  ↑
 Neo4j(知识图谱)    大模型(云API / 本地Ollama)
```

## 目录结构

```
metro-agent/
├── backend/
│   ├── app/
│   │   ├── agents/      # 意图路由/Text2Cypher/答案生成 + 提示词
│   │   ├── graph/       # Neo4j存储、路径规划、站名解析
│   │   ├── llm/         # LLM客户端（Ollama + OpenAI兼容云API）
│   │   ├── safety/      # Cypher只读白名单校验
│   │   ├── config.py    # .env 配置
│   │   ├── main.py      # FastAPI 入口
│   │   └── orchestrator.py  # 多Agent流水线编排
│   └── tests/           # 31个pytest用例
├── frontend/            # 单页Web应用（原生HTML/JS + vis-network）
├── data/                # 自建知识图谱数据（lines/line_stations/transfers）
└── docs/                # 申报书、视频脚本
```

## 快速运行

### 1. 准备数据底座（Neo4j）

```bash
# 启动Neo4j（Community 5.x，默认认证 neo4j/ican2026）
bin/neo4j start
# 首次使用需设置初始密码：
# bin/neo4j-admin dbms set-initial-password ican2026
```

### 2. 配置大模型

```bash
cd backend
cp .env.example .env   # 填入 LLM_API_KEY（DeepSeek/智谱/硅基流动均可）
```

本地模式（可选）：安装Ollama并 `ollama pull qwen3:8b`，不填API密钥即自动走本地。

### 3. 启动后端

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q        # 运行测试（31用例）
.venv/bin/uvicorn app.main:app --port 8000  # 启动服务
```

### 4. 导入知识图谱数据

```bash
.venv/bin/python -c "from app.config import settings; from app.graph.neo4j_store import Neo4jStore; Neo4jStore(settings).import_from_csv(settings.data_dir)"
```

### 5. 打开界面

浏览器访问 http://localhost:8000 ，试试：

- 从虹桥火车站到陆家嘴怎么走最快？
- 从莘庄去五角场，途中经过徐家汇
- 2号线经过哪些换乘站？
- 人民广场可以换乘哪几条线？
- 从上海南站到五角场，避开人民广场

## 演示视频

见 `docs/视频/演示视频脚本.md`（5分钟分镜与台词）。
