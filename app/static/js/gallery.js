// 헤더 히드업
(function(){
  const hdr = document.querySelector('.site-header');
  if(!hdr) return;
  let last = window.scrollY, pinned = true;
  const pin   = ()=>{ if(!pinned){ hdr.style.transform='translateY(0)'; pinned=true; } };
  const unpin = ()=>{ if(pinned){ hdr.style.transform='translateY(-100%)'; pinned=false; } };
  hdr.style.transform='translateY(0)';
  hdr.style.transition='transform 220ms ease';
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if(y > last && y > 80) unpin(); else pin();
    last = y;
  }, {passive:true});
})();

// 연도 필터
(function(){
  const sel = document.getElementById('yearFilter');
  const cards = Array.from(document.querySelectorAll('.photo-card'));
  if(!sel || !cards.length) return;
  sel.addEventListener('change', () => {
    const y = sel.value;
    cards.forEach(c => {
      const ok = (y === 'all') || (c.dataset.year === y);
      c.style.display = ok ? 'inline-block' : 'none';
    });
  });
})();

// 로딩 페이드
(function(){
  const cards = document.querySelectorAll('.photo-card');
  if(!cards.length) return;
  if(!('IntersectionObserver' in window)){
    cards.forEach(c => c.setAttribute('data-inview','1')); return;
  }
  const io = new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        e.target.setAttribute('data-inview','1');
        io.unobserve(e.target);
      }
    });
  }, { rootMargin: '80px 0px', threshold: 0.06 });
  cards.forEach(c=>{ c.setAttribute('data-inview','0'); io.observe(c); });
})();

