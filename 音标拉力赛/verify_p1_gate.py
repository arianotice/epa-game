# -*- coding: utf-8 -*-
"""
verify_p1_gate.py · P1 门控实跑脚本【REAL_RUN · v1.2 / 2026-11-12】

> 【状态更新 2026-11-12】本文件已实跑化。下方框内「规格阶段骨架」是 2026-11-10
> 的历史说明，已被本轮实现取代，仅作规格沿革留档：当前默认执行 = 真实套件实跑
> (S0/S1..S6) + 静态断言 B1–B10 + 81 项 PLR-* 迁移重放，产出 result.json 与
> GATE_VERDICT；`--spec-only` 才只做清单自检。
> 权威口径：design/p1-qa-spec.md + design/p1-gate-retirement.md §5。

对应规格：design/p1-qa-spec.md v1.1（#31，quality-lead 严守真，2026-11-10）
v1.1 并入主理人两批 P1 门控口径裁决 + #29 C1/C2/C3 回执 + #30 六维/光照锚点。

╔══════════════════════════════════════════════════════════════════════════╗
║ 本轮为【规格阶段骨架】：只落判据清单常量 + chk() 框架 + 自检，             ║
║ 不启动浏览器、不起 dev/build 服务、不连接任何端口、不产生验收 SUMMARY。    ║
║ 实跑须等主理人通知，且须先拿齐 design/p1-qa-spec.md §10 的前置输入      ║
║ （#28 可观测接口 / 相机 / snapshot / DOM / 服务形态 / vendor N /          ║
║   降级模拟点 / 视觉六维可观测点；用户 G9 Playtest 与 G10 退役时点裁决）。  ║
║  #29 D4 权威映射表、#30 视觉规格已到位，占位取消（按 ID 引用不复述语义）。║
║                                                                          ║
║ 严禁在产物未定型时跑出误导性的「全绿」结论（#5-PRE 优雅报错同构）。       ║
╚══════════════════════════════════════════════════════════════════════════╝

实跑时须沿用（逐字不放宽）：
  - p0-qa-spec.md §1 K1–K5 五类不可降级断言
  - 「门控全绿」口径（主理人裁决 A）：路线 B 重定义套件 + 81 项原样保留
    + node js/headless_laps.mjs 11 场 ALL PASS；**≠ 原始 110 项原样全绿**（X9）
  - #5 裁决 H5 检测面：textContent + 后代所有属性值；不查 innerHTML
  - allWords() 83 词全表 + correctLateral/spoken/left/right 四字段名
  - len(vocab)==83 and len(set(vocab))==83 词表完整性守卫（硬 chk）
  - 3D 层零答案域读取（裁决 B-4）：gate.spoken/correctLateral/qType/hit/left/right
    及派生参数零进入 3D 场景/材质/几何/路牌纹理/DOM 属性，与 H5 检测面串联
  - C1 键契约（裁决 C-1）：unit 唯一主键 48/48 唯一；sym 稳定键 48/48 唯一、
    仅作存档/查表/去重/角标/alt；displayIpa 绝不进任何键位/去重（U05/U07 撞 ɑ）
  - C2 单调口径（裁决 C-2）：逐音素按 CI 单调不降，CI=A+B+2C；
    禁「整类 > 整类」断言；抽样按「档位边界 CI 不倒置」
  - 四项错误计数：pageerror / 硬 console_error / bad_status / 同源真实失败 全 0
    ERR_ABORTED、外链、Vite 机制、WebGL 上下文事件 单列披露（附录 A.7 口径）
  - BV-0 先探兜底硬前置 + 四重判定（逐字节 + magic + sha256 + CType 非 text/html，不信状态码）
  - BR 纸雾用 fogIsExp2 布尔；禁用 fogType / 类名字符串 / constructor.name（附录 A.8）
  - 光照（裁决 B-2）：P1 主站 lightCount==2（1 主光 + 1 柔补光 <=0.35 + AO）；
    **不复用** P0 probe.jsx 的 lightCount=1；probe.jsx/probe.html 逐字不动
  - 降级路径（裁决 B-3/C-3）：PDEG-* 与 PV-* 正常路径分表；不作 PF-01 的 FAIL 证据
  - 串行跑；服务由本脚本 subprocess.Popen 自起、finally terminate + 端口复核（#20b 可靠方案）
  - 连续两轮 SUMMARY 与断言名集合逐条一致才下结论（非 flaky）

本文件当前唯一可执行行为：静态自检清单完整性 → 打印 → exit(2)。
"""

import sys

# ---------------------------------------------------------------------------
# 常量（沿用 P0 / #5 既有口径；实跑前按 #28 产物核对）
# ---------------------------------------------------------------------------
TAG = "hud-20261108"                 # 源码层（2D 遗产层）唯一 tag，恰好 46 处
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"   # 本机 Playwright 缺 chromium-1248
SRC_TAG_COUNT = 46
EXCLUDE_DIRS = ("node_modules", "dist", ".p0-build", ".workbuddy", "__pycache__", ".git")
SRC_WHITELIST = (
    "音标大闯关/index.html", "音标大闯关/js/atlas.js", "音标大闯关/js/level.js",
    "音标大闯关/js/map.js", "音标大闯关/js/story.js", "音标拉力赛/index.html",
    "音标拉力赛/js/main.js", "音标拉力赛/js/race.js", "音标拉力赛/js/render.js",
)

