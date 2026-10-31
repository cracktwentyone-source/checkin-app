// semete のサービスワーカー(ページを端末に保存して、圏外でも開けるようにする)
// 中身を変えたら SHELL の番号を上げる(v1 → v2)。古い保存は自動で消える。
const SHELL = 'semete-shell-v1';
const LIBS = 'semete-libs-v1';      // 地図の仕組み(MapLibre)と書体。番号付きの版なので一度取れば変わらない
const ROUTES = 'routes-v1';          // 「端末に保存」した路線ファイル(ページ側が管理。ここでは消さない)

// アプリの本体。ここに書いたものは最初に開いたときに保存する
const SHELL_FILES = [
  './route.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './icons/favicon-32.png',
];
const LIB_FILES = [
  'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js',
  'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css',
];

self.addEventListener('install', e => {
  e.waitUntil((async () => {
    const shell = await caches.open(SHELL);
    await shell.addAll(SHELL_FILES);
    // 外部の部品は取れなくても入れ替えを止めない(あとで使ったときに保存する)
    const libs = await caches.open(LIBS);
    await Promise.all(LIB_FILES.map(u => libs.add(new Request(u, { mode: 'cors' })).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) {
      if (k.startsWith('semete-') && k !== SHELL && k !== LIBS) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

// 電波があれば新しいものを取り、無いか遅ければ保存したものを使う
async function networkFirst(req, cacheName, timeoutMs) {
  const cache = await caches.open(cacheName);
  try {
    const res = await Promise.race([
      fetch(req),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), timeoutMs)),
    ]);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    throw err;
  }
}
// 保存したものをすぐ使い、裏で新しいものを取っておく
async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  if (hit) return hit;
  const res = await fetch(req);
  if (res && (res.ok || res.type === 'opaque')) cache.put(req, res.clone());
  return res;
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 背景の地図の画像は保存しない(OSMの決まりで、まとめて保存しないため。地理院も同じ扱い)
  if (/cyberjapandata\.gsi\.go\.jp|tile\.openstreetmap\.org/.test(url.host)) return;

  // 地図の仕組み(unpkg)と書体(Google Fonts)
  if (url.host === 'unpkg.com' || url.host === 'fonts.googleapis.com' || url.host === 'fonts.gstatic.com') {
    e.respondWith(cacheFirst(req, LIBS));
    return;
  }

  if (url.origin !== self.location.origin) return;

  // ページ本体とアイコン:電波があれば新しい版(4秒待って来なければ保存した版)
  if (req.mode === 'navigate' || SHELL_FILES.some(f => url.pathname.endsWith(f.replace('./', '/')))) {
    e.respondWith(networkFirst(req, SHELL, 4000));
    return;
  }

  // 路線の一覧と路線ファイル:電波があればそのまま取り、無ければ保存したもの(「端末に保存」した分もここで使える)
  if (url.pathname.endsWith('/routes.json') || url.pathname.includes('/routes/')) {
    e.respondWith((async () => {
      try {
        const res = await fetch(req);
        if (res.ok && url.pathname.endsWith('/routes.json')) (await caches.open(SHELL)).put(url.pathname, res.clone());
        return res;
      } catch (err) {
        const hit = (await caches.match(url.pathname, { ignoreSearch: true })) || (await caches.match(req, { ignoreSearch: true }));
        if (hit) return hit;
        throw err;
      }
    })());
  }
});
