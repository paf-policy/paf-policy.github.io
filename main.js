'use strict';

const navigation = document.querySelector('.nav-links');

// Keep the active section visible in the sticky navigation.
const sectionLinks = [...navigation.querySelectorAll('a')];
const sections = sectionLinks.map(link => document.querySelector(link.hash));
let scrollQueued = false;
function updateNavigation() {
  let current = null;
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= 150) current = section.id;
  }
  sectionLinks.forEach(link => {
    if (link.hash === `#${current}`) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
  scrollQueued = false;
}
window.addEventListener('scroll', () => {
  if (!scrollQueued) { requestAnimationFrame(updateNavigation); scrollQueued = true; }
}, { passive: true });
updateNavigation();

// Native controls remain available. Only visible affordance clips autoplay.
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const clips = [...document.querySelectorAll('.video-card video')];
const visibility = new Map();
const intent = new Map(clips.map(video => [video, video.hasAttribute('data-autoplay') && !reducedMotion.matches]));
const automaticPause = new WeakSet();
function pauseAutomatically(video) {
  if (!video.paused) { automaticPause.add(video); video.pause(); }
}
function playSafely(video) {
  if (!document.hidden) video.play().catch(() => { /* Native play remains available if autoplay is blocked. */ });
}
function syncVideo(video) {
  if (visibility.get(video) && intent.get(video) && !document.hidden) playSafely(video);
  else pauseAutomatically(video);
}
clips.forEach(video => {
  video.addEventListener('play', () => intent.set(video, true));
  video.addEventListener('pause', () => {
    if (automaticPause.has(video)) automaticPause.delete(video);
    else intent.set(video, false);
  });
});
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    visibility.set(entry.target, entry.isIntersecting);
    syncVideo(entry.target);
  }), { threshold: 0.15 });
  clips.forEach(video => observer.observe(video));
} else {
  clips.forEach(video => visibility.set(video, true));
}
document.addEventListener('visibilitychange', () => clips.forEach(syncVideo));
reducedMotion.addEventListener('change', event => {
  if (event.matches) clips.forEach(video => { intent.set(video, false); pauseAutomatically(video); });
});
document.querySelectorAll('video').forEach(video => {
  video.addEventListener('error', () => {
    if (video.parentElement.querySelector('.media-error')) return;
    const note = document.createElement('p');
    note.className = 'media-error';
    const link = document.createElement('a');
    link.href = video.currentSrc || video.src;
    link.textContent = 'Open the video directly';
    note.append('Unable to play this video. ', link, '.');
    video.insertAdjacentElement('afterend', note);
  });
});

// Enlarge paper figures without navigating away; Escape closes the dialog.
const lightbox = document.querySelector('.lightbox');
const lightboxImage = lightbox.querySelector('img');
const lightboxCaption = lightbox.querySelector('p');
document.querySelectorAll('.figure-button').forEach(button => {
  button.addEventListener('click', event => {
    if (typeof lightbox.showModal !== 'function') return;
    event.preventDefault();
    const source = button.querySelector('img');
    lightboxImage.src = source.src;
    lightboxImage.alt = source.alt;
    lightboxCaption.textContent = source.alt;
    lightbox.showModal();
    document.body.classList.add('modal-open');
  });
});
lightbox.querySelector('button').addEventListener('click', () => lightbox.close());
lightbox.addEventListener('click', event => {
  if (event.target === lightbox) {
    const bounds = lightbox.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) lightbox.close();
  }
});
lightbox.addEventListener('close', () => document.body.classList.remove('modal-open'));