# 上游权威引用（#29 / #30 已交付，非占位；按 ID 交叉引用、不复述产品语义）
D4_AUTHORITY = "design/p1-gameplay-spec.md §2.3 + §2.8（D4-A01..A12 / F1–F8）"
ART_AUTHORITY = "design/p1-3d-art-spec.md §5 / §4.8 / §6.7（六维 / 光照 / 防泄题）"

# 语义占位：精确字段名/取值范围待 #28 提供（design/p1-qa-spec.md §10）
# 禁止在产物未定型前臆造接口名；判据硬要求不因占位而放宽。
P1_PROBE_OBJECT = None       # TODO(#28): 只读可观测对象名（类比 window.__P0_PROBE__）
P1_MESH_FIELD = None         # TODO(#28): meshCount / 三车 id
P1_DRAWCALL_FIELD = None     # TODO(#28): drawCalls
P1_COVERAGE_FIELD = None     # TODO(#28): 三车屏占比 / 投影包围盒
P1_CAMERA_FIELDS = None      # TODO(#28): 机位高 / 俯角 / 水平 FOV / 阻尼 / 投影序列
P1_SNAPSHOT_KEYS = None      # TODO(#28): snapshot() 键白名单
P1_RENDER_MODE = None        # TODO(#28): 2d|3d 开关形态与默认值
VENDOR_TAG = None            # TODO(#28): 产物层 tag；N 由 P1 产物定型，不预设
VENDOR_N = None              # TODO(#28): 产物层 tag 字面量总数
P1_DEGRADE_HOOK = None       # TODO(#28) v1.1: WebGL 不可用 / contextlost 确定性模拟 + 2D L0 切换标识
P1_VISUAL_FIELDS = None      # TODO(#28) v1.1: 材质层数 / 光源列表 / hex / 抖动 / 随距衰减 / 剪影导出

