# -*- coding: utf-8 -*-
"""
申城智行 - 前端演示服务器（零依赖，仅标准库）
作用：后端 FastAPI 未就绪时，让前端 UI 可以完整演示。
访问 http://localhost:8080
"""
import json, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8080

# 与前端 index.html 中 MOCK 一致的演示数据（后端就绪后可删除本文件）
MOCK_DATA = {
    "route": {
        "intent": "路线规划",
        "cypher": "MATCH p = shortestPath((a:LineStation {station_name:'虹桥火车站'})-[r:NEXT_STATION|TRANSFER_TO*]->(b:LineStation {station_name:'陆家嘴'})) RETURN p",
        "answer": "**推荐路线**\n\n乘坐 **2号线**（浦东国际机场方向），从 **虹桥火车站** 上车，经 中山公园 → 静安寺 → 人民广场 → 南京东路，共 **5 站**、约 **22 分钟** 直达 **陆家嘴**，无需换乘。",
        "evidence": [{"type":"站点","name":"虹桥火车站"},{"type":"线路","name":"2号线"},{"type":"关系","name":"NEXT_STATION×5"},{"type":"站点","name":"陆家嘴"}],
        "elapsed_ms": 1284,
        "graph": {"nodes":[
            {"id":"虹桥火车站","label":"虹桥火车站","line":"2号线","transfer":True},
            {"id":"中山公园","label":"中山公园","line":"2号线","transfer":True},
            {"id":"静安寺","label":"静安寺","line":"2号线","transfer":True},
            {"id":"人民广场","label":"人民广场","line":"2号线","transfer":True},
            {"id":"南京东路","label":"南京东路","line":"2号线","transfer":True},
            {"id":"陆家嘴","label":"陆家嘴","line":"2号线","transfer":False}
        ],"edges":[
            {"from":"虹桥火车站","to":"中山公园","label":"21分钟"},
            {"from":"中山公园","to":"静安寺","label":"4分钟"},
            {"from":"静安寺","to":"人民广场","label":"6分钟"},
            {"from":"人民广场","to":"南京东路","label":"2分钟"},
            {"from":"南京东路","to":"陆家嘴","label":"2分钟"}
        ]}
    },
    "constraint_via": {
        "intent": "约束路线规划",
        "cypher": "MATCH p1=shortestPath((a:LineStation {station_name:'莘庄'})-[r:NEXT_STATION|TRANSFER_TO*]->(x:LineStation {station_name:'徐家汇'})), p2=shortestPath((x)-[:NEXT_STATION|TRANSFER_TO*]->(b:LineStation {station_name:'五角场'})) RETURN p1,p2",
        "answer": "**带途经约束的路线** ✅ 途经点「徐家汇」已满足\n\n**第 1 段**：**1号线** 莘庄 → 徐家汇（约 20 分钟）\n**第 2 段**：徐家汇换乘 **11号线** → 交通大学（1 站）\n**第 3 段**：交通大学换乘 **10号线** → 五角场（约 25 分钟）\n\n全程约 **55 分钟**，换乘 2 次。",
        "evidence": [{"type":"站点","name":"莘庄"},{"type":"线路","name":"1号线"},{"type":"站点","name":"徐家汇"},{"type":"关系","name":"TRANSFER_TO"},{"type":"线路","name":"10号线"},{"type":"站点","name":"五角场"}],
        "elapsed_ms": 2156,
        "graph": {"nodes":[
            {"id":"莘庄","label":"莘庄","line":"1号线","transfer":False},
            {"id":"徐家汇","label":"徐家汇","line":"1号线","transfer":True},
            {"id":"交通大学","label":"交通大学","line":"11号线","transfer":True},
            {"id":"五角场","label":"五角场","line":"10号线","transfer":False}
        ],"edges":[
            {"from":"莘庄","to":"徐家汇","label":"1号线"},
            {"from":"徐家汇","to":"交通大学","label":"换乘","dashes":True},
            {"from":"交通大学","to":"五角场","label":"10号线"}
        ]}
    },
    "line_info": {
        "intent": "线路信息查询",
        "cypher": "MATCH (ls:LineStation)-[:ON_LINE]->(l:Line {line_name:'2号线'}) WHERE ls.is_transfer = true RETURN ls.station_name, ls.station_order ORDER BY ls.station_order",
        "answer": "**2号线换乘站列表**（自西向东）：\n\n虹桥火车站（10号线/17号线）→ 中山公园（3号线/4号线）→ 静安寺（7号线/14号线）→ 人民广场（1号线/8号线）→ 世纪大道（4号线/6号线/9号线）→ 龙阳路（7号线/16号线/18号线/磁浮线）→ 广兰路（21号线）",
        "evidence": [{"type":"线路","name":"2号线"},{"type":"关系","name":"ON_LINE"},{"type":"关系","name":"is_transfer=true"}],
        "elapsed_ms": 987,
        "graph": {"nodes":[
            {"id":"虹桥火车站","label":"虹桥火车站","line":"2号线","transfer":True},
            {"id":"中山公园","label":"中山公园","line":"2号线","transfer":True},
            {"id":"静安寺","label":"静安寺","line":"2号线","transfer":True},
            {"id":"人民广场","label":"人民广场","line":"2号线","transfer":True},
            {"id":"世纪大道","label":"世纪大道","line":"2号线","transfer":True},
            {"id":"龙阳路","label":"龙阳路","line":"2号线","transfer":True}
        ],"edges":[
            {"from":"虹桥火车站","to":"中山公园"},{"from":"中山公园","to":"静安寺"},
            {"from":"静安寺","to":"人民广场"},{"from":"人民广场","to":"世纪大道"},
            {"from":"世纪大道","to":"龙阳路"}
        ]}
    },
    "transfer": {
        "intent": "换乘查询",
        "cypher": "MATCH (ls:LineStation {station_name:'人民广场'})-[:TRANSFER_TO]->(t:LineStation)-[:ON_LINE]->(l:Line) RETURN DISTINCT l.line_name, t.transfer_time",
        "answer": "**人民广场** 是 **1号线、2号线、8号线** 三线换乘站。\n\n- 1号线 ↔ 2号线：换乘步行约 4 分钟\n- 1号线 ↔ 8号线：换乘步行约 3 分钟\n- 2号线 ↔ 8号线：换乘步行约 3 分钟",
        "evidence": [{"type":"站点","name":"人民广场"},{"type":"关系","name":"TRANSFER_TO×3"},{"type":"线路","name":"1号线"},{"type":"线路","name":"2号线"},{"type":"线路","name":"8号线"}],
        "elapsed_ms": 842,
        "graph": {"nodes":[
            {"id":"人民广场","label":"人民广场","line":"2号线","transfer":True},
            {"id":"人民广场1","label":"人民广场","line":"1号线","transfer":True},
            {"id":"人民广场8","label":"人民广场","line":"8号线","transfer":True}
        ],"edges":[
            {"from":"人民广场","to":"人民广场1","label":"换乘4分钟","dashes":True},
            {"from":"人民广场","to":"人民广场8","label":"换乘3分钟","dashes":True}
        ]}
    },
    "constraint_avoid": {
        "intent": "约束路线规划",
        "cypher": "MATCH p = shortestPath((a:LineStation {station_name:'虹桥火车站'})-[r:NEXT_STATION|TRANSFER_TO*]->(b:LineStation {station_name:'陆家嘴'})) WHERE NONE(n IN nodes(p) WHERE n.station_name = '人民广场') RETURN p",
        "answer": "**带避让约束的路线** ✅ 已避开「人民广场」\n\n**10号线** 虹桥火车站 → 南京东路（约 28 分钟）\n南京东路换乘 **2号线** → 陆家嘴（1 站，约 4 分钟）\n\n全程约 **36 分钟**，换乘 1 次。",
        "evidence": [{"type":"站点","name":"虹桥火车站"},{"type":"线路","name":"10号线"},{"type":"关系","name":"NEXT_STATION"},{"type":"站点","name":"南京东路"},{"type":"线路","name":"2号线"},{"type":"站点","name":"陆家嘴"}],
        "elapsed_ms": 2013,
        "graph": {"nodes":[
            {"id":"虹桥火车站","label":"虹桥火车站","line":"10号线","transfer":True},
            {"id":"交通大学","label":"交通大学","line":"10号线","transfer":True},
            {"id":"新天地","label":"新天地","line":"10号线","transfer":True},
            {"id":"南京东路","label":"南京东路","line":"10号线","transfer":True},
            {"id":"陆家嘴","label":"陆家嘴","line":"2号线","transfer":False}
        ],"edges":[
            {"from":"虹桥火车站","to":"交通大学"},{"from":"交通大学","to":"新天地"},
            {"from":"新天地","to":"南京东路"},{"from":"南京东路","to":"陆家嘴","label":"换乘","dashes":True}
        ]}
    }
}

