/* ============================================================
   ShopKart — main.js
   Global UX enhancements
   ============================================================ */

(function () {
    'use strict';

    /* ══════════════════════════════════════════════════════════
       1. AUTO-HIDE ALERTS AFTER 3 SECONDS
       ══════════════════════════════════════════════════════════ */
    function initAutoHideAlerts() {
        function dismissAlert(alert) {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity    = '0';
            alert.style.transform  = 'translateY(-6px)';
            setTimeout(() => alert.remove(), 420);
        }

        function scheduleAlerts() {
            document.querySelectorAll('.alert.alert-dismissible, .alert[role="alert"]')
                .forEach(alert => {
                    if (alert.dataset.autoDismiss) return;
                    alert.dataset.autoDismiss = 'true';
                    setTimeout(() => dismissAlert(alert), 3000);
                });
        }

        scheduleAlerts();

        /* Also catch alerts injected dynamically (e.g. by fetch responses) */
        const observer = new MutationObserver(scheduleAlerts);
        observer.observe(document.body, { childList: true, subtree: true });
    }

    /* ══════════════════════════════════════════════════════════
       2. SCROLL-TO-TOP BUTTON
       ══════════════════════════════════════════════════════════ */
    function initScrollToTop() {
        const btn = document.createElement('button');
        btn.id          = 'scroll-top-btn';
        btn.innerHTML   = '<i class="bi bi-arrow-up"></i>';
        btn.title       = 'Back to top';
        btn.setAttribute('aria-label', 'Scroll to top');

        Object.assign(btn.style, {
            position:     'fixed',
            bottom:       '1.75rem',
            right:        '1.75rem',
            width:        '42px',
            height:       '42px',
            borderRadius: '50%',
            border:       'none',
            background:   'linear-gradient(135deg, #4f46e5 0%, #6366f1 100%)',
            color:        '#fff',
            fontSize:     '1.05rem',
            cursor:       'pointer',
            boxShadow:    '0 4px 14px rgba(79, 70, 229, 0.35)',
            display:      'flex',
            alignItems:   'center',
            justifyContent: 'center',
            opacity:      '0',
            transform:    'translateY(12px)',
            transition:   'opacity 0.3s ease, transform 0.3s ease, box-shadow 0.25s ease',
            zIndex:       '9999',
            pointerEvents: 'none',
        });

        document.body.appendChild(btn);

        let visible = false;

        window.addEventListener('scroll', () => {
            const shouldShow = window.scrollY > 280;
            if (shouldShow === visible) return;
            visible = shouldShow;
            btn.style.opacity      = shouldShow ? '1'    : '0';
            btn.style.transform    = shouldShow ? 'translateY(0)' : 'translateY(12px)';
            btn.style.pointerEvents = shouldShow ? 'auto' : 'none';
        }, { passive: true });

        btn.addEventListener('mouseenter', () => {
            btn.style.boxShadow = '0 6px 20px rgba(79, 70, 229, 0.5)';
            btn.style.transform = 'translateY(-2px)';
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.boxShadow = '0 4px 14px rgba(79, 70, 229, 0.35)';
            btn.style.transform = visible ? 'translateY(0)' : 'translateY(12px)';
        });

        btn.addEventListener('click', () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    /* ══════════════════════════════════════════════════════════
       3. FETCH LOADING SPINNER
       ══════════════════════════════════════════════════════════ */
    function initFetchSpinner() {
        /* Inject spinner bar at the very top of the page */
        const bar = document.createElement('div');
        bar.id = 'fetch-progress-bar';
        Object.assign(bar.style, {
            position:   'fixed',
            top:        '0',
            left:       '0',
            width:      '0%',
            height:     '3px',
            background: 'linear-gradient(90deg, #4f46e5, #818cf8)',
            zIndex:     '99999',
            transition: 'width 0.3s ease, opacity 0.4s ease',
            opacity:    '0',
            borderRadius: '0 2px 2px 0',
        });
        document.body.prepend(bar);

        let activeRequests = 0;

        function showBar() {
            bar.style.opacity = '1';
            bar.style.width   = '70%';
        }

        function hideBar() {
            bar.style.width   = '100%';
            setTimeout(() => {
                bar.style.opacity = '0';
                setTimeout(() => { bar.style.width = '0%'; }, 420);
            }, 200);
        }

        /* Patch the global fetch */
        const _fetch = window.fetch;
        window.fetch = function (...args) {
            if (activeRequests === 0) showBar();
            activeRequests++;

            return _fetch.apply(this, args).finally(() => {
                activeRequests--;
                if (activeRequests === 0) hideBar();
            });
        };
    }

    /* ══════════════════════════════════════════════════════════
       4. DEBOUNCED SEARCH INPUT (300 ms)
       ══════════════════════════════════════════════════════════ */
    function debounce(fn, delay) {
        let timer;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function initDebouncedSearch() {
        /* Target search inputs in the public navbar and any page-level search */
        const selectors = [
            '.navbar .search-form input[type="search"]',
            '.navbar .search-form input[name="q"]',
            'input[data-search]',
        ];

        selectors.forEach(sel => {
            document.querySelectorAll(sel).forEach(input => {
                if (input.dataset.debounced) return;
                input.dataset.debounced = 'true';

                const form = input.closest('form');

                /* Only auto-submit forms that opt-in via data-live-search */
                if (form && form.dataset.liveSearch !== undefined) {
                    const submit = debounce(() => form.requestSubmit(), 300);
                    input.addEventListener('input', submit);
                } else {
                    /* For all other search boxes: just prevent rapid-fire
                       keydown submissions, keeping native form submit intact */
                    let lastVal = input.value;
                    const track = debounce(() => { lastVal = input.value; }, 300);
                    input.addEventListener('input', track);
                }
            });
        });
    }

    /* ══════════════════════════════════════════════════════════
       5. ACTIVE STATE FOR NAVBAR LINKS
       ══════════════════════════════════════════════════════════ */
    function initNavActiveState() {
        const current = window.location.pathname.replace(/\/$/, '') || '/';

        document.querySelectorAll('.navbar .nav-link, .sidebar .nav-link').forEach(link => {
            try {
                const url  = new URL(link.href, window.location.origin);
                const path = url.pathname.replace(/\/$/, '') || '/';

                if (path === current) {
                    link.classList.add('active');
                    link.setAttribute('aria-current', 'page');
                } else if (path !== '/' && current.startsWith(path)) {
                    /* Partial match for nested routes (e.g. /products/123 → /products) */
                    link.classList.add('active');
                }
            } catch (_) {
                /* Ignore malformed hrefs */
            }
        });
    }

    /* ══════════════════════════════════════════════════════════
       NAVBAR SCROLL CLASS
       (adds .scrolled for CSS glass-shadow effect)
       ══════════════════════════════════════════════════════════ */
    function initNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;

        const toggle = () => navbar.classList.toggle('scrolled', window.scrollY > 10);
        toggle();
        window.addEventListener('scroll', toggle, { passive: true });
    }

    /* ══════════════════════════════════════════════════════════
       BOOT — run everything after DOM is ready
       ══════════════════════════════════════════════════════════ */
    function init() {
        initAutoHideAlerts();
        initScrollToTop();
        initFetchSpinner();
        initDebouncedSearch();
        initNavActiveState();
        initNavbarScroll();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