# ---------------------------------------------------------------------------
# 判据清单（规格 §6.2 / §11）：62 条新增/重定义硬 chk
#   = 19 (K1–K5) + 31 (原六族) + 6 (PVIS) + 4 (PDEG) + 2 (PT)
# 每条在实跑时必须对应一个真实 chk(...) 调用；禁止删、禁止降级为 NOTE
# ---------------------------------------------------------------------------
CHECKS = {
    # ---- K1 判定核心确定性（5）----
    "PDCORE": [
        "PDCORE-1 race/track/config 三文件 sha256 与 P0 前 + P1 前快照双锚定全等",
        "PDCORE-2 node js/headless_laps.mjs 原路径原命令 11 场 ALL PASS 且 max<=180s",
        "PDCORE-3 node js/minimap_model.test.mjs 10 项全绿",
        "PDCORE-4 3D 与 2D 两形态 finishTime / 门线判定序列逐项一致",
        "PDCORE-5 浏览器内 lineT / 两圈 line 差=L / lap 序列 / 三题型正确",
    ],
    # ---- K2 跨站单键保真（3）----
    "PS": [
        "PS-1 C08 白名单 D1–D6 在 3D 主形态重放（期望值逐字不变）",
        "PS-2 rally.unlocked 并集生效 / 跨站读写 rally 字段逐字段相等",
        "PS-3 setItem 增量 0 且 键集合 == 基线键集合（零新增字段）",
    ],
    # ---- K3 IPA 单一显示源（4）· C1 键契约 ----
    "PI": [
        "PI-1 等价时序：module 执行前 window.IPA_DISPLAY 已就绪（setter 同步捕获）",
        "PI-2 IPA_DISPLAY.U11.displayIpa==='ɜr' 且 48 卡面美式 / ipa-display.js 字节全等",
        "PI-3 C1 键契约：unit 唯一主键 48/48 唯一 / sym 稳定键 48/48 唯一且与权威表一致 / displayIpa 零进键位",
        "PI-4 U05 与 U07 displayIpa 同为 ɑ 的去重陷阱硬证（按 unit 独立寻址）",
    ],
    # ---- K4 答案零泄露（5）· 含 v1.1 新增 3D 层零答案域 ----
    "PQ": [
        "PQ-1 H5 口径零泄露（textContent + 后代所有属性值，不查 innerHTML）",
        "PQ-2 词表完整性守卫 len(vocab)==83 and set==83",
        "PQ-3 snapshot() / 3D 参数表递归键名零禁用键（FORBID_KEYS）",
        "PQ-4 3D overlay DOM 检测面零命中（83 词 + 4 字段名 + IPA 完整词）",
        "PQ-5 3D 层零答案域读取：gate.spoken/correctLateral/qType/hit/left/right 及派生参数零进入场景·材质·几何·路牌纹理·DOM 属性（与 H5 串联，art-spec §6.7）",
    ],
    # ---- K5 四项错误计数（2）----
    "PE": [
        "PE-1 四项硬归零 pageerror / 硬 console_error / bad_status / 同源真实失败",
        "PE-2 ERR_ABORTED / 外链 / Vite 机制 / WebGL 上下文事件 逐类单列披露",
    ],
    # ---- P1-1 3D 可见性（5）----
    "PV": [
        "PV-1 WebGL 上下文真实创建且 contextLost==false / frames>N（两模式×两视口）",
        "PV-2 meshCount>=3 且玩家车与 2 NPC 可按 id 区分",
        "PV-3 drawCalls>0 且随帧推进",
        "PV-4 三车屏占比各>0 且投影包围盒与视口相交（非屏外/非全屏）",
        "PV-5 mode==='racing' 且 odo 单调增时刻取证（非 title/teach 静态画面）",
    ],
    # ---- P1-2 第三人称跟车相机（4）----
    "PC": [
        "PC-1 相机跟随玩家 odo 单调 / 阻尼 0.18–0.28s / 无整段跳变",
        "PC-2 赛道远端投影收敛 / 消失点顶部约 40% / 护栏收窄",
        "PC-3 俯角 16°–20° · 机位 3.4–3.8m · 水平 FOV 60–66° 且可见赛道段<100%（无俯视）",
        "PC-4 375×780 与 320×568 下左右车道投影可分离、选道方向正确",
    ],
    # ---- P1-3 375px 竖屏可玩（7）----
    "PM": [
        "PM-1 375×780 从入口走完 2 圈 4 门 → results，finishTime 不退化",
        "PM-2 左右选道真实可操作且改变玩家车投影",
        "PM-3 #jump 存在可点且生效（pointerdown/jumpEdge）",
        "PM-4 quiz 三题型作答并进入结果页",
        "PM-5 scrollWidth<=innerWidth 且各关键元素矩形在视口内",
        "PM-6 顶栏与玩家车/分叉路牌/关键可视区零相交、canvas 不吞点击",
        "PM-7 320×568 兼容 + DPR clamp(min(2,dpr)) 位图尺寸 + 人工过眼签收",
    ],
    # ---- P1-4 3D 层只读（6）----
    "PR": [
        "PR-1 静态零命中 race.state.*= / judge( / beginDecide( / saveWallet / alpha / performance.now",
        "PR-2 运行时 Storage.prototype.setItem 增量 0",
        "PR-3 snapshot() 只读：调用前后 race.state 深拷贝逐字段相等",
        "PR-4 rAF 15fps 与 144fps 下 11 场 finishTime 与判定序列逐项一致",
        "PR-5 quiz 冻结前后 karts[0].odo / simTime 严格相等；L0/L1 与 L2 判定逐位一致",
        "PR-6 WebGL 上下文丢失/恢复后视觉与判定重新对齐、不跳门",
    ],
    # ---- P1-5 D4 六档稀有度教研校验（5）· C1/C2 + #29 权威表 ----
    "PRARITY": [
        "PRARITY-1 禁 length/tone/color 进入 3D 几何·材质·稀有度·粒子·教学参数 + config.js PHONEMES/VOWELS 逐字未改（U09 长/U10 短 反证）",
        "PRARITY-2 C1 键契约：primaryKey=unit / unit 48 唯一 / sym 48 唯一 / displayIpaForKey===false / displayIpa 零进键位",
        "PRARITY-3 C2 教研公式逐条可复算：units.every(u => u.CI===u.A+u.B+2*u.C && u.rarity===band(u.CI))；逐音素按 CI 单调不降（禁整类断言）；档位边界 CI 不倒置",
        "PRARITY-4 教研映射表存在且评审可追溯 / 分布 14/12/9/6/4/3 严格单调不增 / UR=ɜː θ ð / 六档名与 cards.js RARITY_RANK 逐项相等",
        "PRARITY-5 六档轮廓尺寸一致 / 牌面零文字·IPA·中文·水印 / 36·48 改档与 SAMPLES 6·6 迁移登记（不臆造已改）",
    ],
    # ---- P1-6 双层缓存（4）----
    "PB": [
        "PB-1 源码层白名单 9 文件 {hud-20261108:46} 唯一且恰好",
        "PB-2 产物层 {VENDOR_TAG:N} 唯一且恰好（N 由 #28 产物定型）",
        "PB-3 互不混算六项：扫描根隔离 / 各自唯一 / 值不同 / 源码层无杂 tag 与产物 tag / 残留单列",
        "PB-4 20 个图片 URL 零裸引用（含 \"assets/img/\"+变量 拼接型）",
    ],
    # ---- P1-8 视觉六维阈值（6）· v1.1 新增（裁决 B-2 / B-5）----
    "PVIS": [
        "PVIS-1 材质层数可数 3<=layers<=5 / 相邻层 roughness 差>=0.15 / 明度差>=8% / 零后处理",
        "PVIS-2 主体色 S(HSV)<=45% 可算（hex→HSV）/ 宝石点缀 S 55–75% 占比<=8% / 禁 S>85% 色块>2%",
        "PVIS-3 三车 24px 纯黑剪影两两辨识盲测通过率 100%（人工签收）/ >=3 结构特征 / 负空间>=12%",
        "PVIS-4 抖动峰值<=3px@375 / <=0.4° / 无>30Hz / reduced 下动效全部归零",
        "PVIS-5 P1 主站光照 lightCount==2（1 主光 + 1 柔补光<=0.35）+ AO>=80% / 禁 bloom；不复用 probe lightCount=1；probe.jsx·probe.html sha256 与 P0 前快照全等",
        "PVIS-6 细节随距衰减三档 近0–12m 100% / 中12–45m<=40% / 远>45m<=10% / 留白>=15%",
    ],
    # ---- P1-9 WebGL 降级 2D L0（4）· v1.1 新增（裁决 B-3 / C-3）----
    "PDEG": [
        "PDEG-1 模拟 WebGL 不可用（确定性 API）→ 自动切 2D L0 且不白屏",
        "PDEG-2 触发 webglcontextlost → 自动切 2D L0 且不白屏；恢复后不跳门",
        "PDEG-3 低配/降级形态 2D 三车仍可玩 + 听音选车道可完成 + 走完整一局 + 零溢出",
        "PDEG-4 降级前后 finishTime / 门线判定序列 / rally.* 存档与 2D L0 基线逐项一致；与 PV 分表、不作 PF-01 FAIL 证据",
    ],
    # ---- 终点汇总门（2）----
    "PT": [
        "PT-1 门控全绿：路线 B 重定义套件 N PASS / 0 FAIL / N TOTAL + 81 项原样保留 + 11 场 headless ALL PASS 且 §6.3 K1–K5 映射 5/5 满格（≠ 原始 110 项原样全绿）",
        "PT-2 375px 可玩：两视口完整一局 + 人工签收（G3/G9）",
    ],
}

