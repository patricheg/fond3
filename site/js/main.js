document.addEventListener('DOMContentLoaded', function () {
  var burger = document.querySelector('.burger');
  var nav = document.querySelector('.site-nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }

  // Тень у липкой шапки при прокрутке
  var header = document.querySelector('.site-header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('scrolled', window.scrollY > 8);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Плавное появление блоков при скролле
  var revealTargets = document.querySelectorAll(
    '.direction, .collection, .donate__inner, .gallery a, .article h2, .article p, .section__title'
  );
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (revealTargets.length && 'IntersectionObserver' in window && !reduceMotion) {
    revealTargets.forEach(function (el) { el.classList.add('reveal'); });
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealTargets.forEach(function (el) { observer.observe(el); });
  }

  var lightbox = document.getElementById('lightbox');
  if (lightbox) {

  var links = Array.prototype.slice.call(document.querySelectorAll('.gallery a'));
  var img = lightbox.querySelector('img');
  var current = 0;

  function show(index) {
    current = (index + links.length) % links.length;
    img.src = links[current].getAttribute('href');
    img.alt = links[current].querySelector('img').alt;
  }

  links.forEach(function (link, index) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      show(index);
      lightbox.classList.add('open');
      document.body.style.overflow = 'hidden';
    });
  });

  function close() {
    lightbox.classList.remove('open');
    document.body.style.overflow = '';
  }

  lightbox.querySelector('.lightbox__btn--close').addEventListener('click', close);
  lightbox.querySelector('.lightbox__btn--prev').addEventListener('click', function () { show(current - 1); });
  lightbox.querySelector('.lightbox__btn--next').addEventListener('click', function () { show(current + 1); });

  lightbox.addEventListener('click', function (event) {
    if (event.target === lightbox) close();
  });

  document.addEventListener('keydown', function (event) {
    if (!lightbox.classList.contains('open')) return;
    if (event.key === 'Escape') close();
    if (event.key === 'ArrowLeft') show(current - 1);
    if (event.key === 'ArrowRight') show(current + 1);
  });
  }

  // Увеличение картинок с классом .zoomable (например, реквизиты)
  // и кнопки .js-pay — сразу открыть блок с QR
  var zoomables = document.querySelectorAll('.zoomable');
  var payButtons = document.querySelectorAll('.js-pay');
  if (zoomables.length || payButtons.length) {
    var overlay = document.createElement('div');
    overlay.className = 'lightbox lightbox--zoom';
    overlay.innerHTML = '<button class="lightbox__btn lightbox__btn--close" aria-label="Закрыть">&times;</button><img alt="">';
    document.body.appendChild(overlay);
    var zimg = overlay.querySelector('img');

    function openZoom(src, alt) {
      zimg.src = src;
      zimg.alt = alt;
      overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeZoom() {
      overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    zoomables.forEach(function (el) {
      el.addEventListener('click', function () {
        openZoom(el.currentSrc || el.src, el.alt);
      });
    });

    payButtons.forEach(function (btn) {
      btn.addEventListener('click', function (event) {
        event.preventDefault();
        var payImg = document.querySelector('.donate__qr img');
        var src = btn.getAttribute('data-img') || (payImg && payImg.src) || 'assets/pay.webp';
        openZoom(src, 'Реквизиты для пожертвования');
      });
    });

    overlay.querySelector('.lightbox__btn--close').addEventListener('click', closeZoom);
    overlay.addEventListener('click', function (event) {
      if (event.target === overlay) closeZoom();
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && overlay.classList.contains('open')) closeZoom();
    });
  }
});
