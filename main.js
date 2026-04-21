// Copy to clipboard
function copyToClipboard(text, el) {
  navigator.clipboard.writeText(text).then(() => {
    const original = el.textContent;
    el.textContent = '✓ Gekopieerd!';
    el.style.color = 'var(--accent)';
    setTimeout(() => {
      el.textContent = original;
      el.style.color = '';
    }, 2000);
  });
}

// Scroll reveal
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('visible');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// Modal
function openModal(){
  document.getElementById('modalOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal(){
  document.getElementById('modalOverlay').classList.remove('open');
  document.body.style.overflow = '';
}
function closeModalOutside(e){
  if (e.target === document.getElementById('modalOverlay')) closeModal();
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

// Form submit → Formspree
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const original = btn.innerHTML;
    btn.innerHTML = 'Bezig met verzenden…';
    btn.disabled = true;

    try {
      const res = await fetch(form.action, {
        method:'POST', body:new FormData(form),
        headers:{ 'Accept':'application/json' }
      });
      if (res.ok) {
        form.innerHTML = `
          <div style="text-align:center;padding:24px 0;">
            <div style="font-family:'Fraunces',serif;font-style:italic;font-size:3.4rem;color:var(--accent);line-height:1;margin-bottom:18px;">Verstuurd.</div>
            <p style="color:var(--ink-soft);font-size:1rem;line-height:1.55;max-width:380px;margin:0 auto 28px;">Bedankt! Ik neem zo snel mogelijk contact met je op — meestal binnen een werkdag.</p>
            <button onclick="closeModal()" class="btn-primary" style="margin:0 auto;">
              Sluiten <span class="arrow">→</span>
            </button>
          </div>`;
      } else {
        btn.innerHTML = 'Fout — probeer opnieuw';
        btn.disabled = false;
        setTimeout(()=>{ btn.innerHTML = original; }, 2500);
      }
    } catch(err){
      btn.innerHTML = 'Fout — probeer opnieuw';
      btn.disabled = false;
    }
  });
}