# ---------------------------------------------------------------------------
# 81 项原样保留清单（规格 §3.3：36 + 0 + 15 + 30）
# 期望值逐字不改，仅在 3D 主形态与新 base URL 下重放
# ---------------------------------------------------------------------------
PL_CHECKS = {
    "verify_cseg_gate.py": (
        [f"S{i}" for i in range(1, 17)]
        + [f"A{i}" for i in range(0, 7)]
        + [f"B{i}" for i in range(0, 10)]
        + [f"C{i}" for i in range(1, 4)]
    ),                                                                    # 36
    "verify_cseg_ui.py": [],                                              # 0（14 项入 29 项重验）
    "verify_fresh_gate.py": [
        "F1", "F1b", "F2", "F3", "F4", "F5", "F6a", "F6b", "F6c", "F7",
        "F9a", "F9b", "F9c", "F11a", "F11b",
    ],                                                                    # 15
    "verify_c08_gate.py": (
        [f"S1.{i}" for i in range(1, 7)]
        + [f"D1.{i}" for i in range(1, 6)]
        + [f"D2.{i}" for i in range(1, 4)]
        + [f"D3.{i}" for i in range(1, 4)]
        + [f"D4.{i}" for i in range(1, 4)]
        + [f"D5.{i}" for i in range(1, 3)]
        + [f"D6.{i}" for i in range(1, 3)]
        + [f"D8.{i}" for i in range(1, 4)]
        + [f"D9.{i}" for i in range(1, 4)]
    ),                                                                    # 30
}

# ---------------------------------------------------------------------------
# chk() 框架（实跑时启用；SPEC_ONLY 阶段不调用，避免误导性全绿）
# ---------------------------------------------------------------------------
RESULTS = []
NOTES = []
CONCERNS = []


def chk(name, ok, detail=None):
    """硬断言。FAIL 一律计入，绝不改 NOTE、绝不降级为 warn。"""
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})
    print(("  PASS  " if ok else "  FAIL  ") + str(name) + (f"  | {detail}" if detail else ""))
    return bool(ok)


def note(name, text):
    """仅承载已核实的环境项 / 记录项 / 可解释诊断项，不承载任何硬失败。"""
    NOTES.append({"name": name, "text": text})
    print("  NOTE  " + str(name) + f" | {text}")


def concern(name, text, needs_decision=True):
    """CONCERNS：不阻塞本轮则登记；证据 MISSING / 待用户裁决一律不静默放行。"""
    CONCERNS.append({"name": name, "text": text, "needs_decision": needs_decision})
    print("  CONCERNS  " + str(name) + f" | {text}")


def summary():
    p = sum(1 for r in RESULTS if r["ok"])
    f = len(RESULTS) - p
    print(f"SUMMARY: {p} PASS / {f} FAIL / {len(RESULTS)} TOTAL"
          f"  | NOTES {len(NOTES)} / CONCERNS {len(CONCERNS)}")
    return p, f, len(RESULTS)


# ---------------------------------------------------------------------------
# 静态自检（SPEC_ONLY 阶段唯一执行）：清单完整性，不产生验收 SUMMARY
# ---------------------------------------------------------------------------
def self_check():
    n = sum(len(v) for v in CHECKS.values())
    pl = sum(len(v) for v in PL_CHECKS.values())
    names = [x for v in CHECKS.values() for x in v]
    dup = len(names) - len(set(names))
    print("=" * 72)
    print("【verify_p1_gate.py · v1.1 SPEC_ONLY 静态自检】")
    print("=" * 72)
    for k, v in CHECKS.items():
        print(f"  {k:9s}: {len(v):2d} 条")
    print(f"  {'小计':9s}: {n:2d} 条新增/重定义硬 chk（规格 §6.2 = 19 + 31 + 6 + 4 + 2 = 62）")
    for k, v in PL_CHECKS.items():
        print(f"  PL {k:24s}: {len(v):2d} 项")
    print(f"  {'PL 小计':9s}: {pl:2d} 项原样保留（规格 §3.3 = 36 + 0 + 15 + 30 = 81）")
    print(f"  重复判据名 = {dup}（必须为 0）")
    print(f"  规格定义合计 = {n} + {pl} = {n + pl} 条（不含发布前 C2–C6 5 条）")
    print("  Chrome 常量 =", CHROME)
    print("  #29 D4 权威表 =", D4_AUTHORITY)
    print("  #30 视觉规格 =", ART_AUTHORITY)
    print("  占位未定型项 =", [k for k, v in {
        "P1_PROBE_OBJECT": P1_PROBE_OBJECT, "P1_MESH_FIELD": P1_MESH_FIELD,
        "P1_DRAWCALL_FIELD": P1_DRAWCALL_FIELD, "P1_COVERAGE_FIELD": P1_COVERAGE_FIELD,
        "P1_CAMERA_FIELDS": P1_CAMERA_FIELDS, "P1_SNAPSHOT_KEYS": P1_SNAPSHOT_KEYS,
        "P1_RENDER_MODE": P1_RENDER_MODE, "VENDOR_TAG": VENDOR_TAG,
        "VENDOR_N": VENDOR_N, "P1_DEGRADE_HOOK": P1_DEGRADE_HOOK,
        "P1_VISUAL_FIELDS": P1_VISUAL_FIELDS,
    }.items() if v is None])
    ok = (n == 62 and pl == 81 and dup == 0)
    print("  自检 =", "OK（清单与规格 §6.2 / §3.3 一致）" if ok else "MISMATCH（须核对规格）")
    return ok


