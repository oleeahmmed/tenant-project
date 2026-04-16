(function () {
  'use strict';

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function $all(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /** HSL components as space-separated string for CSS variables */
  var PRESETS = {
    shadcn: {
      label: 'Shadcn',
      /* Light: dark slate primary (shadcn/ui default) */
      primary: '222.2 47.4% 11.2%',
      primaryForeground: '210 40% 98%',
      ring: '222.2 84% 4.9%',
      chart1: '222.2 47.4% 11.2%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '221.2 83.2% 53.3%',
      /* Dark: light primary + zinc charts (same as index.html .dark) — dark slate primary is invisible on dark bg */
      darkPrimary: '0 0% 98%',
      darkPrimaryForeground: '240 5.9% 10%',
      darkRing: '240 4.9% 65.9%',
      darkChart1: '221 83% 53%',
      darkChart2: '240 4.9% 65.9%',
      darkChart3: '240 5.3% 15.9%',
      darkChart4: '240 5.9% 10%',
      darkChart5: '142 71% 45%',
      swatches: ['#0f172a', '#64748b', '#e2e8f0', '#f8fafc'],
    },
    corporate: {
      label: 'Corporate',
      primary: '221.2 83.2% 53.3%',
      primaryForeground: '210 40% 98%',
      ring: '221.2 83.2% 53.3%',
      chart1: '221.2 83.2% 53.3%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '214.3 31.8% 91.4%',
      chart4: '210 40% 96.1%',
      chart5: '199 89% 48%',
      swatches: ['#3b82f6', '#93c5fd', '#dbeafe', '#eff6ff'],
    },
    spotify: {
      label: 'Spotify',
      primary: '142.1 76.2% 36.3%',
      primaryForeground: '355.7 100% 97.3%',
      ring: '142.1 76.2% 36.3%',
      chart1: '142.1 76.2% 36.3%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '84 81% 44%',
      swatches: ['#1db954', '#1ed760', '#121212', '#282828'],
    },
    saas: {
      label: 'SaaS',
      primary: '262.1 83.3% 57.8%',
      primaryForeground: '210 40% 98%',
      ring: '262.1 83.3% 57.8%',
      chart1: '262.1 83.3% 57.8%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '280 65% 60%',
      swatches: ['#8b5cf6', '#a78bfa', '#ede9fe', '#f5f3ff'],
    },
    nature: {
      label: 'Nature',
      primary: '142 71% 45%',
      primaryForeground: '144 100% 98%',
      ring: '142 71% 45%',
      chart1: '142 71% 45%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '88 50% 53%',
      swatches: ['#16a34a', '#4ade80', '#dcfce7', '#f0fdf4'],
    },
    vintage: {
      label: 'Vintage',
      primary: '25 95% 53%',
      primaryForeground: '0 0% 100%',
      ring: '25 95% 53%',
      chart1: '25 95% 53%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '40 30% 90%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '340 75% 55%',
      swatches: ['#ea580c', '#fb923c', '#ffedd5', '#fff7ed'],
    },
    ghibli: {
      label: 'Ghibli',
      primary: '200 98% 39%',
      primaryForeground: '210 40% 98%',
      ring: '200 98% 39%',
      chart1: '200 98% 39%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '195 100% 95%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '45 93% 58%',
      swatches: ['#0284c7', '#38bdf8', '#e0f2fe', '#f0f9ff'],
    },
    slack: {
      label: 'Slack',
      primary: '300 47% 48%',
      primaryForeground: '0 0% 100%',
      ring: '300 47% 48%',
      chart1: '300 47% 48%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '160 84% 39%',
      swatches: ['#611f69', '#ecb22e', '#36c5f0', '#2eb67d'],
    },
    /* Shadcn registry–style primary hues (light mode — same tokens as shadcn/ui theme) */
    rose: {
      label: 'Rose',
      primary: '346.8 77.2% 49.8%',
      primaryForeground: '355.7 100% 97.3%',
      ring: '346.8 77.2% 49.8%',
      chart1: '346.8 77.2% 49.8%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '336 80% 95%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '340 75% 55%',
      swatches: ['#e11d48', '#fb7185', '#ffe4e6', '#fff1f2'],
    },
    blue: {
      label: 'Blue',
      primary: '221.2 83.2% 53.3%',
      primaryForeground: '210 40% 98%',
      ring: '221.2 83.2% 53.3%',
      chart1: '221.2 83.2% 53.3%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '214.3 31.8% 91.4%',
      chart4: '199 89% 48%',
      chart5: '210 40% 96.1%',
      swatches: ['#2563eb', '#60a5fa', '#dbeafe', '#eff6ff'],
    },
    green: {
      label: 'Green',
      primary: '142.1 76.2% 36.3%',
      primaryForeground: '355.7 100% 97.3%',
      ring: '142.1 76.2% 36.3%',
      chart1: '142.1 76.2% 36.3%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '84 81% 44%',
      chart5: '134 65% 45%',
      swatches: ['#16a34a', '#4ade80', '#dcfce7', '#f0fdf4'],
    },
    orange: {
      label: 'Orange',
      primary: '24.6 95% 53.1%',
      primaryForeground: '0 0% 100%',
      ring: '24.6 95% 53.1%',
      chart1: '24.6 95% 53.1%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '40 30% 90%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '25 95% 53%',
      swatches: ['#ea580c', '#fb923c', '#ffedd5', '#fff7ed'],
    },
    violet: {
      label: 'Violet',
      primary: '262.1 83.3% 57.8%',
      primaryForeground: '210 40% 98%',
      ring: '262.1 83.3% 57.8%',
      chart1: '262.1 83.3% 57.8%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '210 40% 96.1%',
      chart4: '270 65% 60%',
      chart5: '280 100% 70%',
      swatches: ['#7c3aed', '#a78bfa', '#ede9fe', '#f5f3ff'],
    },
    amber: {
      label: 'Amber',
      primary: '32.1 94.6% 43.7%',
      primaryForeground: '26 100% 10%',
      ring: '32.1 94.6% 43.7%',
      chart1: '32.1 94.6% 43.7%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '48 100% 96%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '45 93% 58%',
      swatches: ['#d97706', '#fbbf24', '#fef3c7', '#fffbeb'],
    },
    red: {
      label: 'Red',
      primary: '0 72.2% 50.6%',
      primaryForeground: '0 0% 100%',
      ring: '0 72.2% 50.6%',
      chart1: '0 72.2% 50.6%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '0 86% 97%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '350 89% 60%',
      swatches: ['#dc2626', '#f87171', '#fee2e2', '#fef2f2'],
    },
    cyan: {
      label: 'Cyan',
      primary: '188.7 94.5% 42.7%',
      primaryForeground: '196 100% 97%',
      ring: '188.7 94.5% 42.7%',
      chart1: '188.7 94.5% 42.7%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '186 100% 94%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '199 89% 48%',
      swatches: ['#0891b2', '#22d3ee', '#cffafe', '#ecfeff'],
    },
    pink: {
      label: 'Pink',
      primary: '330.4 81.2% 60.4%',
      primaryForeground: '0 0% 100%',
      ring: '330.4 81.2% 60.4%',
      chart1: '330.4 81.2% 60.4%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '327 73% 97%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '340 75% 55%',
      swatches: ['#db2777', '#f472b6', '#fce7f3', '#fdf2f8'],
    },
    lime: {
      label: 'Lime',
      primary: '85.5 79.2% 42.2%',
      primaryForeground: '26 100% 10%',
      ring: '85.5 79.2% 42.2%',
      chart1: '85.5 79.2% 42.2%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '86 85% 93%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '142 71% 45%',
      swatches: ['#65a30d', '#a3e635', '#ecfccb', '#f7fee7'],
    },
    indigo: {
      label: 'Indigo',
      primary: '238.7 83.5% 66.7%',
      primaryForeground: '210 40% 98%',
      ring: '238.7 83.5% 66.7%',
      chart1: '238.7 83.5% 66.7%',
      chart2: '215.4 16.3% 46.9%',
      chart3: '226 100% 97%',
      chart4: '214.3 31.8% 91.4%',
      chart5: '262 83% 58%',
      swatches: ['#4f46e5', '#818cf8', '#e0e7ff', '#eef2ff'],
    },
  };

  /** Hue from "H S% L%" for tinted backgrounds (grayscale → slate 222) */
  function parseHueFromPrimary(primary) {
    var parts = String(primary).trim().split(/\s+/);
    var h = parseFloat(parts[0]);
    var s = parseFloat(parts[1]);
    if (isNaN(h)) return 222;
    if (isNaN(s) || s < 6) return 222;
    return h;
  }

  /** Apply --background, --card, --muted, --border, --accent, etc. from theme hue */
  function applyThemeSurfaces(hue, isDark, root) {
    if (isDark) {
      root.style.setProperty('--background', hue + ' 14% 8%');
      root.style.setProperty('--foreground', '0 0% 98%');
      root.style.setProperty('--card', hue + ' 11% 10.5%');
      root.style.setProperty('--card-foreground', '0 0% 98%');
      root.style.setProperty('--popover', hue + ' 11% 10.5%');
      root.style.setProperty('--popover-foreground', '0 0% 98%');
      root.style.setProperty('--muted', hue + ' 9% 14%');
      root.style.setProperty('--muted-foreground', hue + ' 6% 63%');
      root.style.setProperty('--accent', hue + ' 10% 16%');
      root.style.setProperty('--accent-foreground', '0 0% 98%');
      root.style.setProperty('--border', hue + ' 8% 17%');
      root.style.setProperty('--input', hue + ' 8% 17%');
      root.style.setProperty('--secondary', hue + ' 9% 15%');
      root.style.setProperty('--secondary-foreground', '0 0% 98%');
    } else {
      root.style.setProperty('--background', hue + ' 30% 99%');
      root.style.setProperty('--foreground', '222.2 84% 4.9%');
      root.style.setProperty('--card', '0 0% 100%');
      root.style.setProperty('--card-foreground', '222.2 84% 4.9%');
      root.style.setProperty('--popover', '0 0% 100%');
      root.style.setProperty('--popover-foreground', '222.2 84% 4.9%');
      root.style.setProperty('--muted', hue + ' 22% 96%');
      root.style.setProperty('--muted-foreground', '215.4 16.3% 46.9%');
      root.style.setProperty('--accent', hue + ' 25% 95%');
      root.style.setProperty('--accent-foreground', '222.2 47.4% 11.2%');
      root.style.setProperty('--border', hue + ' 16% 90%');
      root.style.setProperty('--input', hue + ' 16% 90%');
      root.style.setProperty('--secondary', hue + ' 20% 96%');
      root.style.setProperty('--secondary-foreground', '222.2 47.4% 11.2%');
    }
  }

  function applyPreset(name) {
    var p = PRESETS[name];
    if (!p) return;
    var r = document.documentElement;
    var isDark = r.classList.contains('dark');
    var hue = parseHueFromPrimary(p.primary);
    if (isDark && p.darkPrimary) {
      r.style.setProperty('--primary', p.darkPrimary);
      r.style.setProperty('--primary-foreground', p.darkPrimaryForeground);
      r.style.setProperty('--ring', p.darkRing);
      for (var di = 1; di <= 5; di++) {
        var dk = 'darkChart' + di;
        if (p[dk]) r.style.setProperty('--chart-' + di, p[dk]);
      }
      hue = 240;
    } else {
      r.style.setProperty('--primary', p.primary);
      r.style.setProperty('--primary-foreground', p.primaryForeground);
      r.style.setProperty('--ring', p.ring);
      for (var i = 1; i <= 5; i++) {
        var key = 'chart' + i;
        if (p[key]) r.style.setProperty('--chart-' + i, p[key]);
      }
    }
    applyThemeSurfaces(hue, isDark, r);

    r.setAttribute('data-theme', name);
    try {
      localStorage.setItem('admin-theme', name);
    } catch (e) {}

    $all('[data-theme-item]').forEach(function (el) {
      var active = el.getAttribute('data-theme-item') === name;
      el.setAttribute('aria-pressed', active ? 'true' : 'false');
      el.classList.toggle('ring-2', active);
      el.classList.toggle('ring-primary', active);
      el.classList.toggle('ring-offset-2', active);
      el.classList.toggle('ring-offset-background', active);
    });

    var label = $('#theme-active-label');
    if (label) label.textContent = p.label;
  }

  /** Convert #rrggbb to "H S% L%" for --primary */
  function hexToHslString(hex) {
    hex = hex.replace(/^#/, '');
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    var r = parseInt(hex.slice(0, 2), 16) / 255;
    var g = parseInt(hex.slice(2, 4), 16) / 255;
    var b = parseInt(hex.slice(4, 6), 16) / 255;
    var max = Math.max(r, g, b);
    var min = Math.min(r, g, b);
    var h = 0;
    var s = 0;
    var l = (max + min) / 2;
    if (max !== min) {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r:
          h = (g - b) / d + (g < b ? 6 : 0);
          break;
        case g:
          h = (b - r) / d + 2;
          break;
        default:
          h = (r - g) / d + 4;
      }
      h /= 6;
    }
    h = Math.round(h * 360 * 10) / 10;
    s = Math.round(s * 1000) / 10;
    l = Math.round(l * 1000) / 10;
    return h + ' ' + s + '% ' + l + '%';
  }

  function applyCustomPrimary(hex) {
    var hsl = hexToHslString(hex);
    var r = document.documentElement;
    var isDark = r.classList.contains('dark');
    r.style.setProperty('--primary', hsl);
    r.style.setProperty('--ring', hsl);
    var parts = hsl.split(' ');
    var l = parseFloat(String(parts[2]).replace('%', ''));
    var fg = l > 55 ? '222.2 47.4% 11.2%' : '210 40% 98%';
    r.style.setProperty('--primary-foreground', fg);
    applyThemeSurfaces(parseHueFromPrimary(hsl), isDark, r);
    r.setAttribute('data-theme', 'custom');
    try {
      localStorage.setItem('admin-custom-primary', hex);
      localStorage.removeItem('admin-theme');
    } catch (e) {}
    $all('[data-theme-item]').forEach(function (el) {
      el.setAttribute('aria-pressed', 'false');
      el.classList.remove('ring-2', 'ring-primary', 'ring-offset-2', 'ring-offset-background');
    });
    var label = $('#theme-active-label');
    if (label) label.textContent = 'Custom';
    var picker = $('#primary-color');
    var pickerPanel = $('#primary-color-panel');
    if (picker) picker.value = hex;
    if (pickerPanel) pickerPanel.value = hex;
  }

  function setDark(on) {
    document.documentElement.classList.toggle('dark', on);
    try {
      localStorage.setItem('admin-dark', on ? '1' : '0');
    } catch (e) {}
    var sun = $('#icon-theme-sun');
    var moon = $('#icon-theme-moon');
    if (sun && moon) {
      sun.classList.toggle('hidden', !on);
      moon.classList.toggle('hidden', on);
    }
    var customHex = null;
    var savedTheme = null;
    try {
      customHex = localStorage.getItem('admin-custom-primary');
      savedTheme = localStorage.getItem('admin-theme');
    } catch (e) {}
    if (customHex && !savedTheme) {
      applyCustomPrimary(customHex);
    } else if (savedTheme && PRESETS[savedTheme]) {
      applyPreset(savedTheme);
    } else {
      applyPreset('shadcn');
    }
    if (window.lucide && typeof lucide.createIcons === 'function') {
      lucide.createIcons();
    }
  }

  // —— Existing UI ——
  var sidebar = $('#sidebar');
  var overlay = $('#sidebar-overlay');
  var btnMenu = $('#btn-menu');

  function openSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.remove('-translate-x-full');
    overlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!sidebar || !overlay) return;
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
    document.body.style.overflow = '';
  }

  if (btnMenu) {
    btnMenu.addEventListener('click', function () {
      if (sidebar && sidebar.classList.contains('-translate-x-full')) openSidebar();
      else closeSidebar();
    });
  }
  if (overlay) overlay.addEventListener('click', closeSidebar);
  window.addEventListener('resize', function () {
    if (window.innerWidth >= 1024) closeSidebar();
  });

  function closeAllDropdowns() {
    $all('.dropdown-panel').forEach(function (el) {
      el.classList.add('hidden');
    });
  }

  $all('.dropdown-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var id = btn.getAttribute('data-dropdown');
      var panel = id ? document.getElementById(id) : null;
      if (!panel) return;
      var isHidden = panel.classList.contains('hidden');
      closeAllDropdowns();
      if (isHidden) panel.classList.remove('hidden');
    });
  });

  document.addEventListener('click', closeAllDropdowns);

  $all('.dropdown-panel').forEach(function (panel) {
    panel.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  });

  $all('.submenu-toggle').forEach(function (toggle) {
    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      var id = toggle.getAttribute('data-target');
      var sub = id ? document.getElementById(id) : null;
      if (!sub) return;
      sub.classList.toggle('hidden');
    });
  });

  var btnCollapse = $('#btn-collapse');
  if (btnCollapse && sidebar) {
    btnCollapse.addEventListener('click', function () {
      var collapsed = sidebar.getAttribute('data-collapsed') === 'true';
      collapsed = !collapsed;
      sidebar.setAttribute('data-collapsed', collapsed ? 'true' : 'false');
      var icon = $('#collapse-icon');
      if (icon) icon.textContent = collapsed ? '»' : '«';
    });
  }

  var customizer = $('#customizer');
  var backdrop = $('#customizer-backdrop');
  var btnCustomizer = $('#btn-customizer');
  var btnClose = $('#btn-close-customizer');

  function openCustomizer() {
    if (!customizer) return;
    customizer.classList.remove('translate-x-full');
    customizer.setAttribute('aria-hidden', 'false');
    if (backdrop) backdrop.classList.remove('hidden');
  }

  function closeCustomizer() {
    if (!customizer) return;
    customizer.classList.add('translate-x-full');
    customizer.setAttribute('aria-hidden', 'true');
    if (backdrop) backdrop.classList.add('hidden');
  }

  if (btnCustomizer) btnCustomizer.addEventListener('click', openCustomizer);
  if (btnClose) btnClose.addEventListener('click', closeCustomizer);
  if (backdrop) backdrop.addEventListener('click', closeCustomizer);

  function initTheme() {
    var savedName = null;
    try {
      savedName = localStorage.getItem('admin-theme');
    } catch (e) {}
    var customHex = null;
    try {
      customHex = localStorage.getItem('admin-custom-primary');
    } catch (e) {}
    var dark = false;
    try {
      dark = localStorage.getItem('admin-dark') === '1';
    } catch (e) {}

    document.documentElement.classList.toggle('dark', dark);
    var sun = $('#icon-theme-sun');
    var moon = $('#icon-theme-moon');
    if (sun && moon) {
      sun.classList.toggle('hidden', !dark);
      moon.classList.toggle('hidden', dark);
    }

    if (customHex && !savedName) {
      var pickerInit = $('#primary-color');
      if (pickerInit) pickerInit.value = customHex;
      applyCustomPrimary(customHex);
    } else {
      applyPreset(savedName && PRESETS[savedName] ? savedName : 'shadcn');
    }

    $all('[data-theme-item]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var name = btn.getAttribute('data-theme-item');
        applyPreset(name);
        try {
          localStorage.removeItem('admin-custom-primary');
        } catch (err) {}
      });
    });

    var btnToggle = $('#btn-theme-toggle');
    if (btnToggle) {
      btnToggle.addEventListener('click', function (e) {
        e.stopPropagation();
        setDark(!document.documentElement.classList.contains('dark'));
      });
    }

    var picker = $('#primary-color');
    var pickerPanel = $('#primary-color-panel');
    if (picker) {
      picker.addEventListener('input', function () {
        applyCustomPrimary(picker.value);
      });
    }
    if (pickerPanel) {
      pickerPanel.addEventListener('input', function () {
        applyCustomPrimary(pickerPanel.value);
      });
    }

    var btnCustomizerLight = $('#customizer-light');
    var btnCustomizerDark = $('#customizer-dark');
    if (btnCustomizerLight)
      btnCustomizerLight.addEventListener('click', function () {
        setDark(false);
      });
    if (btnCustomizerDark)
      btnCustomizerDark.addEventListener('click', function () {
        setDark(true);
      });

    if (window.lucide && typeof lucide.createIcons === 'function') {
      lucide.createIcons();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();
