# 音标精灵资产管线厘清 · 美式重出版权威链

> 2026-11-10 · team-lead 本地收口（用户授权「我自己用本地工具收口」）
> 对应请求：**「厘清管线，需要根据美式重出版来」**
> 本轮边界：**只修脚本 + 只写文档 + 只做只读校验**；零重出、零改线上资产、零部署、零上线、零 commit。
> 上游只读评估：`design/p1-sprite-reaudit-impact.md`（F2 / RR3 / §7 前置 a）

---

## §0 一句话结论

线上 49 张卡面来自 **2026-11-06 的美式重出版**（`cards_american/ → webp_american/ → assets/sprites/`），
但 `sprite_gen/convert_webp.py` 仍硬编码 **英式基线 `sprite_gen/cards/`** 作为卡面源。
一次无意重跑就会把英式 DJ IPA 大字（`iː / ɒ / əʊ / ɪə / eə / ʊə`、`U11=ɜː`）覆盖回已上线图鉴。

**本轮已把脚本改为美式权威链，并加结构守卫 + 只读校验；线上资产一个字节都没动。**

---

## §1 唯一权威链（勿再混用）

```
[文案/数据]  音标大闯关/js/ipa-display.js  window.IPA_DISPLAY
             = 唯一权威美式显示源（U11=ɜr / U18=ɪr / U19=ɛr / U20=ʊr）
             sprite_gen/manifest.json  = 每 unit 的 displayIpa + sym + rarity + name
                │  sym 是英式 IPA 稳定键：只作存档/查表/去重/角标，禁止改、禁止当主键
                │  displayIpa 面向用户：零进键位（U05/U07 同为 ɑ，用它会丢 U07）
                ▼
[立绘 PNG]   gen_sprites.py (Agnes) → unkey_white.py (flood-fill 抠白底)
             → sprite_gen/sprites/U01..U48.png      48 张，本体不含文字
[卡面 PNG]   compose_cards.py  (Pillow 精确合成，防 AI 乱码)
             → sprite_gen/cards_american/            48 张单卡 + rarity_progress.png
                ▼
[转换]       convert_webp.py  ← 本轮修正点
             卡面 RGB / quality=90 / method=6 ；总图 quality=86 / method=6
             立绘 RGBA / quality=90 / method=6
                ├──→ sprite_gen/webp_american/       中间产物 = 门控权威源（不发布）
                └──→ assets/sprites/cards/U*.webp    发布目录 ┐ 同一份字节，
                     assets/sprites/rarity_progress.webp     │ 不做二次编码
                     assets/sprites/U*.webp (立绘)          ┘
                ▼
[发布]       音标大闯关/deploy.sh : scp -r assets/sprites → /var/www/ipaquest/assets/
             （另含音标拉力赛/ 同源同级部署，本轮只改脚本、不执行）
                ▼
[门控]       verify_fresh_gate.py:252  F9c
             以 sprite_gen/webp_american/ 为 49 张发布卡面的逐字节比对源
```

**已作废：`sprite_gen/cards/`（50 文件，2026-11-03 英式 DJ IPA 基线）**
只作历史留档，**不删除、只隔离**，严禁作为任何发布资产来源。

---

## §2 本轮改了什么

| 文件 | 动作 | 说明 |
|---|---|---|
| `音标大闯关/sprite_gen/convert_webp.py` | **重写** | `CARD = "sprite_gen/cards"` → `CARDS_AMERICAN = cards_american/`；新增 `webp_american/` 中间产物写入；路径改为基于 `__file__` 的绝对路径（可从任意目录运行）；新增 `--check-fast` / `--check` / `--write` 三模式，默认只读 |
| `音标拉力赛/design/asset-pipeline-american.md` | 新建 | 本文 |
| `音标拉力赛/design/p1-sprite-reaudit-impact.md` | 追加状态 | F2 / RR3 / §7 前置 a 标记 CLOSED |
| 线上 48 张卡面 + 六档总图 + 48 张立绘 | **零改动** | 只做只读 hash/cmp，未调 `--write` |
| `compose_cards.py` / `manifest.json` / `js/data.js` / `js/cards.js` | **零改动** | 见 §4 下一轮硬阻断 |

**新增守卫**（`--write` 前整体中止，绝不部分覆盖）：
1. `cards_american/` 恰好 48 张 `U*.png` 且 `U01..U48` 无缺号；
2. `cards_american/rarity_progress.png` 存在；
3. `sprites/` 恰好 48 张且无缺号；
4. 权威源目录尾名必须是 `cards_american`，且绝不与 `cards/` 同路径。

---

## §3 实证结果（本地实跑，非推断）

环境：Node v22.22.2 / `py -3.13` + Pillow 12.3.0。

| 验证 | 结果 |
|---|---|
| 全量 `cmp`：`webp_american/U01..U48.webp` vs `assets/sprites/cards/U*.webp` | **48 / 48 全等，diff=0** |
| `webp_american/rarity_progress.webp` vs `assets/sprites/rarity_progress.webp` | **全等**（91442 B / sha `76161bf3b5fd9fe8`） |
| 美式 PNG 重编码复现（5 抽样 U01/U11/U18/U05/U48） | **5/5 MATCH** → `webp_american/` |
| 美式总图 `rarity_progress.png` q86 重编码 | **MATCH** |
| 立绘 `sprites/*.png` RGBA q90 重编码（U01/U11/U48） | **3/3 MATCH** → `assets/sprites/` |
| **英式基线 `cards/*.png` q90 重编码 vs 线上（4 抽样）** | **4/4 全不等**（如 U01 英式 `fdcaca82303ef594` vs 线上 `5fb52dc2d22bb984`）→ 线上确非英式 |
| `convert_webp.py --check-fast` | **PASS=10 / FAIL=0** |
| `convert_webp.py --check`（146 次字节比对 + 4 条英式隔离实证） | **PASS=20 / FAIL=0** |

