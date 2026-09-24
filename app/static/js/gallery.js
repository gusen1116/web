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

// 사진 비율에 맞춰 배치하되 DOM 순서는 좌→우로 유지한다.
const galleryMasonry = (() => {
  const grid = document.getElementById('masonry');
  if (!grid || !grid.querySelector('.photo-card') || typeof window.Masonry !== 'function') {
    return null;
  }

  let masonry;

  try {
    grid.classList.add('is-masonry');
    masonry = new window.Masonry(grid, {
      itemSelector: '.photo-card:not([hidden])',
      columnWidth: '.masonry-sizer',
      gutter: '.masonry-gutter',
      percentPosition: true,
      horizontalOrder: true,
      transitionDuration: '240ms'
    });
  } catch (error) {
    grid.classList.remove('is-masonry');
    return null;
  }

  const refresh = () => {
    masonry.reloadItems();
    masonry.layout();
  };

  if (typeof window.imagesLoaded === 'function') {
    const imageLoad = window.imagesLoaded(grid);
    imageLoad.on('progress', refresh);
    imageLoad.on('always', refresh);
  } else {
    window.addEventListener('load', refresh, { once: true });
  }

  return { refresh };
})();

// 연도 필터
(function(){
  const sel = document.getElementById('yearFilter');
  if(!sel) return;
  const cards = Array.from(document.querySelectorAll('.photo-card'));
  if(!cards.length) return;

  sel.addEventListener('change', () => {
    const selectedYear = sel.value;
    
    cards.forEach(card => {
      const cardYear = card.dataset.year;
      card.hidden = selectedYear !== 'all' && cardYear !== selectedYear;
    });

    if (galleryMasonry) {
      window.requestAnimationFrame(galleryMasonry.refresh);
    }
  });
})();

/* ================= 공통 사진 뷰어 컨트롤 ================= */
(function initPhotoViewerControls(){
  const viewers = Array.from(document.querySelectorAll('[data-photo-viewer]'));
  if (!viewers.length) return;

  const setInfoState = (viewer, isOpen) => {
    viewer.classList.toggle('is-info-open', isOpen);
    const toggle = viewer.querySelector('.photo-viewer__info-toggle');
    if (toggle) toggle.setAttribute('aria-expanded', String(isOpen));
  };

  const updateFullscreenControls = () => {
    viewers.forEach(viewer => {
      const button = viewer.querySelector('[data-action="fullscreen"]');
      if (!button) return;

      const isFullscreen = document.fullscreenElement === viewer;
      const icon = button.querySelector('i');
      const label = button.querySelector('.photo-viewer__tool-label');
      button.setAttribute('aria-label', isFullscreen ? '전체 화면 종료' : '전체 화면으로 보기');
      if (icon) icon.className = isFullscreen ? 'fa-solid fa-compress' : 'fa-solid fa-expand';
      if (label) label.textContent = isFullscreen ? '전체 화면 종료' : '전체 화면';
    });
  };

  viewers.forEach(viewer => {
    viewer.querySelectorAll('[data-action="toggle-info"]').forEach(button => {
      button.addEventListener('click', () => {
        setInfoState(viewer, !viewer.classList.contains('is-info-open'));
      });
    });

    const fullscreenButton = viewer.querySelector('[data-action="fullscreen"]');
    if (fullscreenButton) {
      fullscreenButton.addEventListener('click', async () => {
        try {
          if (document.fullscreenElement) {
            await document.exitFullscreen();
          } else if (viewer.requestFullscreen) {
            await viewer.requestFullscreen();
          }
        } catch (error) {
          // 전체 화면 API를 지원하지 않거나 권한이 없는 경우 기본 화면을 유지한다.
        }
      });
    }
  });

  document.addEventListener('fullscreenchange', updateFullscreenControls);

  const pageViewer = document.querySelector('.photo-viewer--page');
  if (!pageViewer) return;

  const previousLink = pageViewer.querySelector('[data-direction="previous"]');
  const nextLink = pageViewer.querySelector('[data-direction="next"]');
  const stage = pageViewer.querySelector('.photo-viewer__stage');

  window.addEventListener('keydown', event => {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
    if (event.key === 'Escape' && pageViewer.classList.contains('is-info-open')) {
      setInfoState(pageViewer, false);
      return;
    }
    if (event.key === 'ArrowLeft' && previousLink) previousLink.click();
    if (event.key === 'ArrowRight' && nextLink) nextLink.click();
  });

  if (stage) {
    let touchStartX = 0;
    let touchStartY = 0;

    stage.addEventListener('touchstart', event => {
      const touch = event.changedTouches[0];
      touchStartX = touch.clientX;
      touchStartY = touch.clientY;
    }, { passive: true });

    stage.addEventListener('touchend', event => {
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;
      if (Math.abs(deltaX) < 55 || Math.abs(deltaX) <= Math.abs(deltaY)) return;
      if (deltaX > 0 && previousLink) previousLink.click();
      if (deltaX < 0 && nextLink) nextLink.click();
    }, { passive: true });
  }
})();

