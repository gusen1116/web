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
  const data = cards.map((a, idx) => {
    let exifObj = {};
    const rawExif = a.getAttribute('data-exif');
    
    try {
      if (rawExif) {
        const trimmed = rawExif.trim();
        if (trimmed.startsWith('{')) {
          exifObj = JSON.parse(trimmed);
        }
      }
    } catch(e) { 
      console.error(`[Gallery] EXIF 파싱 실패 (${a.dataset.id}):`, e);
      exifObj = {}; 
    }

    return {
      idx,
      id: a.dataset.id,
      url: a.dataset.url,
      title: a.dataset.title || '',
      exif: exifObj,
      lat: a.dataset.lat ? parseFloat(a.dataset.lat) : null,
      lon: a.dataset.lon ? parseFloat(a.dataset.lon) : null,
      address: a.dataset.address && a.dataset.address !== 'None' ? a.dataset.address : null
    };
  });

  let cur = -1;

  const METADATA_CONFIG = [
    { key: 'model', label: '카메라 모델', icon: 'fa-solid fa-camera' },
    { key: 'fnumber', label: '조리개', icon: 'fa-regular fa-circle' },
    { key: 'exposuretime', label: '셔터 스피드', icon: 'fa-solid fa-stopwatch' },
    { key: 'isospeedratings', label: 'ISO', icon: 'fa-solid fa-sliders' },
    { key: 'focallength', label: '초점 거리', icon: 'fa-solid fa-arrows-left-right' },
  ];

  async function fillPanel(d) {
    if (!d) return;
    
    titleEl.textContent = d.title || d.id || '';
    metaEl.innerHTML = ''; 

    const renderMeta = (addressVal) => {
      METADATA_CONFIG.forEach(cfg => {
        const val = d.exif[cfg.key];
        if (val) {
          const item = document.createElement('div');
          item.className = 'meta-item';
          item.innerHTML = `
            <i class="${cfg.icon}"></i>
            <div class="meta-content">
              <span class="meta-label">${cfg.label}</span>
              <span class="meta-value">${val}</span>
            </div>
          `;
          metaEl.appendChild(item);
        }
      });

      if (d.lat && d.lon) {
        const gpsItem = document.createElement('div');
        gpsItem.className = 'meta-item gps-item';
        gpsItem.innerHTML = `
          <i class="fa-solid fa-location-dot"></i>
          <div class="meta-content">
            <span class="meta-label">위치 정보</span>
            <span class="meta-value">${addressVal || `${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}`}</span>
            <a href="https://www.google.com/maps/search/?api=1&query=${d.lat},${d.lon}" 
               target="_blank" class="map-link">지도에서 보기</a>
          </div>
        `;
        metaEl.appendChild(gpsItem);
      }
    };

    renderMeta(d.address);
  }

  function open(idx) {
    if(idx < 0 || idx >= data.length) return;
    cur = idx;
    const d = data[cur];
    img.src = d.url;
    fillPanel(d);
    root.hidden = false;
    root.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    root.hidden = true;
    root.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    img.src = '';
  }

  cards.forEach((a, i) => {
    a.addEventListener('click', e => {
      e.preventDefault();
      open(i);
    });
  });

  root.addEventListener('click', e => {
    if (e.target.dataset.action === 'close') close();
  });

  window.addEventListener('keydown', e => {
    if (root.hidden) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') open(cur - 1);
    if (e.key === 'ArrowRight') open(cur + 1);
  });
})();