/* ================= Lightbox ================= */
(function(){
  const root = document.getElementById('glightbox');
  if(!root) return;

  const img = root.querySelector('#glbx-img');
  const titleEl = root.querySelector('#glbx-title');
  const metaEl = root.querySelector('#glbx-meta');

  const cards = Array.from(document.querySelectorAll('.photo-card'));
  const data = cards.map((a, idx) => ({
    idx,
    id: a.dataset.id,
    url: a.dataset.url,
    title: a.dataset.title || '',
    year: a.dataset.year || '',
    tags: (a.dataset.tags || '').split(',').filter(Boolean),
    exif: (()=>{ try{ return JSON.parse(a.dataset.exif || '{}'); }catch(_){ return {}; } })(),
    lat: a.dataset.lat ? parseFloat(a.dataset.lat) : null,
    lon: a.dataset.lon ? parseFloat(a.dataset.lon) : null
  }));

  const prevBtn = root.querySelector('[data-action="prev"]');
  const nextBtn = root.querySelector('[data-action="next"]');

  let cur = -1;
  let zoom = 1;

  const LABELS_KO = {
    'Make': '제조사',
    'Model': '카메라',
    'LensModel': '렌즈',
    'FNumber': '조리개',
    'ExposureTime': '셔터 속도',
    'ISOSpeedRatings': '감도(ISO)',
    'FocalLength': '초점거리',
    'DateTimeOriginal': '촬영일시',
    'DateTimeDigitized': '디지털화일시'
  };

  const geoCache = new Map();
  async function reverseGeocode(lat, lon){
    const key = `${lat},${lon}`;
    if(geoCache.has(key)) return geoCache.get(key);
    try{
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}&zoom=10&addressdetails=1`;
      const res = await fetch(url, { headers: { 'Accept': 'application/json' }});
      if(!res.ok) throw new Error('geocode failed');
      const data = await res.json();
      const addr = data.address || {};
      const city = addr.city || addr.town || addr.village || addr.county || '';
      const country = addr.country || '';
      const out = { country, city };
      geoCache.set(key, out);
      return out;
    }catch(e){
      return { country:'', city:'' };
    }
  }

  async function fillPanel(d){
    titleEl.textContent = d.title || d.id || '';
    metaEl.innerHTML = '';

    const rows = [];
    // 촬영일/연도 우선
    if(d.exif && (d.exif.DateTimeOriginal || d.exif.DateTimeDigitized)){
      rows.push([LABELS_KO['DateTimeOriginal'], d.exif.DateTimeOriginal || d.exif.DateTimeDigitized]);
    }
    if(d.year && d.year !== 'unknown'){
      rows.push(['연도', d.year]);
    }

    // 위치 (좌표 → 나라/도시)
    if(d.lat && d.lon){
      rows.push(['좌표', `${d.lat}, ${d.lon}`]);
      const place = await reverseGeocode(d.lat, d.lon);
      if(place.country || place.city){
        rows.push(['위치', [place.country, place.city].filter(Boolean).join(' / ')]);
      }
    }

    // EXIF 핵심
    const want = ['Make','Model','LensModel','FNumber','ExposureTime','ISOSpeedRatings','FocalLength'];
    want.forEach(k=>{
      const v = d.exif?.[k];
      if(v){
        const label = LABELS_KO[k] || k;
        rows.push([label, String(v)]);
      }
    });

    for(const [k,v] of rows){
      const dt = document.createElement('dt'); dt.textContent = k;
      const dd = document.createElement('dd'); dd.textContent = v;
      metaEl.appendChild(dt); metaEl.appendChild(dd);
    }
  }

  function open(){
    root.hidden = false;
    root.setAttribute('aria-hidden','false');
    document.documentElement.classList.add('glibx-open');
    if(matchMedia('(pointer:coarse)').matches) root.classList.add('touch');
    else root.classList.remove('touch');
  }

  function close(){
    root.hidden = true;
    root.setAttribute('aria-hidden','true');
    document.documentElement.classList.remove('glibx-open');
    zoom = 1; img.style.transform = 'scale(1)';
    if(history.state?.glbx) history.back();
  }

  function showAt(index, dir){
    if(index < 0 || index >= data.length) return;
    cur = index; zoom = 1; img.style.transform = 'scale(1)';
    const d = data[cur];

    const wrap = root.querySelector('.glbx-image-wrap');
    wrap.classList.remove('enter-from-left','enter-from-right');
    if(dir==='left') wrap.classList.add('enter-from-left');
    if(dir==='right') wrap.classList.add('enter-from-right');

    img.src = d.url;
    img.alt = d.title || d.id || '';
    fillPanel(d);

    const target = `/gallery/photo/${encodeURIComponent(d.id)}`;
    if(location.pathname !== target){
      history.pushState({glbx:true, id:d.id}, '', target);
    }
  }

  function openById(id){
    const index = data.findIndex(x => x.id === id);
    if(index === -1) return false;
    open();
    showAt(index);
    return true;
  }

  // 카드 클릭 → 라이트박스
  cards.forEach((a, i)=>{
    a.addEventListener('click', (e)=>{
      e.preventDefault();
      open(); showAt(i);
    });
  });

  // 컨트롤
  root.addEventListener('click', (e)=>{
    const act = e.target?.dataset?.action;
    if(act==='close') close();
    if(act==='prev') showAt(Math.max(0, cur-1), 'left');
    if(act==='next') showAt(Math.min(data.length-1, cur+1), 'right');
  });

  // 이미지 영역 좌/우 클릭
  root.querySelector('.glbx-image-wrap').addEventListener('click', (e)=>{
    if(e.target !== img) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if(x < rect.width/2) showAt(Math.max(0, cur-1), 'left');
    else showAt(Math.min(data.length-1, cur+1), 'right');
  });

  // 키보드
  window.addEventListener('keydown', (e)=>{
    if(root.hidden) return;
    if(e.key==='Escape') close();
    if(e.key==='ArrowLeft') showAt(Math.max(0, cur-1), 'left');
    if(e.key==='ArrowRight') showAt(Math.min(data.length-1, cur+1), 'right');
  });

  // 더블클릭 줌
  img.addEventListener('dblclick', ()=>{
    zoom = (zoom === 1 ? 1.75 : 1);
    img.style.transform = `scale(${zoom})`;
  });

  // 터치: 좌우 스와이프 / 위로 닫기
  (function(){
    let sx=0, sy=0, dx=0, dy=0, active=false;
    const TH=40;
    root.addEventListener('touchstart', (e)=>{
      if(root.hidden) return;
      active = true; sx = e.touches[0].clientX; sy = e.touches[0].clientY;
    }, {passive:true});
    root.addEventListener('touchmove', (e)=>{
      if(!active) return;
      dx = e.touches[0].clientX - sx; dy = e.touches[0].clientY - sy;
    }, {passive:true});
    root.addEventListener('touchend', ()=>{
      if(!active) return; active=false;
      if(Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > TH){
        if(dx > 0) showAt(Math.max(0, cur-1), 'left');
        else showAt(Math.min(data.length-1, cur+1), 'right');
      }else if(dy < -TH){
        close();
      }
      dx=dy=0;
    });
  })();

  // 히스토리/딥링크 대응
  window.addEventListener('popstate', ()=>{
    const m = location.pathname.match(/\/gallery\/photo\/(.+)$/);
    if(m){
      const id = decodeURIComponent(m[1]);
      if(root.hidden){
        if(!openById(id)){
          history.replaceState({}, '', '/gallery/');
        }
      }else{
        const i = data.findIndex(x=>x.id===id);
        if(i>=0) showAt(i);
      }
    }else{
      if(!root.hidden) close();
    }
  });

  // 첫 로드가 /gallery/photo/:id 면 자동 오픈
  (function initFromURL(){
    const m = location.pathname.match(/\/gallery\/photo\/(.+)$/);
    if(m){
      const id = decodeURIComponent(m[1]);
      openById(id);
    }
  })();
})();