复跑命令（大闯关根目录下，或从任意目录用绝对路径）：
```bash
py -3.13 sprite_gen/convert_webp.py --check-fast   # 秒级，纯 cmp + 结构守卫
py -3.13 sprite_gen/convert_webp.py --check        # 约 2-4 分钟，全量重编码复现
py -3.13 sprite_gen/convert_webp.py --write        # 重建；需人工确认，本轮未执行
```

> 坑位记录：初版守卫用「扫描自身源码中是否含 `CARD = "sprite_gen/cards"`」做静态断言，
> 结果扫到守卫自己的字符串字面量而自命中假 FAIL；已改为运行时路径语义断言。
> 另一坑：默认 `python` 无 Pillow，须用 `py -3.13`；纯 `cmp` 比对可无依赖完成。

---

## §4 尚未解决 · 下一轮 D4 重出的硬阻断（本轮明确不处理）

用户 2026-11-10 问卷已拍板 **「先落教研表，资产另立一轮」**，本轮零重出。
但下一轮开工前必须先解决以下已坐实的矛盾，否则会把错误固化进已上线图鉴：

### 4.1 档位有 4 份旧数据源，且与已 ACCEPTED 教研表不一致

| 数据源 | 六档分布 P/SR/SAR/HR/SSR/UR | 状态 |
|---|---|---|
| `sprite_gen/manifest.json`（`compose_cards.py` 实读 `m["rarity"]`） | **5/17/10/8/4/4** | 旧，当前线上卡面 / 立绘光环按此 |
| `音标大闯关/js/data.js`（96 处 = 48 unit × 2） | **10/34/20/16/8/8**（= 旧分布 ×2） | 旧，运行时图鉴 |
| `音标拉力赛/js/cards.js`（48 处） | **5/17/10/8/4/4** | 旧，拉力赛车库 |
| `compose_cards.py RAR_META` / `image_profiles.py` / `atlas.js` | 六档中文名与配色元数据 | 旧 |
| **`音标拉力赛/design/rarity-map.json`** | **14/12/9/6/4/3** | **ACCEPTED · 用户认可现版**，但**未生效、未入库** |

公式 `CI = A + B + 2*C`；`UR = ɜː θ ð`；主键 `unit`（U01…U48，48/48 唯一），
`sym` 仅附带校验，`displayIpaForKey=false`。

**结论**：`rarity-map.json` 与 4 份旧源 **36/48 个 unit 档位不同**。
若下一轮直接跑 `compose_cards.py` 而不先统一唯一权威源，会重出一批仍按旧档的卡面，
与已 ACCEPTED 教研表自相矛盾。**须先定主从关系与同步顺序，再原子替换。**

### 4.2 立绘光环是 baked 像素，不是后期文字层

`gen_sprites.py` 的 AI prompt 内嵌了旧档光晕；`unkey_white.py` 只抠白底。
因此「只重出卡面文字层、立绘不动」不可行，会产生肉眼可见的档位错配
（详见 `p1-sprite-reaudit-impact.md` §5：P 档 14 张里 10 张带绿星）。
下一轮预算按 **85 张全量重出**（36 立绘 + 48 卡面 + 1 总图）估。

### 4.3 其它下一轮前置

- `js/data.js` 后半段 48 处 `rarity` 是否同步（本轮核实为 96 处，即两份表）；
- SAMPLES 6 个 unit 重选、六档总图 `desc` 文案按 CI 口径重写；
- 全站缓存串 `?v=hud-20261108` 共 46 处需统一 bump，否则老用户卡面走旧缓存；
- D5 参数化精灵造型（允许改原 2D 标志性造型）建议不搭车，单独排期。

---

## §5 发布链路与已知陷阱

`deploy.sh` 只 scp `assets/sprites/`，本地中间产物 `sprite_gen/webp_american/` 与
`sprite_gen/cards_american/` **不发布**，这是正确分工（门控权威源留在本地/CI）。

**Caddy 陷阱（历史已登记，务必沿用）**：线上对任意不存在路径（含 `.opus` / `.webp`）
可能 fallback 返回 `index.html` 且 HTTP 200。**判定资源是否真送达必须比对字节数 / magic /
sha256 / Content-Type 非 `text/html`，绝不轻信状态码。**
`verify_fresh_gate.py` F9c 正是按 sha256 逐字节做的，勿改成状态码断言。

**当前状态**：本轮未部署、未上线、未 commit、未建 git 仓库。
Phase B（门控全绿后建仓全量纳入 + 同源部署 + commit）仍受
「先做 3D 卡丁车再上线」「D6 终点 = 门控全绿 + 375px 可玩」约束，须用户放行。

---

*本文只记录已实证事实与待办口径，未替用户放行任何资产重出 / 改档 / 退役动作。*
