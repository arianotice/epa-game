/* map.js — 大地图首页：A1 全图 + 30 个关卡节点 + 毕业证书 */
(function () {
  const { $, $$, h, esc, Toast, confetti } = window.App;

  const REGION_DESC = {
    camp: "建立概念：什么是音标、嘴巴怎么工作",
    vowel: "先学乐音：20 个元音精灵，开口建立自信",
    cons: "按 6 大家族攻克 28 个阻碍音，成对对比",
    peak: "音节 · 重音 · 连读 · 毕业总复习",
  };

  function starsText(n) {
    return n > 0 ? "★".repeat(n) : "";
  }

  function render(view) {
    const data = window.IPA_DATA;
    const levels = data.levels;
    const curEp = Store.currentEp();

    /* 头部信息卡 */
    const head = h("div", { class: "map-head" },
      h("div", { class: "card" },
        h("div", { class: "big" }, curEp ? `🎯 下一站：${levelOf(curEp).title}` : "🏆 全部通关，你已毕业！"),
        h("div", { class: "small" }, curEp
          ? `${levelOf(curEp).regionName} · ${levelOf(curEp).scene}`
          : "去地图看看 48 颗全亮的宝藏格吧")
      ),
      h("button", {
        class: "btn red", onclick: () => {
          if (curEp) location.hash = "#/level/" + curEp;
          else { location.hash = "#/grad"; }
          AudioMgr.sfx("click");
        }
      }, curEp ? "继续探险 ▶" : "领取毕业证书 🎓"),
      h("button", {
        class: "btn ghost", onclick: () => { location.hash = "#/atlas"; AudioMgr.sfx("click"); }
      }, "💎 音标图鉴"),
      h("button", {
        class: "btn ghost", onclick: () => { location.href = "../音标拉力赛/index.html"; }
      }, "🏁 声音拉力赛")
    );
    view.append(head);

    /* 地图舞台 */
    const stage = h("div", { class: "map-stage" },
      h("img", { class: "bg", src: "assets/img/a1.webp?v=hud-20261108", alt: "英语音标大地图：出发营地到进阶峰的四幕探险全图", draggable: "false" })
    );
    data.regions.forEach((r) => {
      stage.append(h("div", {
        class: "region-badge", style: `left:${r.badge.x}%;top:${r.badge.y}%`
      }, `${r.name}｜${r.sub}`));
    });
    levels.forEach((lv, i) => {
      const st = Store.starsOf(lv.ep);
      const unlocked = Store.isUnlocked(lv.ep);
      const isCur = lv.ep === curEp;
      const cls = "node" + (unlocked ? "" : " locked") + (st > 0 ? " done" : "") + (isCur ? " current" : "");
      const btn = h("button", {
        class: cls, style: `left:${lv.node.x}%;top:${lv.node.y}%`,
        title: unlocked ? `${lv.ep} ${lv.title}` : "先通过上一关才能解锁哦",
        onclick: () => {
          if (!unlocked) { Toast.show("🔒 先通过上一关，才能解锁这一关！"); AudioMgr.sfx("wrong"); return; }
          AudioMgr.sfx("click");
          location.hash = "#/level/" + lv.ep;
        }
      },
        h("span", { class: "n-ep" }, lv.ep.replace("EP", "")),
        h("span", { class: "n-st" }, unlocked ? (st > 0 ? starsText(st) : (isCur ? "出发" : "▶")) : "🔒")
      );
      stage.append(btn);
    });
    view.append(h("div", { class: "map-wrap" }, stage));

    /* 图例 */
    const legend = h("div", { class: "map-legend" },
      h("span", null, h("i", { class: "dot", style: "background:var(--red)" }), "清辅音 · 松元音"),
      h("span", null, h("i", { class: "dot", style: "background:var(--green)" }), "浊辅音 · 鼻音"),
      h("span", null, h("i", { class: "dot", style: "background:var(--blue)" }), "紧元音 · 半元音"),
      h("span", null, h("i", { class: "dot", style: "background:var(--purple)" }), "双元音滑梯"),
      h("span", null, "⭐ 已获星星"), h("span", null, "🔒 未解锁"),
      h("span", null, "点击发光的关卡开始探险")
    );
    view.append(legend);

    /* 四大区简介 */
    const regionCards = h("div", {
      style: "display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:16px;"
    });
    data.regions.forEach((r) => {
      regionCards.append(h("div", { class: "card" },
        h("div", { class: "card-title" }, `🗺️ ${r.name}`),
        h("div", { style: "font-size:13.5px;color:var(--ink-soft)" }, REGION_DESC[r.id]),
        h("div", { style: "font-size:13px;margin-top:6px;color:var(--gold-deep);font-weight:700" }, r.sub)
      ));
    });
    view.append(regionCards);

    /* 毕业横幅 */
    if (Store.allCleared()) {
      const banner = h("div", { class: "card diploma", style: "margin-top:16px;" },
        h("img", { src: "assets/img/cover.webp?v=hud-20261108", alt: "声音探险队毕业封面" }),
        h("h2", null, "🎓 声音探险队 · 毕业证书"),
        h("p", null, "48 个音标精灵全部收集，30 座关卡全部通关！"),
        h("p", null, "「看到任何一个单词，都能自信地把它读出来——这才是真正的毕业。」"),
        h("button", { class: "btn", onclick: () => { location.hash = "#/grad"; } }, "查看毕业证书")
      );
      view.append(banner);
    }
  }

  function levelOf(ep) {
    return window.IPA_DATA.levels.find((l) => l.ep === ep);
  }

  /* 毕业证书页 */
  function renderDiploma(view) {
    const data = window.IPA_DATA;
    view.append(h("div", { class: "card diploma" },
      h("img", { src: "assets/img/cover.webp?v=hud-20261108", alt: "声音探险队封面" }),
      h("h2", null, "🎓 毕 业 证 书"),
      h("p", null, "兹证明"),
      h("p", { style: "font-size:20px;font-weight:700;color:var(--ink)" }, "声音探险队队员"),
      h("p", null, "已完成 出发营地 → 元音城堡 → 辅音王国 → 进阶峰 全部 30 座关卡，"),
      h("p", null, "收集全部 48 个音标精灵，获得 " + Store.totalStars() + " 颗星星。"),
      h("div", { class: "result-stars" }, "⭐".repeat(3)),
      h("p", { style: "font-size:13.5px" }, "波波队长 & 小 Q 颁发 · " + new Date().toLocaleDateString("zh-CN")),
      h("div", { class: "result-actions" },
        h("button", { class: "btn", onclick: () => { location.hash = "#/map"; } }, "回到地图"),
        h("button", { class: "btn ghost", onclick: () => { confetti(); AudioMgr.sfx("fanfare"); } }, "撒花庆祝 🎉")
      )
    ));
    confetti();
    AudioMgr.sfx("fanfare");
  }

  window.MapView = { render, renderDiploma };
})();