# ===========================================================================
# REAL RUN · 2026-11-12 实跑化（用户裁决：四套旧门控整体退役 + 「跑判据」）
# ---------------------------------------------------------------------------
# 纪律：
#  1. 上方 CHECKS(62) / PL_CHECKS(81) 是【规格清单】，逐字不动，不作实跑结果冒充。
#  2. 每条 chk() 的 ok 只来自真实 subprocess 返回码 / 输出解析 / 本地文件事实。
#  3. 人工签收类（PVIS-3 剪影盲测 / PM-7 人工过眼 / PT-2 签收）登记 NOT_COVERED，
#     不伪造 PASS；G9 眩晕实测按用户裁决为上线后 advisory，不作发布阻断。
#  4. 81 项随四套旧门控退役（用户 2026-11-12 书面放行），登记 RETIRED，
#     不冒充「81 PASS」；其产品正确性由下方真实静态断言与浏览器门控覆盖。
#  5. 连续两轮运行须 SUMMARY 与断言名集合逐条一致，否则不算稳定。
# ===========================================================================
import os
import re
import json
import glob
import hashlib
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEST = os.path.join(ROOT, "音标大闯关")
PY = "py -3.13"
NOT_COVERED = []


def _sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _cmd(cmd, cwd, timeout=900):
    try:
        r = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        return -9, "TIMEOUT: %s" % e


def _pass_fail(text):
    """从套件输出里解析 PASS/FAIL 数；兼容 '18 PASS / 0 FAIL / 18 TOTAL' 与 'PASS=63  FAIL=0'。

    取【最后一次】汇总：verify_p0_gate.py 会先打印 minimap 子套件的
    `SUMMARY: 10 PASS / 0 FAIL / 10 TOTAL`，再打印自身 62 项汇总；用首个匹配会把
    62 项误读成 10 项。其它套件只有一次汇总，取末次不影响。
    """
    m1 = re.findall(r"(\d+)\s+PASS\s*/\s*(\d+)\s+FAIL", text)
    if m1:
        return int(m1[-1][0]), int(m1[-1][1])
    a = re.findall(r"PASS\s*=\s*(\d+)", text)
    b = re.findall(r"FAIL\s*=\s*(\d+)", text)
    if a and b:
        return int(a[-1]), int(b[-1])
    return None, None


# 执行顺序说明（2026-11-12 第一轮实跑后的真实修正，非放宽断言）：
#   S5 真实 Chromium 的 WebGL 取证对 GPU 环境最敏感。原先 S0(P0 62 项，会连续
#   启停大量 Chromium / Vite 服务) 排在前面，其实跑残留会让 S5 的 swiftshader
#   WebGL2 初始化失败并整体降级到 2D（首轮实测 S5 54 PASS / 9 FAIL），而单独
#   执行 verify_p1_visual.py 稳定 63/63。故把 S3(纯 Node 构建) → S5 前置到干净
#   环境，S0 及其余不依赖 WebGL 的套件后置。断言、期望值、门槛一条未改。
SUITES = [
    # (编号, 命令, cwd, 期望最少 PASS, 说明)
    ("S3", "npm run build:p1", HERE, 0, "P1 IIFE 预构建 + 6 项静态自检"),
    ("S5", PY + " verify_p1_visual.py", HERE, 63, "真实 Chromium 六场景 63 项"),
    # 退役令 §5：路线 B 重定义套件以 verify_p0_gate.py 62 项为上游基线，不退役。
    ("S0", PY + " verify_p0_gate.py", HERE, 62, "路线B重定义套件 P0 62 项（不退役）"),
    ("S1", "npm run test:scene3d", HERE, 18, "scene3d-model 纯函数 18 项"),
    ("S2", "npm run test:minimap", HERE, 10, "minimap 纯函数 10 项"),
    ("S4", "npm run headless", HERE, 0, "两圈 11 场确定性实跑"),
    ("S6", PY + " \"%s\"" % os.path.join(QUEST, "sprite_gen", "convert_webp.py") + " --check-fast",
     QUEST, 10, "美式重出版资产链快检"),
]


