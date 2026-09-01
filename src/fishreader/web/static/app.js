/**
 * fishreader Web Documentation Disguise SPA
 * Supports Vue 3 (VitePress), React (react.dev), Rust (mdBook), Python (Sphinx)
 */

(function () {
  'use strict';

  // --- SVG Icons for Brands ---
  const BRAND_LOGOS = {
    vue: `
      <svg width="28" height="28" viewBox="0 0 128 128" width="100%" height="100%">
        <path fill="#42b883" d="M78.8,10L64,35.4L49.2,10H0l64,110l64-110H78.8z"/>
        <path fill="#35495e" d="M78.8,10L64,35.4L49.2,10H25.6L64,76l38.4-66H78.8z"/>
      </svg>
    `,
    react: `
      <svg width="28" height="28" viewBox="-11.5 -10.23174 23 20.46348" fill="#149eca">
        <circle cx="0" cy="0" r="2.05" fill="#149eca"/>
        <g stroke="#149eca" stroke-width="1" fill="none">
          <ellipse rx="11" ry="4.2"/>
          <ellipse rx="11" ry="4.2" transform="rotate(60)"/>
          <ellipse rx="11" ry="4.2" transform="rotate(120)"/>
        </g>
      </svg>
    `,
    rust: `
      <svg width="26" height="26" viewBox="0 0 106 106" fill="currentColor">
        <path d="M53 5a48 48 0 1 0 48 48A48 48 0 0 0 53 5zm0 10a38 38 0 1 1-38 38 38 38 0 0 1 38-38z"/>
        <circle cx="53" cy="53" r="24" fill="none" stroke="currentColor" stroke-width="6"/>
      </svg>
    `,
    python: `
      <svg width="26" height="26" viewBox="0 0 110 110" fill="currentColor">
        <path fill="#306998" d="M51.7 5.8c-23.7 0-22.3 10.3-22.3 10.3l.1 10.7h22.7v3.2H20.6S5.8 28.3 5.8 52.1s13 23.3 13 23.3h7.7v-10.9s-.4-13 12.8-13h22.1s12.2.2 12.2-11.8V17.8s1.8-12-21.9-12zm-12.4 7c2.3 0 4.1 1.8 4.1 4.1s-1.8 4.1-4.1 4.1-4.1-1.8-4.1-4.1 1.8-4.1 4.1-4.1z"/>
        <path fill="#ffd43b" d="M58.3 104.2c23.7 0 22.3-10.3 22.3-10.3l-.1-10.7H57.8V80h31.6s14.8 1.7 14.8-22.1-13-23.3-13-23.3h-7.7v10.9s.4 13-12.8 13H48.6s-12.2-.2-12.2 11.8v21.9s-1.8 12 21.9 12zm12.4-7c-2.3 0-4.1-1.8-4.1-4.1s1.8-4.1 4.1-4.1 4.1 1.8 4.1 4.1-1.8 4.1-4.1 4.1z"/>
      </svg>
    `
  };

  const BRAND_NAMES = {
    vue: 'Vue.js',
    react: 'React',
    rust: 'The Rust Book',
    python: 'Python 3.13 Docs'
  };

  const DEFAULT_PAGE_TITLES = {
    vue: '响应式基础 | Vue.js',
    react: 'Quick Start – React',
    rust: 'What is Ownership? - The Rust Book',
    python: '3. Informal Introduction to Python'
  };

  // Disguised technical subpage names
  const DISGUISED_CHAPTER_NAMES = [
    '快速起步与环境初始化',
    '响应式状态与核心上下文',
    '生命周期调度与副作用分析',
    '依赖追踪与计算属性优化',
    '组件间通信与数据流转机制',
    '异步任务处理与并发模式',
    '深层状态代理与变更侦听',
    '底层渲染引擎与 DOM 协调',
    '插件系统与全局配置注入',
    '服务端水合与性能基准评估',
    '类型推导与静态契约约束',
    '错误边界与容灾回退策略'
  ];

  // --- App State ---
  const state = {
    theme: localStorage.getItem('fish_web_theme') || 'vue',
    mode: localStorage.getItem('fish_web_mode') || 'light',
    disguiseMode: localStorage.getItem('fish_web_disguise') || 'hybrid',
    isBossMode: false,
    books: [],
    currentBookId: null,
    currentBookDetail: null,
    currentChapterIndex: 0,
    useDisguisedNaming: true,
    progress: {},
    rawDocCache: {},
    // Video & Ad State
    adStyle: localStorage.getItem('fish_ad_style') || 'flashy_game',
    videoSize: localStorage.getItem('fish_video_size') || 'normal',
    videoDocked: localStorage.getItem('fish_video_docked') === 'true',
    serverVideos: []
  };

  // --- Flashy Junk Web Ad Themes (Decoy when Boss Key is pressed) ---
  const FLASHY_AD_THEMES = {
    flashy_game: {
      title: '🔥 屠龙宝刀 点击就送！',
      subtitle: '首充1元送VIP12，爆率9.9，神装秒回收秒到账！',
      btn: '立即开宝箱 >>',
      badge: 'HOT 爆款页游'
    },
    tech_course: {
      title: '⚡ 3天速成 Java / AI 架构师！',
      subtitle: '年薪百万大模型实战训练营，99元限时秒杀，先到先得！',
      btn: '抢占名额 >>',
      badge: '限时 99 元'
    },
    cloud_sale: {
      title: '🎁 云服务器 0 元免费抢！',
      subtitle: '企业级 8核32G 独立带宽，首年仅需 0 元，极速建站上线！',
      btn: '0元领取 >>',
      badge: '双十一特惠'
    },
    vue_sponsor: {
      title: 'Mall4j 企业级开源商城',
      subtitle: '100% 源码交付 · 二开简单 · SpringBoot 3.x / 微服务架构 Gitee 15k Star',
      btn: '查看在线演示 >>',
      badge: '企业赞助'
    }
  };

  // --- DOM Elements ---
  const elements = {
    body: document.body,
    pageTitle: document.getElementById('page-title'),
    brandIcon: document.getElementById('brand-icon'),
    brandText: document.getElementById('brand-text'),
    brandLogo: document.getElementById('brand-logo'),
    themeSelect: document.getElementById('doc-theme-select'),
    disguiseSelect: document.getElementById('disguise-mode-select'),
    bookSelect: document.getElementById('book-select'),
    darkModeToggle: document.getElementById('dark-mode-toggle'),
    bossBtn: document.getElementById('boss-key-btn'),
    bossBanner: document.getElementById('boss-banner'),
    sidebarLeft: document.getElementById('sidebar-left'),
    mobileMenuBtn: document.getElementById('mobile-menu-btn'),
    vueApiPreference: document.getElementById('vue-api-preference'),
    prefOptionsBtn: document.getElementById('pref-options'),
    prefCompositionBtn: document.getElementById('pref-composition'),
    toggleNamingBtn: document.getElementById('toggle-chapter-naming'),
    namingModeLabel: document.getElementById('naming-mode-label'),
    chapterCountBadge: document.getElementById('chapter-count-badge'),
    chapterList: document.getElementById('chapter-list'),
    crumbCurrent: document.getElementById('crumb-current'),
    articleTitle: document.getElementById('article-title'),
    docBlocks: document.getElementById('doc-blocks'),
    prevChapterBtn: document.getElementById('prev-chapter-btn'),
    nextChapterBtn: document.getElementById('next-chapter-btn'),
    prevChapterTitle: document.getElementById('prev-chapter-title'),
    nextChapterTitle: document.getElementById('next-chapter-title'),
    tocList: document.getElementById('toc-list'),
    searchTrigger: document.getElementById('search-trigger'),
    searchModal: document.getElementById('search-modal'),
    modalSearchInput: document.getElementById('modal-search-input'),
    searchResultsList: document.getElementById('search-results-list'),
    // Video Ad Elements
    floatingAdWidget: document.getElementById('floating-ad-widget'),
    adWidgetHeader: document.getElementById('ad-widget-header'),
    adTitleLabel: document.getElementById('ad-title-label'),
    adSourceBtn: document.getElementById('ad-source-btn'),
    adSizeBtn: document.getElementById('ad-size-btn'),
    adDockBtn: document.getElementById('ad-dock-btn'),
    adCloseBtn: document.getElementById('ad-close-btn'),
    adBodyContainer: document.getElementById('ad-body-container'),
    adVideo: document.getElementById('ad-video-element'),
    adPlaceholder: document.getElementById('ad-placeholder'),
    adSelectVideoBtn: document.getElementById('ad-select-video-btn'),
    adVideoControls: document.getElementById('ad-video-controls'),
    videoSeekBar: document.getElementById('video-seek-bar'),
    videoPlayBtn: document.getElementById('video-play-btn'),
    videoTimeDisplay: document.getElementById('video-time-display'),
    videoSpeedSelect: document.getElementById('video-speed-select'),
    videoMuteBtn: document.getElementById('video-mute-btn'),
    videoVolumeBar: document.getElementById('video-volume-bar'),
    bossAdOverlay: document.getElementById('boss-ad-overlay'),
    flashyAdTitle: document.getElementById('flashy-ad-title'),
    flashyAdSubtitle: document.getElementById('flashy-ad-subtitle'),
    adClosedToast: document.getElementById('ad-closed-toast'),
    adResizeHandle: document.getElementById('ad-resize-handle'),
    sidebarSponsorAnchor: document.getElementById('sidebar-sponsor-anchor'),
    sidebarAdMock: document.getElementById('sidebar-ad-mock'),
    // Video Source Modal
    videoSourceModal: document.getElementById('video-source-modal'),
    closeVideoModalBtn: document.getElementById('close-video-modal-btn'),
    fileDropZone: document.getElementById('file-drop-zone'),
    localVideoFileInput: document.getElementById('local-video-file-input'),
    pickLocalFileBtn: document.getElementById('pick-local-file-btn'),
    serverVideosList: document.getElementById('server-videos-list'),
    refreshServerVideosBtn: document.getElementById('refresh-server-videos-btn'),
    onlineVideoUrlInput: document.getElementById('online-video-url-input'),
    loadOnlineUrlBtn: document.getElementById('load-online-url-btn'),
    adStyleSelect: document.getElementById('ad-style-select'),
    videoSizeSelect: document.getElementById('video-size-select')
  };

  // --- Initialization ---
  async function init() {
    applyThemeAndMode();
    bindEvents();
    initVideoAd();
    await fetchInitialData();
  }

  // --- Theme & Mode Applicator ---
  function applyThemeAndMode() {
    elements.body.setAttribute('data-theme', state.theme);
    elements.body.setAttribute('data-mode', state.mode);
    elements.themeSelect.value = state.theme;
    if (elements.disguiseSelect) {
      elements.disguiseSelect.value = state.disguiseMode;
    }

    elements.brandIcon.innerHTML = BRAND_LOGOS[state.theme] || BRAND_LOGOS.vue;
    elements.brandText.textContent = BRAND_NAMES[state.theme] || 'Documentation';

    // Toggle Vue API preference widget visibility
    if (elements.vueApiPreference) {
      elements.vueApiPreference.style.display = state.theme === 'vue' ? 'block' : 'none';
    }

    localStorage.setItem('fish_web_theme', state.theme);
    localStorage.setItem('fish_web_mode', state.mode);
  }

  // --- API Fetchers ---
  async function fetchInitialData() {
    try {
      // 1. Fetch Status
      const statusRes = await fetch('/api/status');
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        if (statusData.theme && !localStorage.getItem('fish_web_theme')) {
          state.theme = statusData.theme;
          applyThemeAndMode();
        }
      }

      // 2. Fetch Books
      const booksRes = await fetch('/api/books');
      if (booksRes.ok) {
        state.books = await booksRes.json();
        renderBookSelect();
      }

      // 3. Fetch Progress
      const progRes = await fetch('/api/progress');
      if (progRes.ok) {
        state.progress = await progRes.json();
      }

      // Determine initial book
      const lastBookId = state.progress.last_book_id || (state.books.find(b => b.readable) || {}).id;
      if (lastBookId) {
        await selectBook(lastBookId);
      } else {
        elements.docBlocks.innerHTML = '<div class="loading-state">未发现小说书籍，请将 .txt / .epub 放入 books/ 目录</div>';
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
      elements.docBlocks.innerHTML = `<div class="loading-state">服务连接失败: ${err.message}</div>`;
    }
  }

  function renderBookSelect() {
    elements.bookSelect.innerHTML = '';
    state.books.forEach(book => {
      const opt = document.createElement('option');
      opt.value = book.id;
      opt.textContent = `${book.title} (${book.fmt.toUpperCase()})`;
      if (!book.readable) {
        opt.textContent += ' [不支持]';
        opt.disabled = true;
      }
      elements.bookSelect.appendChild(opt);
    });
  }

  async function selectBook(bookId) {
    state.currentBookId = bookId;
    elements.bookSelect.value = bookId;

    try {
      const res = await fetch(`/api/books/${encodeURIComponent(bookId)}`);
      if (!res.ok) throw new Error('Cannot load book details');
      const bookDetail = await res.json();
      state.currentBookDetail = bookDetail;

      // Determine chapter index from progress
      const bookProg = (state.progress.books || {})[bookId] || {};
      const targetChapter = bookProg.chapter_index || 0;

      renderSidebarChapters();
      await loadChapter(targetChapter);
    } catch (err) {
      console.error('Error selecting book:', err);
    }
  }

  function renderSidebarChapters() {
    if (!state.currentBookDetail) return;
    const chapters = state.currentBookDetail.chapters || [];
    elements.chapterCountBadge.textContent = `共 ${chapters.length} 节`;
    elements.chapterList.innerHTML = '';

    chapters.forEach((ch, idx) => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#chapter-${idx}`;
      a.className = 'nav-item-link';
      if (idx === state.currentChapterIndex) {
        a.classList.add('active');
      }

      // Display name
      let displayName = ch.title;
      if (state.useDisguisedNaming) {
        const fakeName = DISGUISED_CHAPTER_NAMES[idx % DISGUISED_CHAPTER_NAMES.length];
        displayName = `${idx + 1}. ${fakeName}`;
      }

      a.textContent = displayName;
      a.title = ch.title;
      a.addEventListener('click', (e) => {
        e.preventDefault();
        loadChapter(idx);
      });
      li.appendChild(a);
      elements.chapterList.appendChild(li);
    });
  }

  async function loadChapter(chapterIdx) {
    if (!state.currentBookId || !state.currentBookDetail) return;
    state.currentChapterIndex = chapterIdx;

    // Update active class in sidebar
    const items = elements.chapterList.querySelectorAll('.nav-item-link');
    items.forEach((item, idx) => {
      item.classList.toggle('active', idx === chapterIdx);
      if (idx === chapterIdx) {
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });

    if (state.isBossMode) {
      await renderBossMode();
      return;
    }

    elements.docBlocks.innerHTML = '<div class="loading-state">载入章节中...</div>';

    try {
      const url = `/api/books/${encodeURIComponent(state.currentBookId)}/chapters/${chapterIdx}?theme=${state.theme}&disguise=${state.disguiseMode}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Cannot load chapter content');
      const data = await res.json();
      renderDocPage(data);
      saveProgress(chapterIdx);
    } catch (err) {
      console.error('Error loading chapter:', err);
      elements.docBlocks.innerHTML = `<div class="loading-state">载入失败: ${err.message}</div>`;
    }
  }

  // --- Doc Page Renderer ---
  function renderDocPage(data) {
    const doc = data.doc;
    const chapters = state.currentBookDetail.chapters || [];

    // Title & Breadcrumbs
    let displayTitle = doc.title;
    if (state.useDisguisedNaming) {
      const fakeName = DISGUISED_CHAPTER_NAMES[data.chapter_index % DISGUISED_CHAPTER_NAMES.length];
      displayTitle = `${data.chapter_index + 1}. ${fakeName}`;
    }
    elements.articleTitle.textContent = displayTitle;
    elements.crumbCurrent.textContent = displayTitle;
    elements.pageTitle.textContent = `${displayTitle} | ${BRAND_NAMES[state.theme]}`;

    // Render Blocks
    elements.docBlocks.innerHTML = '';
    (doc.sections || []).forEach(sec => {
      const secEl = document.createElement('section');
      secEl.className = 'doc-section';
      secEl.id = sec.id;

      // Section Heading (H2 / H3)
      if (sec.level === 2) {
        const h2 = document.createElement('h2');
        h2.className = 'doc-h2';
        h2.textContent = sec.title;
        secEl.appendChild(h2);
      } else if (sec.level === 3) {
        const h3 = document.createElement('h3');
        h3.className = 'doc-h3';
        h3.textContent = sec.title;
        secEl.appendChild(h3);
      }

      // Blocks inside section
      (sec.blocks || []).forEach(block => {
        if (block.type === 'paragraph') {
          const p = document.createElement('p');
          p.className = 'doc-p';
          p.innerHTML = formatInlineCode(escapeHtml(block.content));
          secEl.appendChild(p);
        } else if (block.type === 'callout') {
          const callout = document.createElement('div');
          callout.className = `doc-callout ${block.flavor === 'warning' ? 'warning' : 'info'}`;
          const icon = block.flavor === 'warning' ? '⚠️' : '💡';
          callout.innerHTML = `
            <div class="callout-header">
              <span class="callout-icon">${icon}</span>
              <span class="callout-title">${escapeHtml(block.title || '提示')}</span>
            </div>
            <div class="callout-content">${formatInlineCode(escapeHtml(block.content))}</div>
          `;
          secEl.appendChild(callout);
        } else if (block.type === 'code') {
          const codeBox = document.createElement('div');
          codeBox.className = 'doc-code-block';
          codeBox.innerHTML = `
            <span class="code-lang-badge">${block.lang || 'js'}</span>
            <pre><code>${highlightFakeCode(escapeHtml(block.content), block.lang)}</code></pre>
          `;
          secEl.appendChild(codeBox);
        }
      });

      elements.docBlocks.appendChild(secEl);
    });

    // Render TOC
    renderToc(doc.toc || []);

    // Render Prev / Next footer navigation
    renderFooterNav(data.chapter_index, chapters);

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function renderToc(tocItems) {
    elements.tocList.innerHTML = '';
    tocItems.forEach(item => {
      const li = document.createElement('li');
      li.className = `toc-item level-${item.level || 2}`;
      const a = document.createElement('a');
      a.href = `#${item.id}`;
      a.className = 'toc-link';
      a.textContent = item.text;
      a.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.getElementById(item.id);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
      li.appendChild(a);
      elements.tocList.appendChild(li);
    });
    setupTocScrollSpy();
  }

  function setupTocScrollSpy() {
    const links = elements.tocList.querySelectorAll('.toc-link');
    const sections = elements.docBlocks.querySelectorAll('.doc-section');
    if (!sections.length || !links.length) return;

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          links.forEach(l => {
            l.classList.toggle('active', l.getAttribute('href') === `#${id}`);
          });
        }
      });
    }, { rootMargin: '-10% 0px -70% 0px' });

    sections.forEach(s => observer.observe(s));
  }

  function renderFooterNav(currentIdx, chapters) {
    if (currentIdx > 0) {
      elements.prevChapterBtn.classList.remove('hidden');
      const prevTitle = state.useDisguisedNaming
        ? `${currentIdx}. ${DISGUISED_CHAPTER_NAMES[(currentIdx - 1) % DISGUISED_CHAPTER_NAMES.length]}`
        : chapters[currentIdx - 1].title;
      elements.prevChapterTitle.textContent = prevTitle;
      elements.prevChapterBtn.onclick = (e) => {
        e.preventDefault();
        loadChapter(currentIdx - 1);
      };
    } else {
      elements.prevChapterBtn.classList.add('hidden');
    }

    if (currentIdx + 1 < chapters.length) {
      elements.nextChapterBtn.classList.remove('hidden');
      const nextTitle = state.useDisguisedNaming
        ? `${currentIdx + 2}. ${DISGUISED_CHAPTER_NAMES[(currentIdx + 1) % DISGUISED_CHAPTER_NAMES.length]}`
        : chapters[currentIdx + 1].title;
      elements.nextChapterTitle.textContent = nextTitle;
      elements.nextChapterBtn.onclick = (e) => {
        e.preventDefault();
        loadChapter(currentIdx + 1);
      };
    } else {
      elements.nextChapterBtn.classList.add('hidden');
    }
  }

  // --- Boss Mode (Panic Button) ---
  async function toggleBossMode() {
    state.isBossMode = !state.isBossMode;
    elements.bossBanner.classList.toggle('hidden', !state.isBossMode);

    if (state.isBossMode) {
      // 1. Pause video automatically
      if (elements.adVideo && !elements.adVideo.paused) {
        elements.adVideo.pause();
        updatePlayButton();
      }
      // 2. Show Boss Flashing Decoy Ad
      updateBossAdOverlay();
      if (elements.bossAdOverlay) {
        elements.bossAdOverlay.classList.remove('hidden');
      }

      await renderBossMode();
    } else {
      // Hide Boss Flashing Decoy Ad
      if (elements.bossAdOverlay) {
        elements.bossAdOverlay.classList.add('hidden');
      }

      await loadChapter(state.currentChapterIndex);
    }
  }

  async function renderBossMode() {
    try {
      const res = await fetch(`/api/real_docs/${state.theme}`);
      const data = await res.json();
      renderDocPage({
        chapter_index: 0,
        doc: data
      });
      elements.articleTitle.textContent = data.title;
      elements.crumbCurrent.textContent = data.title;
      elements.pageTitle.textContent = `${data.title} | ${BRAND_NAMES[state.theme]}`;
    } catch (err) {
      console.error('Error fetching real docs for boss mode:', err);
    }
  }

  // --- Video & Floating Ad Disguise Manager ---
  function initVideoAd() {
    if (!elements.floatingAdWidget) return;

    // Apply stored size & ad style
    setVideoSize(state.videoSize);
    setAdStyle(state.adStyle);
    if (state.videoDocked) {
      toggleVideoDock(true);
    }

    // Video Element Events
    elements.adVideo.addEventListener('play', updatePlayButton);
    elements.adVideo.addEventListener('pause', updatePlayButton);
    elements.adVideo.addEventListener('timeupdate', updateVideoProgress);
    elements.adVideo.addEventListener('loadedmetadata', onVideoLoadedMetadata);
    elements.adVideo.addEventListener('volumechange', updateVolumeDisplay);

    // Video Controls
    elements.videoPlayBtn.addEventListener('click', toggleVideoPlay);
    elements.adBodyContainer.addEventListener('click', (e) => {
      if (e.target === elements.adVideo || e.target === elements.adBodyContainer) {
        toggleVideoPlay();
      }
    });

    elements.videoSeekBar.addEventListener('input', () => {
      if (elements.adVideo.duration) {
        const time = (elements.videoSeekBar.value / 100) * elements.adVideo.duration;
        elements.adVideo.currentTime = time;
      }
    });

    elements.videoSpeedSelect.addEventListener('change', (e) => {
      elements.adVideo.playbackRate = parseFloat(e.target.value);
    });

    elements.videoMuteBtn.addEventListener('click', () => {
      elements.adVideo.muted = !elements.adVideo.muted;
      updateVolumeDisplay();
    });

    elements.videoVolumeBar.addEventListener('input', (e) => {
      elements.adVideo.volume = parseFloat(e.target.value);
      elements.adVideo.muted = false;
      updateVolumeDisplay();
    });

    // Widget Header Buttons
    elements.adSourceBtn.addEventListener('click', openVideoSourceModal);
    elements.adSelectVideoBtn.addEventListener('click', openVideoSourceModal);
    elements.adSizeBtn.addEventListener('click', cycleVideoSize);
    elements.adDockBtn.addEventListener('click', () => toggleVideoDock(!state.videoDocked));
    elements.adCloseBtn.addEventListener('click', closeAdToast);

    // Modal Events
    elements.closeVideoModalBtn.addEventListener('click', closeVideoSourceModal);
    elements.videoSourceModal.addEventListener('click', (e) => {
      if (e.target === elements.videoSourceModal) closeVideoSourceModal();
    });

    // Modal Tabs
    const tabBtns = elements.videoSourceModal.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        elements.videoSourceModal.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const target = elements.videoSourceModal.querySelector(`#${btn.dataset.tab}`);
        if (target) target.classList.add('active');
        if (btn.dataset.tab === 'tab-server-videos') {
          fetchServerVideos();
        }
      });
    });

    // Local File Picker
    elements.pickLocalFileBtn.addEventListener('click', () => elements.localVideoFileInput.click());
    elements.localVideoFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        loadVideoFile(e.target.files[0]);
        closeVideoSourceModal();
      }
    });

    // Drag and Drop
    elements.fileDropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      elements.fileDropZone.classList.add('dragover');
    });
    elements.fileDropZone.addEventListener('dragleave', () => {
      elements.fileDropZone.classList.remove('dragover');
    });
    elements.fileDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      elements.fileDropZone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        loadVideoFile(e.dataTransfer.files[0]);
        closeVideoSourceModal();
      }
    });

    // Refresh Server Videos
    elements.refreshServerVideosBtn.addEventListener('click', fetchServerVideos);

    // Online URL
    elements.loadOnlineUrlBtn.addEventListener('click', () => {
      const url = elements.onlineVideoUrlInput.value.trim();
      if (url) {
        loadVideoUrl(url, '网络视频');
        closeVideoSourceModal();
      }
    });

    // Ad Style & Size Settings
    elements.adStyleSelect.value = state.adStyle;
    elements.adStyleSelect.addEventListener('change', (e) => {
      setAdStyle(e.target.value);
    });

    elements.videoSizeSelect.value = state.videoSize;
    elements.videoSizeSelect.addEventListener('change', (e) => {
      setVideoSize(e.target.value);
    });

    // Drag to Reposition
    setupVideoWidgetDrag();
    setupVideoWidgetResize();
  }

  function updatePlayButton() {
    if (!elements.videoPlayBtn) return;
    elements.videoPlayBtn.textContent = elements.adVideo.paused ? '▶' : '⏸';
  }

  function toggleVideoPlay() {
    if (!elements.adVideo.src && !elements.adVideo.currentSrc) {
      openVideoSourceModal();
      return;
    }
    if (elements.adVideo.paused) {
      elements.adVideo.play().catch(() => {});
    } else {
      elements.adVideo.pause();
    }
    updatePlayButton();
  }

  function updateVideoProgress() {
    if (!elements.adVideo.duration) return;
    const pct = (elements.adVideo.currentTime / elements.adVideo.duration) * 100;
    elements.videoSeekBar.value = pct;
    elements.videoTimeDisplay.textContent = `${formatTime(elements.adVideo.currentTime)} / ${formatTime(elements.adVideo.duration)}`;
  }

  function onVideoLoadedMetadata() {
    elements.adPlaceholder.classList.add('hidden');
    elements.adVideoControls.classList.remove('hidden');
    updateVideoProgress();
    elements.adVideo.play().catch(() => {});
    updatePlayButton();
  }

  function updateVolumeDisplay() {
    if (elements.adVideo.muted || elements.adVideo.volume === 0) {
      elements.videoMuteBtn.textContent = '🔇';
    } else if (elements.adVideo.volume < 0.5) {
      elements.videoMuteBtn.textContent = '🔉';
    } else {
      elements.videoMuteBtn.textContent = '🔊';
    }
    elements.videoVolumeBar.value = elements.adVideo.muted ? 0 : elements.adVideo.volume;
  }

  function formatTime(secs) {
    if (isNaN(secs)) return '00:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }

  function loadVideoFile(file) {
    const url = URL.createObjectURL(file);
    elements.adVideo.src = url;
    elements.adTitleLabel.textContent = file.name.slice(0, 16);
    elements.adPlaceholder.classList.add('hidden');
  }

  function loadVideoUrl(url, name) {
    elements.adVideo.src = url;
    elements.adTitleLabel.textContent = name || '赞助视频';
    elements.adPlaceholder.classList.add('hidden');
  }

  async function fetchServerVideos() {
    elements.serverVideosList.innerHTML = '<div class="empty-hint">正在读取 videos/ 目录...</div>';
    try {
      const res = await fetch('/api/videos');
      if (!res.ok) throw new Error('API error');
      state.serverVideos = await res.json();
      renderServerVideosList();
    } catch (err) {
      elements.serverVideosList.innerHTML = `<div class="empty-hint">读取失败: ${err.message}</div>`;
    }
  }

  function renderServerVideosList() {
    elements.serverVideosList.innerHTML = '';
    if (!state.serverVideos.length) {
      elements.serverVideosList.innerHTML = '<div class="empty-hint">videos/ 目录暂无视频文件，请将 .mp4 / .webm 放入该目录</div>';
      return;
    }
    state.serverVideos.forEach(v => {
      const item = document.createElement('div');
      item.className = 'server-video-item';
      const sizeMb = (v.size_bytes / (1024 * 1024)).toFixed(1);
      item.innerHTML = `
        <span class="video-name">🎬 ${escapeHtml(v.name)}</span>
        <span class="video-size">${sizeMb} MB</span>
      `;
      item.onclick = () => {
        loadVideoUrl(v.url, v.name);
        closeVideoSourceModal();
      };
      elements.serverVideosList.appendChild(item);
    });
  }

  function setVideoSize(size) {
    state.videoSize = size;
    localStorage.setItem('fish_video_size', size);
    ['size-small', 'size-normal', 'size-large', 'size-xl'].forEach(c => elements.floatingAdWidget.classList.remove(c));
    elements.floatingAdWidget.classList.add(`size-${size}`);
    elements.floatingAdWidget.style.width = '';
    elements.floatingAdWidget.style.height = '';
  }

  function cycleVideoSize() {
    const sizes = ['small', 'normal', 'large', 'xl'];
    const idx = sizes.indexOf(state.videoSize);
    const next = sizes[(idx + 1) % sizes.length];
    setVideoSize(next);
  }

  function toggleVideoDock(docked) {
    state.videoDocked = docked;
    localStorage.setItem('fish_video_docked', String(docked));
    if (docked) {
      elements.floatingAdWidget.classList.remove('pos-bottom-right');
      elements.floatingAdWidget.classList.add('pos-sidebar');
      elements.sidebarSponsorAnchor.appendChild(elements.floatingAdWidget);
      elements.sidebarAdMock.classList.add('hidden');
    } else {
      elements.floatingAdWidget.classList.remove('pos-sidebar');
      elements.floatingAdWidget.classList.add('pos-bottom-right');
      document.body.appendChild(elements.floatingAdWidget);
      elements.sidebarAdMock.classList.remove('hidden');
    }
  }

  function setAdStyle(style) {
    state.adStyle = style;
    localStorage.setItem('fish_ad_style', style);
    elements.floatingAdWidget.setAttribute('data-ad-style', style);
    updateBossAdOverlay();
  }

  function updateBossAdOverlay() {
    const theme = FLASHY_AD_THEMES[state.adStyle] || FLASHY_AD_THEMES.flashy_game;
    elements.flashyAdTitle.textContent = theme.title;
    elements.flashyAdSubtitle.textContent = theme.subtitle;
    const badge = elements.bossAdOverlay.querySelector('.flashy-badge.hot');
    if (badge) badge.textContent = theme.badge;
    const btn = elements.bossAdOverlay.querySelector('.flashy-btn');
    if (btn) btn.textContent = theme.btn;
  }

  function closeAdToast() {
    elements.adClosedToast.classList.remove('hidden');
    setTimeout(() => {
      elements.adClosedToast.classList.add('hidden');
    }, 3000);
  }

  function openVideoSourceModal() {
    elements.videoSourceModal.classList.remove('hidden');
  }

  function closeVideoSourceModal() {
    elements.videoSourceModal.classList.add('hidden');
  }

  function setupVideoWidgetDrag() {
    let isDragging = false;
    let startX, startY, initialLeft, initialTop;

    elements.adWidgetHeader.addEventListener('mousedown', (e) => {
      if (state.videoDocked) return;
      if (['BUTTON', 'SELECT', 'INPUT'].includes(e.target.tagName)) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = elements.floatingAdWidget.getBoundingClientRect();
      initialLeft = rect.left;
      initialTop = rect.top;

      // Unset bottom/right to allow absolute positioning
      elements.floatingAdWidget.style.right = 'auto';
      elements.floatingAdWidget.style.bottom = 'auto';
      elements.floatingAdWidget.style.left = `${initialLeft}px`;
      elements.floatingAdWidget.style.top = `${initialTop}px`;
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      elements.floatingAdWidget.style.left = `${Math.max(10, initialLeft + dx)}px`;
      elements.floatingAdWidget.style.top = `${Math.max(10, initialTop + dy)}px`;
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }

  function setupVideoWidgetResize() {
    let isResizing = false;
    let startX, startW;

    elements.adResizeHandle.addEventListener('mousedown', (e) => {
      if (state.videoDocked) return;
      isResizing = true;
      startX = e.clientX;
      startW = elements.floatingAdWidget.offsetWidth;
      e.preventDefault();
      e.stopPropagation();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const dx = startX - e.clientX;
      const newW = Math.max(180, Math.min(800, startW + dx));
      elements.floatingAdWidget.style.width = `${newW}px`;
    });

    window.addEventListener('mouseup', () => {
      isResizing = false;
    });
  }

  // --- Progress Saving ---
  let saveTimeout = null;
  function saveProgress(chapterIdx) {
    if (!state.currentBookId) return;
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(async () => {
      try {
        await fetch('/api/progress', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            book_id: state.currentBookId,
            chapter_index: chapterIdx,
            char_offset: 0,
            scroll_line: 0
          })
        });
      } catch (err) {
        console.warn('Progress autosave failed:', err);
      }
    }, 1000);
  }

  // --- Formatting Helpers ---
  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatInlineCode(str) {
    // Wrap words matching common code patterns like foo(), <script>, .value in <code>
    return str.replace(/(`[^`]+`|\b[a-zA-Z_$][a-zA-Z0-9_$]*\(\)|&lt;[a-zA-Z0-9_-]+&gt;|\.[a-zA-Z_$][a-zA-Z0-9_$]*\b)/g, (m) => {
      const clean = m.startsWith('`') && m.endsWith('`') ? m.slice(1, -1) : m;
      return `<code class="inline-code">${clean}</code>`;
    });
  }

  function highlightFakeCode(code, lang) {
    // Simple regex-based syntax highlighter for clean realistic looks
    return code
      .replace(/(\/\/.*$|#.*$)/gm, '<span style="color:#6a9955;font-style:italic">$1</span>')
      .replace(/\b(import|export|from|const|let|var|function|return|if|else|async|await|fn|pub|use|def|class|struct|impl)\b/g, '<span style="color:#c678dd;font-weight:600">$1</span>')
      .replace(/\b(ref|computed|reactive|useState|useEffect|useMemo|Arc|Mutex|Result|Option)\b/g, '<span style="color:#61afef">$1</span>')
      .replace(/('([^'\\]|\\.)*'|"([^"\\]|\\.)*")/g, '<span style="color:#98c379">$1</span>');
  }

  // --- Search Modal (⌘K) ---
  function openSearchModal() {
    elements.searchModal.classList.remove('hidden');
    elements.modalSearchInput.value = '';
    elements.modalSearchInput.focus();
    renderSearchResults('');
  }

  function closeSearchModal() {
    elements.searchModal.classList.add('hidden');
  }

  function renderSearchResults(query) {
    if (!state.currentBookDetail) return;
    const chapters = state.currentBookDetail.chapters || [];
    const q = query.trim().toLowerCase();
    elements.searchResultsList.innerHTML = '';

    const matches = chapters.filter((c, idx) => {
      if (!q) return true;
      const fakeName = DISGUISED_CHAPTER_NAMES[idx % DISGUISED_CHAPTER_NAMES.length];
      return c.title.toLowerCase().includes(q) || fakeName.toLowerCase().includes(q);
    });

    matches.slice(0, 15).forEach(c => {
      const div = document.createElement('div');
      div.className = 'search-item';
      const fakeName = DISGUISED_CHAPTER_NAMES[c.index % DISGUISED_CHAPTER_NAMES.length];
      div.innerHTML = `
        <span class="search-item-title">${escapeHtml(state.useDisguisedNaming ? `${c.index + 1}. ${fakeName}` : c.title)}</span>
        <span class="search-item-sub">第 ${c.index + 1} 节</span>
      `;
      div.onclick = () => {
        closeSearchModal();
        loadChapter(c.index);
      };
      elements.searchResultsList.appendChild(div);
    });
  }

  // --- Event Bindings ---
  function bindEvents() {
    // Theme Select
    elements.themeSelect.addEventListener('change', (e) => {
      state.theme = e.target.value;
      applyThemeAndMode();
      if (state.isBossMode) {
        renderBossMode();
      } else {
        loadChapter(state.currentChapterIndex);
      }
    });

    // Disguise Style Select
    if (elements.disguiseSelect) {
      elements.disguiseSelect.addEventListener('change', (e) => {
        state.disguiseMode = e.target.value;
        localStorage.setItem('fish_web_disguise', state.disguiseMode);
        loadChapter(state.currentChapterIndex);
      });
    }

    // Book Select
    elements.bookSelect.addEventListener('change', (e) => {
      selectBook(e.target.value);
    });

    // Dark / Light Toggle
    elements.darkModeToggle.addEventListener('click', () => {
      state.mode = state.mode === 'light' ? 'dark' : 'light';
      applyThemeAndMode();
    });

    // Boss Key Buttons
    elements.bossBtn.addEventListener('click', toggleBossMode);
    elements.brandLogo.addEventListener('dblclick', toggleBossMode);

    // Toggle Chapter Naming Mode
    elements.toggleNamingBtn.addEventListener('click', () => {
      state.useDisguisedNaming = !state.useDisguisedNaming;
      elements.namingModeLabel.textContent = `伪装命名: ${state.useDisguisedNaming ? '开' : '关'}`;
      renderSidebarChapters();
      loadChapter(state.currentChapterIndex);
    });

    // Vue API Preference toggle buttons
    elements.prefOptionsBtn.addEventListener('click', () => {
      elements.prefOptionsBtn.classList.add('active');
      elements.prefCompositionBtn.classList.remove('active');
    });
    elements.prefCompositionBtn.addEventListener('click', () => {
      elements.prefCompositionBtn.classList.add('active');
      elements.prefOptionsBtn.classList.remove('active');
    });

    // Mobile Menu Toggle
    elements.mobileMenuBtn.addEventListener('click', () => {
      elements.sidebarLeft.classList.toggle('mobile-open');
    });

    // Search Trigger (⌘K)
    elements.searchTrigger.addEventListener('click', openSearchModal);
    elements.modalSearchInput.addEventListener('input', (e) => {
      renderSearchResults(e.target.value);
    });
    elements.searchModal.addEventListener('click', (e) => {
      if (e.target === elements.searchModal) closeSearchModal();
    });

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      // Escape or 'b' for Boss Key (when not in search modal)
      if (e.key === 'Escape') {
        if (!elements.searchModal.classList.contains('hidden')) {
          closeSearchModal();
        } else {
          toggleBossMode();
        }
      } else if (e.key === 'b' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        toggleBossMode();
      } else if (e.key === 'v' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        e.preventDefault();
        toggleVideoPlay();
      } else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (elements.searchModal.classList.contains('hidden')) {
          openSearchModal();
        } else {
          closeSearchModal();
        }
      } else if (['[', 'p'].includes(e.key) && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        // Prev chapter
        if (state.currentChapterIndex > 0) {
          e.preventDefault();
          loadChapter(state.currentChapterIndex - 1);
        }
      } else if ([']', 'n'].includes(e.key) && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        // Next chapter
        const total = (state.currentBookDetail && state.currentBookDetail.chapters) ? state.currentBookDetail.chapters.length : 0;
        if (state.currentChapterIndex + 1 < total) {
          e.preventDefault();
          loadChapter(state.currentChapterIndex + 1);
        }
      }
    });
  }

  // Launch app when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
