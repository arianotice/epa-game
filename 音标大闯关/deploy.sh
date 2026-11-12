#!/usr/bin/env bash
# 《音标大闯关》部署脚本 —— 把四项新功能推送到腾讯云 Lighthouse (192.144.226.216)
# 用法（本地 Git Bash）：  bash deploy.sh
# 运行后会提示输入 SSH 密码（用户 ubuntu，密码登录）。
set -e

SRC="/c/Users/86135/WorkBuddy/英语音标播客/音标大闯关"
RALLY="/c/Users/86135/WorkBuddy/英语音标播客/音标拉力赛"
HOST="ubuntu@192.144.226.216"
DEST="/var/www/ipaquest"

echo "==> [1/3] 增量同步 index.html js/ css/ assets/sprites/ 与 assets/audio/ph/（48音标真人录音短音）"
scp -r "$SRC/index.html" "$HOST:$DEST/"
scp -r "$SRC/js"  "$HOST:$DEST/"
scp -r "$SRC/css" "$HOST:$DEST/"
scp -r "$SRC/assets/sprites" "$HOST:$DEST/assets/"
scp -r "$SRC/assets/audio/ph" "$HOST:$DEST/assets/audio/"

# Task #28 / P1 · 同源同级部署：拉力赛 index.html 用 ../音标大闯关/... 引用跨目录资源，
# 两站必须挂在同一 origin 的同级目录。静态源码形态直接 scp（不跑 Vite / 不装依赖）。
# assets/p1/scene3d.js 是 js/build-p1.mjs 预构建的自包含 IIFE，随源码一起上线。
# 注意：本轮只改脚本、不执行部署（SSH 交互式密码是硬阻断）。
echo "==> [2/3] 同源同级部署 音标拉力赛/（3D 主形态 + 2D L0 降级层，纯静态源码）"
ssh "$HOST" "mkdir -p $DEST/音标拉力赛 $DEST/音标拉力赛/assets"
scp -r "$RALLY/index.html" "$RALLY/probe.html" "$RALLY/vendor.manifest.json" "$HOST:$DEST/音标拉力赛/"
scp -r "$RALLY/css" "$RALLY/js" "$RALLY/audio" "$HOST:$DEST/音标拉力赛/"
scp -r "$RALLY/assets/p1" "$HOST:$DEST/音标拉力赛/assets/"

echo "==> [3/3] 重新加载 Caddy 使静态资源生效"
ssh "$HOST" "sudo caddy reload --config /etc/caddy/Caddyfile && echo RELOADED"

echo ""
echo "✅ 部署完成，访问 http://192.144.226.216/ 与 http://192.144.226.216/音标拉力赛/"

# ===== 如需全量覆盖（含 assets/、index.html 等），先备份再改用下面两行 =====
# ssh "$HOST" "sudo cp -r $DEST $DEST.bak-$(date +%Y%m%d)"
# scp -r "$SRC/." "$HOST:$DEST/"
# ssh "$HOST" "sudo caddy reload --config /etc/caddy/Caddyfile"