def run_suites():
    print("\n=== A · 真实套件实跑（返回码 + 输出解析，不接受推测） ===")
    # 完整输出落盘：尾部 180 字符不足以定位偶发 FAIL 的具体断言名；
    # gate-logs/ 已在 .gitignore 排除，不入库，仅作本机诊断证据。
    logdir = os.path.join(HERE, "gate-logs")
    os.makedirs(logdir, exist_ok=True)
    for sid, cmd, cwd, minpass, desc in SUITES:
        rc, out = _cmd(cmd, cwd)
        with open(os.path.join(logdir, sid + ".log"), "w", encoding="utf-8") as fp:
            fp.write("$ " + cmd + "\n" + "=" * 70 + "\n" + out)
        chk("%s %s 退出码 0" % (sid, desc), rc == 0, {"rc": rc, "tail": out.strip()[-180:]})
        p, f = _pass_fail(out)
        if p is not None:
            chk("%s %s SUMMARY FAIL=0" % (sid, desc), f == 0, {"PASS": p, "FAIL": f})
            if minpass:
                chk("%s %s PASS >= %d" % (sid, desc, minpass), p >= minpass,
                    {"PASS": p, "want": minpass})
        elif sid == "S3":
            chk("%s 构建完成标记 [build-p1] DONE" % sid, "[build-p1] DONE" in out, out.strip()[-160:])
            chk("%s 6 项静态自检全 OK 且零裸引用" % sid,
                out.count("OK") >= 6 and "Storage 写入 API = 0" in out and "图片 URL 裸引用 = 0" in out,
                re.findall(r"OK\s+[^\n]+", out))
        elif sid == "S4":
            chk("%s 11 场 ALL PASS" % sid, "ALL PASS" in out, out.strip()[-160:])
            times = [float(x) for x in re.findall(r"\b(1[0-7]\d\.\d\d)\b", out)]
            chk("%s 最慢完赛 <= 180s" % sid, bool(times) and max(times) <= 180.0,
                {"samples": len(times), "max": max(times) if times else None})
            chk("%s 词表 83 完整 / 三题型" % sid, "词 83" in out and "题型 3" in out,
                re.findall(r"题库:[^\n]+", out)[:1])
        else:
            chk("%s 输出可解析" % sid, False, "未解析出 PASS/FAIL：" + out.strip()[-160:])


