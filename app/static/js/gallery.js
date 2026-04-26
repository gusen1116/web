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
        // 속성값이 이미 이중 인코딩된 경우 등을 고려하여 트림 처리
        const trimmed = rawExif.trim();
        if (trimmed.startsWith('{')) {
          exifObj = JSON.parse(trimmed);
        }
      }
    } catch(e) { 
      console.error(`[Gallery] EXIF 파싱 실패 (${a.dataset.id}):`, e);
      console.log(`[Gallery] 원본 데이터:`, rawExif);
      // 실패 시 빈 객체 유지
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
    { key: 'model', label: 'Camera Model', icon: 'fa-solid fa-camera' },
    { key: 'fnumber', label: 'Aperture', icon: 'fa-regular fa-circle' },
    { key: 'exposuretime', label: 'Shutter Speed', icon: 'fa-solid fa-stopwatch' },
    { key: 'isospeedratings', label: 'ISO', icon: 'fa-solid fa-sliders' },
    { key: 'focallength', label: 'Focal Length', icon: 'fa-solid fa-arrows-left-right' },
  ];

  async function fillPanel(d) {
    if (!d) return;
    
    titleEl.textContent = d.title || d.id || '';
    metaEl.innerHTML = ''; 

    const renderMeta = (addressVal) => {
      let metaHtml = '';
      METADATA_CONFIG.forEach(cfg => {
        const value = d.exif[cfg.key];
        if (value && value !== 'None' && value !== 'undefined' && value !== 'null') {
          metaHtml += `
            <div class="glbx-meta-item">
              <span class="label"><i class="${cfg.icon}"></i> ${cfg.label}</span>
              <span class="value">${value}</span>
            </div>`;
        }
      });

      if (d.lat && d.lon) {
        const addrDisplay = (addressVal && addressVal !== 'None') ? addressVal : `${d.lat.toFixed(4)}, ${d.lon.toFixed(4)}`;
        metaHtml += `
          <div class="glbx-meta-item">
            <span class="label"><i class="fa-solid fa-location-dot"></i> GPS</span>
            <span class="value">${addrDisplay}</span>
          </div>`;
      }
      
      if (!metaHtml) {
        metaHtml = '<div class="glbx-meta-item"><span class="value">정보가 없습니다.</span></div>';
      }
      metaEl.innerHTML = metaHtml;
    };

    renderMeta(d.address);

    if (d.lat && d.lon && (!d.address || d.address === 'None')) {
      try {
        const res = await fetch(`/gallery/api/photo/${encodeURIComponent(d.id)}/address`);
        if (res.ok) {
          const json = await res.json();
          if (json.address && json.address !== 'None') {
            d.address = json.address;
            renderMeta(d.address);
          }
        }
      } catch (e) { console.warn("[Gallery] 주소 업데이트 실패:", e); }
    }
  }

  function open() {
    root.hidden = false;
    root.classList.add('is-active');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    root.hidden = true;
    root.classList.remove('is-active');
    document.body.style.overflow = '';
    if (history.state?.glbx) history.back();
  }

  function showAt(index) {
    if (index < 0 || index >= data.length) return;
    cur = index;
    const d = data[cur];
    
    img.style.opacity = '0';
    
    const tempImg = new Image();
    tempImg.onload = () => {
      img.src = d.url;
      img.style.opacity = '1';
    };
    tempImg.onerror = () => {
      img.src = d.url;
      img.style.opacity = '1';
    };
    tempImg.src = d.url;
    
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
    else if (e.target.classList.contains('glbx-overlay')) close();
  });

  window.addEventListener('keydown', (e) => {
    if (root.hidden) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') showAt(cur - 1);
    if (e.key === 'ArrowRight') showAt(cur + 1);
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
    if (m) {
      const id = decodeURIComponent(m[1]);
      openById(id);
    }
  })();
})();
