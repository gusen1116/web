// app/static/js/gallery.js
// 헤더 숨김 기능
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

// 연도 필터 (페이지 새로고침 없이 동적 필터링으로 수정)
(function(){
  const sel = document.getElementById('yearFilter');
  if(!sel) return;
  const cards = Array.from(document.querySelectorAll('.photo-card'));
  if(!cards.length) return;

  sel.addEventListener('change', () => {
    const selectedYear = sel.value;
    
    cards.forEach(card => {
      const cardYear = card.dataset.year;
      if (selectedYear === 'all' || cardYear === selectedYear) {
        card.style.display = '';
      } else {
        card.style.display = 'none';
      }
    });
  });
})();

/* ================= Lightbox (업그레이드) ================= */
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
    lon: a.dataset.lon ? parseFloat(a.dataset.lon) : null,
    map_url: a.dataset.mapUrl || null
  }));

  let cur = -1;

  const METADATA_MAP = {
    'Make': { label: '제조사', icon: 'fa-solid fa-industry' },
    'Model': { label: '카메라', icon: 'fa-solid fa-camera' },
    'LensModel': { label: '렌즈', icon: 'fa-solid fa-circle-dot' },
    'FNumber': { label: '조리개', icon: 'fa-regular fa-circle' },
    'ExposureTime': { label: '셔터 속도', icon: 'fa-solid fa-stopwatch' },
    'ISOSpeedRatings': { label: 'ISO', icon: 'fa-solid fa-sliders' },
    'FocalLength': { label: '초점 거리', icon: 'fa-solid fa-magnifying-glass-location' },
    'DateTimeOriginal': { label: '촬영일', icon: 'fa-regular fa-calendar-days' },
  };

  const geoCache = new Map();
  async function reverseGeocode(lat, lon) {
    const key = `${lat.toFixed(4)},${lon.toFixed(4)}`;
    if (geoCache.has(key)) return geoCache.get(key);
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&zoom=10&accept-language=ko`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Geocode failed');
      const data = await res.json();
      const addr = data.address || {};
      const place = addr.city || addr.town || addr.village || addr.county || addr.country || '알 수 없는 위치';
      geoCache.set(key, place);
      return place;
    } catch (e) {
      console.error("Geocoding Error:", e);
      geoCache.set(key, null);
      return null;
    }
  }

  async function fillPanel(d) {
    titleEl.textContent = d.title || d.id || '';
    metaEl.innerHTML = '';

    const createMetaItem = (item) => {
      const { icon, label, value, href } = item;
      if (!value) return '';
      const valueEl = href ? `<a href="${href}" target="_blank" rel="noopener noreferrer">${value}</a>` : value;
      return `
        <div class="glbx-meta-item">
          <i class="${icon}"></i>
          <span class="label">${label}</span>
          <span class="value">${valueEl}</span>
        </div>`;
    };

    let metaHtml = '';
    
    metaHtml += createMetaItem({ ...METADATA_MAP.DateTimeOriginal, value: d.exif.DateTimeOriginal });
    
    if (d.lat && d.lon) {
      const placeholder = `
        <div class="glbx-meta-item" id="geo-placeholder">
          <i class="fa-solid fa-location-dot"></i>
          <span class="label">위치</span>
          <span class="value">불러오는 중...</span>
        </div>`;
      metaEl.innerHTML += placeholder;
      const place = await reverseGeocode(d.lat, d.lon);
      const geoEl = document.getElementById('geo-placeholder');
      if (geoEl && place) {
        geoEl.querySelector('.value').innerHTML = `<a href="${d.map_url}" target="_blank" rel="noopener noreferrer">${place}</a>`;
      } else if (geoEl) {
        geoEl.remove();
      }
    }

    const mainExifKeys = ['FNumber', 'ExposureTime', 'ISOSpeedRatings', 'FocalLength', 'Model', 'LensModel'];
    mainExifKeys.forEach(key => {
        if (d.exif[key]) {
            metaHtml += createMetaItem({ ...METADATA_MAP[key], value: d.exif[key] });
        }
    });

    metaEl.innerHTML = metaHtml + metaEl.innerHTML;
  }

  function open() {
    root.hidden = false;
    document.documentElement.classList.add('glibx-open');
  }

  function close() {
    root.hidden = true;
    document.documentElement.classList.remove('glibx-open');
    if (history.state?.glbx) history.back();
  }

  function showAt(index) {
    if (index < 0 || index >= data.length) return;
    cur = index;
    const d = data[cur];
    
    img.src = d.url;
    img.alt = d.title || d.id || '';
    fillPanel(d);

    const target = `/gallery/photo/${encodeURIComponent(d.id)}`;
    if (location.pathname !== target) {
      history.pushState({ glbx: true, id: d.id }, '', target);
    }
  }
  
  function openById(id) {
    const index = data.findIndex(x => x.id === id);
    if (index === -1) return false;
    open();
    showAt(index);
    return true;
  }
  
  cards.forEach((a, i) => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      open();
      showAt(i);
    });
  });

  root.addEventListener('click', (e) => {
    const act = e.target?.closest('[data-action]')?.dataset.action;
    if (act === 'close') close();
  });

  window.addEventListener('keydown', (e) => {
    if (root.hidden) return;
    if (e.key === 'Escape') close();
  });

  window.addEventListener('popstate', () => {
    const m = location.pathname.match(/\/gallery\/photo\/(.+)$/);
    if (m) {
      const id = decodeURIComponent(m[1]);
      if (root.hidden) openById(id);
    } else {
      if (!root.hidden) close();
    }
  });

  (function initFromURL() {
    const m = location.pathname.match(/\/gallery\/photo\/(.+)$/);
    if (m) openById(decodeURIComponent(m[1]));
  })();
})();