def route_question(q):
    if "避开" in q:
        return "constraint_avoid"
    if "人民广场" in q and "换乘" in q:
        return "transfer"
    if "虹桥" in q and "陆家嘴" in q:
        return "route"
    if "莘庄" in q:
        return "constraint_via"
    if "2号线" in q or "二号线" in q:
        return "line_info"
    if "人民广场" in q:
        return "transfer"
    return "route"

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, "")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok", "mode": "mock", "model": "Qwen2.5-7B-Instruct (即将接入)"})
        elif path == "/api/graph/preview":
            self._send(200, MOCK_DATA["route"]["graph"])
        elif path == "/" or path == "/index.html":
            self._send(200, open(os.path.join(ROOT, "index.html"), "rb").read(), "text/html; charset=utf-8")
        elif path == "/lib/vis-network.min.js":
            self._send(200, open(os.path.join(ROOT, "lib", "vis-network.min.js"), "rb").read(), "application/javascript")
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/chat":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        q = body.get("message", "")
        key = route_question(q)
        resp = dict(MOCK_DATA[key])
        if key == "route" and not (("虹桥" in q and "陆家嘴" in q)):
            resp["answer"] = "（演示模式）我收到了你的问题：" + q + "\n\n当前后端尚未接入，此回复为演示数据。"
        self._send(200, resp)

if __name__ == "__main__":
    print("=" * 50)
    print("  申城智行 · 前端演示服务器")
    print("  访问: http://localhost:%d" % PORT)
    print("  提示: 后端 FastAPI 就绪后，前端会自动切换连接")
    print("=" * 50)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