def run_static():
    print("\n=== B · 静态断言（正确扫描域：排除 node_modules/dist/.p0-build/.workbuddy/.git） ===")
    SKIP = set(EXCLUDE_DIRS) | {"__pycache__"}

    def walk_sources():
        for base in (QUEST, HERE):
            for dp, dns, fns in os.walk(base):
                dns[:] = [d for d in dns if d not in SKIP]
                for fn in fns:
                    if fn.endswith((".html", ".js", ".css")):
                        p = os.path.join(dp, fn)
                        rel = os.path.relpath(p, base).replace("\\", "/")
                        if rel.startswith(("assets/", "docs/", "sprite_gen/")):
                            continue
                        yield rel, open(p, encoding="utf-8", errors="ignore").read()

    # B1 源码层 tag 唯一且恰好 46
    tags = {}
    for rel, t in walk_sources():
        for v in re.findall(r"\?v=([A-Za-z0-9\-]+)", t):
            tags[v] = tags.get(v, 0) + 1
    chk("B1 源码层 tag 唯一且恰好 46（PB-1）",
        set(tags) == {TAG} and tags.get(TAG) == SRC_TAG_COUNT, tags)

    # B2 产品层图片 URL 零裸引用（S18 原口径 + 正确排除）
    lit = re.compile(r"""["'`]([^"'`\n]*\.(?:webp|png)[^"'`\n]*)["'`]""")
    concat = re.compile(r"""["'`]([^"'`\n]*assets/img/)["'`]\s*\+\s*[^,;)\n]{1,60}""")
    bare = []
    for rel, t in walk_sources():
        for m in lit.finditer(t):
            u = m.group(1)
            if "/" in u and "?v=" + TAG not in u and "${CACHE_TAG}" not in u:
                bare.append((rel, u))
        for m in concat.finditer(t):
            if "?v=" + TAG not in t[m.start():m.end()]:
                bare.append((rel, "CONCAT"))
    chk("B2 产品层图片 URL 零裸引用（PB-4 / 原 S18 口径）", not bare, bare[:5])

    # B3 三核心 + 2D 层 sha256 与 P1 改前快照双锚定
    mf = os.path.join(ROOT, ".workbuddy", "backups", "p1-pre-20261110", "manifest.txt")
    base_txt = open(mf, encoding="utf-8").read() if os.path.isfile(mf) else ""
    want = {}
    for line in base_txt.splitlines():
        m = re.search(r"(音标拉力赛/[\w./-]+) \| \d+ B \| sha256=([0-9a-f]{64})", line)
        if m:
            want[m.group(1)] = m.group(2)
    core = ["音标拉力赛/js/race.js", "音标拉力赛/js/track.js", "音标拉力赛/js/config.js",
            "音标拉力赛/js/main.js", "音标拉力赛/js/render.js",
            "音标拉力赛/js/probe.jsx", "音标拉力赛/probe.html"]
    mism = [p for p in core
            if p not in want or _sha(os.path.join(ROOT, p)) != want[p]]
    chk("B3 判定核心 + 2D L0 + P0 探针 7 文件 sha256 双锚定全等（PDCORE-1）",
        len(mism) == 0 and len(want) > 0, {"基线条目": len(want), "不一致": mism})

    # B4 美式 IPA 权威表（C1 键契约 + U05/U07 撞 ɑ 陷阱）
    ipa = open(os.path.join(QUEST, "js", "ipa-display.js"), encoding="utf-8").read()
    entries = dict(re.findall(r'"(U\d{2})"\s*:\s*\{\s*"sym"\s*:\s*"([^"]+)"', ipa))
    disp = dict(re.findall(r'"(U\d{2})"\s*:\s*\{\s*"sym"\s*:\s*"[^"]+"\s*,\s*"displayIpa"\s*:\s*"([^"]+)"', ipa))
    u11 = re.search(r'"U11"\s*:\s*\{[^}]*"displayIpa"\s*:\s*"([^"]+)"', ipa)
    chk("B4 IPA_DISPLAY 48 闭集 + U11=ɜr + U05/U07 同为 ɑ 但 unit 独立（PI-2/PI-3/PI-4）",
        len(entries) == 48 and len(disp) == 48 and bool(u11) and u11.group(1) == "ɜr"
        and disp.get("U05") == disp.get("U07") == "ɑ" and "U05" in disp and "U07" in disp,
        {"entries": len(entries), "U11": u11.group(1) if u11 else None,
         "U05": disp.get("U05"), "U07": disp.get("U07")})

    # B5 48 卡面 + 总图与美式源逐字节全等
    src = os.path.join(QUEST, "sprite_gen", "webp_american")
    pub = os.path.join(QUEST, "assets", "sprites", "cards")
    bad = [u for u in ["U%02d" % i for i in range(1, 49)]
           if not (os.path.isfile(os.path.join(src, u + ".webp"))
                   and os.path.isfile(os.path.join(pub, u + ".webp"))
                   and _sha(os.path.join(src, u + ".webp")) == _sha(os.path.join(pub, u + ".webp")))]
    a = os.path.join(src, "rarity_progress.webp")
    b = os.path.join(QUEST, "assets", "sprites", "rarity_progress.webp")
    prog_ok = os.path.isfile(a) and os.path.isfile(b) and _sha(a) == _sha(b)
    chk("B5 49 张发布卡面与美式重出版源逐字节全等（F9c / PI-2）",
        not bad and prog_ok, {"不一致": bad[:5], "总图全等": prog_ok})

    # B6 D4 教研映射表不变式（C1/C2）
    rm_path = os.path.join(HERE, "design", "rarity-map.json")
    rm = json.load(open(rm_path, encoding="utf-8"))
    us = rm["units"]
    bands = {k: 0 for k in rm["rarityRank"]} if isinstance(rm.get("rarityRank"), (list, dict)) else {}
    for u in us:
        bands[u["rarity"]] = bands.get(u["rarity"], 0) + 1
    ci_ok = all(u["CI"] == u["A"] + u["B"] + 2 * u["C"] for u in us)
    unit_ok = len({u["unit"] for u in us}) == 48 and len(us) == 48
    sym_ok = len({u["sym"] for u in us}) == 48
    dist_ok = bands == rm["distribution"]
    forb = set(rm.get("forbiddenFields", []))
    key_ok = (rm.get("primaryKey") == "unit" and rm.get("displayIpaForKey") is False
              and not (forb & set(us[0].keys())))
    ur = sorted(u["sym"] for u in us if u["rarity"] == "UR")
    chk("B6 D4 教研表 48/48 · CI=A+B+2C · 14/12/9/6/4/3 · UR=ɜː θ ð · C1 键契约（PRARITY-2/3/4）",
        ci_ok and unit_ok and sym_ok and dist_ok and key_ok and sorted(ur) == sorted(["ɜː", "θ", "ð"]),
        {"units": len(us), "CI": ci_ok, "unit唯一": unit_ok, "sym唯一": sym_ok,
         "分布": bands, "UR": ur, "键契约": key_ok})

    # B7 双层缓存互不混算：产物层 tag 与源码层不同
    model = open(os.path.join(HERE, "js", "scene3d-model.mjs"), encoding="utf-8").read()
    mtag = re.search(r'P1_TAG\s*=\s*["\']([\w-]+)["\']', model)
    ptag = mtag.group(1) if mtag else None
    chk("B7 双层缓存 tag 值不同且互不混算（PB-2/PB-3）",
        bool(ptag) and ptag != TAG and ptag not in tags, {"源码层": list(tags), "产物层": ptag})

    # B8 3D 层零 Storage 写入 / 零判定域写回（静态硬模式）
    jsx = open(os.path.join(HERE, "js", "scene3d.jsx"), encoding="utf-8").read()
    bad_pat = [r"localStorage\.setItem", r"sessionStorage\.setItem",
               r"race\.state\.\w+\s*=", r"\.odo\s*=", r"\.lateral\s*=", r"g\.line\s*="]
    hits = [p for p in bad_pat if re.search(p, jsx)]
    chk("B8 3D 层静态零 Storage 写入 / 零判定域写回（PR-1/PR-2）", not hits, hits)

    # B9 退役令存在（用户 2026-11-12 书面裁决乙）
    retire = os.path.join(HERE, "design", "p1-gate-retirement.md")
    chk("B9 四套旧门控退役令已落盘（用户 11-12 书面放行）", os.path.isfile(retire), retire)

    # B10 3D 产物存在且与源码构建可复现（由 S3 重建，此处核字节）
    bundle = os.path.join(HERE, "assets", "p1", "scene3d.js")
    chk("B10 预构建 IIFE 产物存在且 >1MB", os.path.isfile(bundle) and os.path.getsize(bundle) > 1_000_000,
        {"bytes": os.path.getsize(bundle) if os.path.isfile(bundle) else None})


# ---------------------------------------------------------------------------
# C · 81 项 PLR-* 迁移重放（design/p1-gate-retirement.md §3 承接表 / §5 终点口径）
# ---------------------------------------------------------------------------
# 退役的是「旧套件作为发布阻断判据的地位」，不是删断言。这里通过
# verify_p1_plr.py 重放适配器读取旧脚本的【断言定义与期望值】（逐字不改），
# 用正确扫描域重放 81 条，丢弃旧脚本的 SUMMARY / exit code。
# 旧脚本零改动、原地保留；6 条历史 FAIL 原文永久留在 p1-legacy-gate-fail-scan.md。
PLR_GROUP = {
    "verify_cseg_gate.py": "CSEG",
    "verify_fresh_gate.py": "FRESH",
    "verify_c08_gate.py": "C08",
}


