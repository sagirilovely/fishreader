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
    rawDocCache: {}
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
    searchResultsList: document.getElementById('search-results-list')
  };

  // --- Initialization ---
  async function init() {
    applyThemeAndMode();
    bindEvents();
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
      await renderBossMode();
    } else {
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