/* ================= 갤러리 몰입형 뷰어 ================= */
(function initGalleryViewer(){
  const root = document.getElementById('glightbox');
  if (!root) return;

  const img = root.querySelector('#glbx-img');
  const titleEl = root.querySelector('#glbx-title');
  const metaEl = root.querySelector('#glbx-meta');
  const counterEl = root.querySelector('#glbx-counter');
  const previousButton = root.querySelector('[data-action="previous"]');
  const nextButton = root.querySelector('[data-action="next"]');
  const stage = root.querySelector('.photo-viewer__stage');
  const cards = Array.from(document.querySelectorAll('.photo-card'));

  const photos = cards.map(card => {
    let exif = {};
    try {
      exif = JSON.parse(card.dataset.exif || '{}');
    } catch (error) {
      exif = {};
    }

    return {
      element: card,
      id: card.dataset.id,
      href: card.href,
      url: card.dataset.url,
      title: card.dataset.title || card.dataset.id || '',
      year: card.dataset.year || '',
      exif
    };
  });

  let currentPhoto = null;
  let lastTrigger = null;
  let previousBodyOverflow = '';

  const visiblePhotos = () => photos.filter(photo => !photo.element.hidden);

  const appendMeta = (label, value, wide = false) => {
    if (!value) return;

    const item = document.createElement('div');
    item.className = `photo-viewer__meta-item${wide ? ' photo-viewer__meta-item--wide' : ''}`;

    const term = document.createElement('dt');
    term.textContent = label;
    const description = document.createElement('dd');
    description.textContent = value;

    item.append(term, description);
    metaEl.appendChild(item);
  };

  const renderPhoto = photo => {
    currentPhoto = photo;
    img.src = photo.url;
    img.alt = photo.title;
    titleEl.textContent = photo.title;
    metaEl.replaceChildren();

    appendMeta('카메라', photo.exif.model, true);
    appendMeta('촬영 연도', photo.year);
    appendMeta('조리개', photo.exif.fnumber);
    appendMeta('셔터', photo.exif.exposuretime);
    appendMeta('ISO', photo.exif.isospeedratings);
    appendMeta('초점 거리', photo.exif.focallength);

    if (!metaEl.children.length) {
      const empty = document.createElement('p');
      empty.className = 'photo-viewer__empty-meta';
      empty.textContent = '표시할 촬영 정보가 없습니다.';
      metaEl.appendChild(empty);
    }

    const visible = visiblePhotos();
    const position = visible.indexOf(photo);
    counterEl.textContent = `${position + 1} / ${visible.length}`;
    counterEl.setAttribute('aria-label', `전체 ${visible.length}장 중 ${position + 1}번째 사진`);
    previousButton.disabled = position <= 0;
    nextButton.disabled = position < 0 || position >= visible.length - 1;
  };

  const openPhoto = (photo, historyMode = 'push') => {
    if (!photo) return;
    renderPhoto(photo);

    if (root.hidden) {
      previousBodyOverflow = document.body.style.overflow;
      root.hidden = false;
      root.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      root.querySelector('[data-action="close"]')?.focus({ preventScroll: true });
    }

    const state = { galleryViewer: true, photoId: photo.id };
    if (historyMode === 'push') history.pushState(state, '', photo.href);
    if (historyMode === 'replace') history.replaceState(state, '', photo.href);
  };

  const closeImmediately = () => {
    if (root.hidden) return;
    root.hidden = true;
    root.setAttribute('aria-hidden', 'true');
    root.classList.remove('is-info-open');
    root.querySelector('.photo-viewer__info-toggle')?.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = previousBodyOverflow;
    img.removeAttribute('src');
    currentPhoto = null;
    lastTrigger?.focus({ preventScroll: true });
  };

  const requestClose = () => {
    if (history.state?.galleryViewer) {
      history.back();
    } else {
      closeImmediately();
    }
  };

  const move = offset => {
    const visible = visiblePhotos();
    const position = visible.indexOf(currentPhoto);
    const nextPhoto = visible[position + offset];
    if (nextPhoto) openPhoto(nextPhoto, 'replace');
  };

  cards.forEach((card, index) => {
    card.addEventListener('click', event => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      lastTrigger = card;
      openPhoto(photos[index], 'push');
    });
  });

  root.addEventListener('click', event => {
    const actionButton = event.target.closest('[data-action]');
    if (!actionButton) return;
    if (actionButton.dataset.action === 'close') requestClose();
    if (actionButton.dataset.action === 'previous') move(-1);
    if (actionButton.dataset.action === 'next') move(1);
  });

  window.addEventListener('keydown', event => {
    if (root.hidden) return;
    if (event.key === 'Escape' && root.classList.contains('is-info-open')) {
      root.classList.remove('is-info-open');
      root.querySelector('.photo-viewer__info-toggle')?.setAttribute('aria-expanded', 'false');
      return;
    }
    if (event.key === 'Escape' && !document.fullscreenElement) requestClose();
    if (event.key === 'ArrowLeft') move(-1);
    if (event.key === 'ArrowRight') move(1);
  });

  window.addEventListener('popstate', event => {
    if (event.state?.galleryViewer) {
      const photo = photos.find(item => item.id === event.state.photoId);
      openPhoto(photo, 'none');
    } else {
      closeImmediately();
    }
  });

  if (stage) {
    let touchStartX = 0;
    let touchStartY = 0;

    stage.addEventListener('touchstart', event => {
      const touch = event.changedTouches[0];
      touchStartX = touch.clientX;
      touchStartY = touch.clientY;
    }, { passive: true });

    stage.addEventListener('touchend', event => {
      const touch = event.changedTouches[0];
      const deltaX = touch.clientX - touchStartX;
      const deltaY = touch.clientY - touchStartY;
      if (Math.abs(deltaX) < 55 || Math.abs(deltaX) <= Math.abs(deltaY)) return;
      move(deltaX > 0 ? -1 : 1);
    }, { passive: true });
  }
})();
