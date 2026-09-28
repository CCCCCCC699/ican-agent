"""生成申报书配图：架构图 + 知识图谱Schema图（中文字体SimHei）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import font_manager
from pathlib import Path

font_manager.fontManager.addfont(str(Path.home() / ".local/share/fonts/simhei.ttf"))
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(__file__).parent
METRO_RED = "#E3002B"
METRO_BLUE = "#1F4E79"
METRO_GREEN = "#94D40B"
BG = "#f5f6f8"

def box(ax, x, y, w, h, text, fc, tc="white", fs=12, lw=0, ec="none"):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, fontweight="bold")

def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#5a6c7d", lw=1.8))

# ============ 图1: 架构图 ============
fig, ax = plt.subplots(figsize=(12, 7.2), dpi=150)
ax.set_xlim(0, 12); ax.set_ylim(0, 7.2); ax.axis("off")
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

# 前端层
box(ax, 3.5, 6.0, 5, 0.9, "Web前端\n聊天界面 · Agent运行轨迹 · 图谱可视化", METRO_BLUE, fs=11)
# 后端编排层
box(ax, 0.2, 3.6, 11.6, 1.9, "", "#ffffff", ec="#c9d4dd", lw=1)
ax.text(0.5, 5.15, "FastAPI 后端（多Agent流水线）", fontsize=11, fontweight="bold", color=METRO_BLUE)
agents = ["意图路由Agent\n分类+槽位提取\n站名模糊匹配",
          "Text2Cypher Agent\n自然语言→只读Cypher\n白名单安全校验",
          "图算法模块\nDijkstra最短路\n途经/避让约束",
          "答案生成Agent\n基于图谱证据\n可控生成"]
for i, a in enumerate(agents):
    box(ax, 0.5 + i * 2.95, 3.75, 2.6, 1.35, a, "#2c6faa" if i != 2 else METRO_GREEN, fs=9.5, tc="white" if i != 2 else "#1a3a12")
# 层间箭头
arrow(ax, 6, 5.9, 6, 5.6)
arrow(ax, 6, 3.5, 6, 3.2)
# 数据底座层
box(ax, 0.2, 1.0, 5.4, 1.6, "Neo4j 知识图谱\nLine / LineStation / Transfer\n(线路·站点·换乘关系)", "#8e44ad", fs=11)
box(ax, 6.4, 1.0, 5.4, 1.6, "大模型（双模式）\n云API: DeepSeek/智谱/硅基流动\n本地: Ollama + Qwen", "#c0392b", fs=11)
# 图算法模块 → Neo4j
arrow(ax, 2.6, 3.7, 2.9, 2.7)
# Text2Cypher → Neo4j
arrow(ax, 3.6, 3.7, 3.3, 2.7)
# LLM与后端双向
arrow(ax, 9.0, 3.7, 9.1, 2.7); arrow(ax, 9.6, 2.6, 9.5, 3.7)
# 标签
ax.text(1.2, 3.3, "查询/执行", fontsize=9, color="#5a6c7d")
ax.text(8.6, 3.3, "推理调用", fontsize=9, color="#5a6c7d")
ax.text(6.05, 1.2, "确定性计算 + 语义理解 双引擎", fontsize=10, ha="center", color="#5a6c7d", style="italic")
fig.savefig(OUT / "图-架构图.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)

# ============ 图2: 图谱Schema图 ============
fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
ax.set_xlim(0, 10); ax.set_ylim(0, 5.5); ax.axis("off")
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

pos = {
    "Line1": (1.2, 3.6), "Line2": (1.2, 1.4),
    "LS1": (4.6, 4.6), "LS2": (7.2, 4.6), "LS3": (9.4, 4.6),
    "LS4": (4.6, 0.6), "LS5": (7.2, 0.6),
}
def nbox(name, label, fc, fs=11):
    x, y = pos[name]
    box(ax, x - 1.15, y - 0.42, 2.3, 0.84, label, fc, fs=fs)

nbox("Line1", "Line 线路\nname, color", METRO_BLUE, fs=10)
nbox("Line2", "Line 线路\nname, color", METRO_BLUE, fs=10)
nbox("LS1", "LineStation 站A\nstation, line, order", "#2c6faa", fs=10)
nbox("LS2", "LineStation 站B\nstation, line, order", "#2c6faa", fs=10)
nbox("LS3", "LineStation 站C\nstation, line, order", "#2c6faa", fs=10)
nbox("LS4", "LineStation 站D\nstation, line, order", "#2c6faa", fs=10)
nbox("LS5", "LineStation 站E\nstation, line, order", "#2c6faa", fs=10)

rels = [
    ("Line1", "LS1", "ON_LINE", 0.2), ("Line1", "LS2", "ON_LINE", -0.2), ("Line1", "LS3", "ON_LINE", 0.2),
    ("Line2", "LS4", "ON_LINE", -0.2), ("Line2", "LS5", "ON_LINE", 0.2),
    ("LS1", "LS2", "NEXT_STATION", 0.25), ("LS2", "LS3", "NEXT_STATION", 0.25),
    ("LS4", "LS5", "NEXT_STATION", 0.25),
    ("LS2", "LS4", "TRANSFER_TO\n(transfer_time)", 0.3),
]
for a, b, label, off in rels:
    (x1, y1), (x2, y2) = pos[a], pos[b]
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#5a6c7d", lw=1.4,
                                connectionstyle="arc3,rad=" + str(off)))
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + off * 1.6
    ax.text(mx, my, label, fontsize=9, color=METRO_RED, ha="center", fontweight="bold",
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.5))
ax.set_title("上海轨道交通知识图谱 Schema", fontsize=14, fontweight="bold", color=METRO_BLUE, pad=10)
fig.savefig(OUT / "图-schema.png", bbox_inches="tight", facecolor=BG)
plt.close(fig)
print("OK:", list(OUT.glob("图-*.png")))