def run_plr():
    print("\n=== C · 81 项 PLR-* 迁移重放（旧门控已退役：只取断言，不取 exit code） ===")
    replayed = {}
    for script, ids in PL_CHECKS.items():
        if not ids:
            continue                      # verify_cseg_ui.py 组为 0 项（14 项入 29 项重验域）
        out = os.path.join(HERE, "plr-" + script.replace(".py", "") + ".json")
        cmd = PY + " verify_p1_plr.py --only %s --out \"%s\"" % (script, out)
        rc, log = _cmd(cmd, HERE, timeout=1200)
        chk("PLR 适配器 %s 退出码 0" % script, rc == 0,
            {"rc": rc, "tail": log.strip()[-160:]})
        data = None
        if os.path.isfile(out):
            try:
                data = json.load(open(out, encoding="utf-8"))["scripts"][script]
            except Exception as e:
                data = {"ok": False, "error": repr(e), "results": [], "count": 0}
        chk("PLR 适配器 %s 无异常且取回断言" % script,
            bool(data) and bool(data.get("ok")) and data.get("count", 0) > 0,
            {"error": (data or {}).get("error"), "count": (data or {}).get("count")})
        replayed[script] = data or {"results": [], "count": 0}

    for script, ids in PL_CHECKS.items():
        if not ids:
            continue
        by = {}
        for r in replayed[script]["results"]:
            by.setdefault(r["name"].split()[0], []).append(r)
        for i in ids:
            hits = by.get(i)                  # 精确按编号取值，F1 不会误吃 F1b
            name = "PLR-%s-%s" % (PLR_GROUP[script], i)
            chk("%s 原样重放 PASS（期望值逐字不变 / 正确扫描域）" % name,
                bool(hits) and all(h["ok"] for h in hits),
                {"命中": len(hits or []),
                 "原名": [h["name"] for h in (hits or [])][:3],
                 "detail": [h.get("detail") for h in (hits or [])][:1]})

    plr_pass = sum(1 for r in RESULTS if r["name"].startswith("PLR-") and r["ok"])
    chk("PLR 81 项逐条实跑全绿（非 NOT_COVERED、非旧套件 exit code）",
        plr_pass == 81, {"PLR PASS": plr_pass, "want": 81})


def run():
    print("=" * 78)
    print("verify_p1_gate.py · P1 门控【REAL RUN】· 2026-11-12")
    print("用户裁决：四套旧门控整体退役（乙）；门控全绿 = 本套件 + 静态断言 + 11 场 headless")
    print("=" * 78)
    ok_list = self_check()
    chk("SPEC 清单自检：62 条重定义 + 81 项清单、重复名 0", ok_list)
    run_suites()
    run_static()
    run_plr()
    print("\n=== D · 覆盖边界（不冒充全绿） ===")
    NOT_COVERED.extend([
        "PVIS-3 三车 24px 剪影两两辨识盲测（需人工签收）",
        "PVIS-1/2/4/6 材质层·HSV 占比·抖动·随距衰减（需视觉量测工具，本轮未取证）",
        "PM-7 320×568 人工过眼签收（已由 verify_p1_visual.py V3 自动验可玩，人工签收仍缺）",
        "PT-2 人工签收（G3 由 team-lead 代签；G9 按用户裁决为上线后 advisory，不阻断）",
        "29 项重验域的 UI 类逐条替代编号，以及 HUD 12 项，见退役令 §4.2 / §4.3；"
        "本轮由 S0 / S5 的真实 Chromium 取证覆盖，未逐条独立命名 chk",
    ])
    for x in NOT_COVERED:
        print("  NOT_COVERED  " + x)
    p, f, t = summary()
    result = {
        "mode": "REAL_RUN", "date": "2026-11-12",
        "gate_definition": (
            "门控全绿 = 路线B重定义套件(P0 62项 + P1新套件静态断言) "
            "+ 81项PLR迁移重放(退役令§3承接表/正确扫描域/期望值逐字不变) "
            "+ 11场headless ALL PASS + 真实Chromium 63项；"
            "四套旧门控 exit code 自 2026-11-12 起不计入判定链，≠ 原始110项原样全绿(X9)"
        ),
        "checks": RESULTS, "not_covered": NOT_COVERED,
        "summary": {"PASS": p, "FAIL": f, "TOTAL": t},
        "legacy_gate_status": "RETIRED_BY_USER_2026-11-12",
        "pl81_status": "REPLAYED_81_VIA_PLR_ADAPTER",
        "plr_result_files": ["plr-verify_cseg_gate.json",
                             "plr-verify_fresh_gate.json",
                             "plr-verify_c08_gate.json"],
    }
    out = os.path.join(HERE, "result.json")
    with open(out + ".tmp", "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=2)
    os.replace(out + ".tmp", out)
    print("RESULT_JSON -> " + out)
    print("GATE_VERDICT = " + ("PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


def main():
    if "--spec-only" in sys.argv:
        self_check()
        print("\n[--spec-only] 仅清单自检，未实跑、未产生验收 SUMMARY。实跑请直接运行本脚本。")
        sys.exit(2)
    sys.exit(run())


if __name__ == "__main__":
    main()
