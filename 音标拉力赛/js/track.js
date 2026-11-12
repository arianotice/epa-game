/* 俯视椭圆赛道。世界坐标 y 向下，与画布一致。1 单位约等于画面上的 1 像素量级。 */

export function createTrack(tuning) {
  const S = tuning.straight;
  const R = tuning.radius;
  const pts = [];

  const addLine = (x0, y0, x1, y1, n) => {
    for (let i = 0; i < n; i++) {
      const u = i / n;
      pts.push({ x: x0 + (x1 - x0) * u, y: y0 + (y1 - y0) * u });
    }
  };
  const addArc = (cx, cy, r, a0, a1, n) => {
    for (let i = 0; i < n; i++) {
      const u = i / n;
      const a = a0 + (a1 - a0) * u;
      pts.push({ x: cx + Math.cos(a) * r, y: cy + Math.sin(a) * r });
    }
  };

  addLine(-S / 2, R, S / 2, R, 180);
  addArc(S / 2, 0, R, Math.PI / 2, -Math.PI / 2, 80);
  addLine(S / 2, -R, -S / 2, -R, 180);
  addArc(-S / 2, 0, R, -Math.PI / 2, -Math.PI * 1.5, 80);

  const lens = [0];
  for (let i = 1; i < pts.length; i++) lens.push(lens[i - 1] + dist(pts[i - 1], pts[i]));
  const total = lens[lens.length - 1] + dist(pts[pts.length - 1], pts[0]);

  function atDist(d) {
    d = ((d % total) + total) % total;
    let lo = 0;
    let hi = lens.length - 1;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (lens[mid] <= d) lo = mid;
      else hi = mid - 1;
    }
    const i2 = (lo + 1) % pts.length;
    const span = i2 === 0 ? total - lens[lo] : lens[i2] - lens[lo];
    const u = span > 0.0001 ? (d - lens[lo]) / span : 0;
    const a = pts[lo];
    const b = pts[i2];
    return {
      x: a.x + (b.x - a.x) * u,
      y: a.y + (b.y - a.y) * u,
    };
  }

  function sample(t) {
    let tt = t % 1;
    if (tt < 0) tt += 1;
    const d = tt * total;
    const p = atDist(d);
    const ahead = atDist(d + 160);
    const back = atDist(d - 160);
    let fx = ahead.x - back.x;
    let fy = ahead.y - back.y;
    const fl = Math.hypot(fx, fy) || 1;
    fx /= fl;
    fy /= fl;
    return { x: p.x, y: p.y, fx, fy, rx: -fy, ry: fx, t: tt };
  }

  const samples = [];
  const N = 520;
  for (let i = 0; i < N; i++) samples.push(sample(i / N));

  return { length: total, sample, samples, roadHalf: tuning.roadHalf };
}

export function offsetPoint(s, lateral) {
  return { x: s.x + s.rx * lateral, y: s.y + s.ry * lateral };
}

function dist(a, b) {
  return Math.hypot(b.x - a.x, b.y - a.y);
}
