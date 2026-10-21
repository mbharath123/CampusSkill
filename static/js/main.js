/* ============================================================
   CampusSkill – main.js
   ============================================================ */

// ── Flash message auto-close ──────────────────────────────────
document.querySelectorAll('.alert-close').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.alert').style.animation = 'fadeIn .2s ease reverse';
    setTimeout(() => btn.closest('.alert').remove(), 200);
  });
});
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => {
    a.style.transition = 'opacity .5s';
    a.style.opacity = '0';
    setTimeout(() => a.remove(), 500);
  });
}, 5000);

// ── Sidebar mobile toggle ─────────────────────────────────────
const sidebar  = document.querySelector('.sidebar');
const overlay  = document.querySelector('.sidebar-overlay');
const hamburger = document.querySelector('.hamburger');

if (hamburger) {
  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  });
}
if (overlay) {
  overlay.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  });
}

// ── Active sidebar link highlight ─────────────────────────────
const currentPath = window.location.pathname;
document.querySelectorAll('.sidebar-link').forEach(link => {
  const href = link.getAttribute('href');
  if (href && (currentPath === href || (href !== '/' && currentPath.startsWith(href)))) {
    link.classList.add('active');
  }
});

// ── Tabs ──────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const group = btn.closest('[data-tabs]') || btn.parentElement.parentElement;
    group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const target = btn.dataset.tab;
    document.querySelectorAll('.tab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === target);
    });
  });
});

// ── Modal helpers ─────────────────────────────────────────────
function openModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.add('active'); document.body.style.overflow = 'hidden'; }
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) { m.classList.remove('active'); document.body.style.overflow = ''; }
}
// Close modal on backdrop click
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
  backdrop.addEventListener('click', e => {
    if (e.target === backdrop) closeModal(backdrop.id);
  });
});
// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-backdrop.active').forEach(m => {
      m.classList.remove('active');
      document.body.style.overflow = '';
    });
  }
});

// ── Request modal population ──────────────────────────────────
document.querySelectorAll('[data-request-btn]').forEach(btn => {
  btn.addEventListener('click', () => {
    const skillId    = btn.dataset.skillId;
    const providerId = btn.dataset.providerId;
    const modal = document.getElementById('requestModal');
    if (!modal) return;

    // Pre-fill hidden fields
    modal.querySelector('[name="skill_id"]').value    = skillId;
    modal.querySelector('[name="provider_id"]').value = providerId;

    // Fetch info from API
    fetch(`/api/request_modal_data?skill_id=${skillId}&provider_id=${providerId}`)
      .then(r => r.json())
      .then(data => {
        modal.querySelector('#modal-skill-name').textContent    = data.skill_name    || '';
        modal.querySelector('#modal-provider-name').textContent = data.provider_name || '';
        modal.querySelector('#modal-level').textContent         = data.proficiency_level || '';
      })
      .catch(() => {});

    openModal('requestModal');
  });
});

// ── Edit skill modal population ───────────────────────────────
document.querySelectorAll('[data-edit-skill]').forEach(btn => {
  btn.addEventListener('click', () => {
    const skillId = btn.dataset.editSkill;
    fetch(`/api/skills/${skillId}`)
      .then(r => r.json())
      .then(skill => {
        const modal = document.getElementById('editSkillModal');
        if (!modal) return;
        modal.querySelector('[name="skill_name"]').value         = skill.skill_name || '';
        modal.querySelector('[name="category"]').value           = skill.category   || '';
        modal.querySelector('[name="proficiency_level"]').value  = skill.proficiency_level || '';
        modal.querySelector('[name="description"]').value        = skill.description || '';
        modal.querySelector('form').action = `/skills/edit/${skillId}`;
        openModal('editSkillModal');
      });
  });
});

// ── Delete confirm ────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    if (!confirm(form.dataset.confirm || 'Are you sure?')) {
      e.preventDefault();
    }
  });
});

// ── Schedule session modal ────────────────────────────────────
document.querySelectorAll('[data-schedule-btn]').forEach(btn => {
  btn.addEventListener('click', () => {
    const reqId = btn.dataset.requestId;
    const modal = document.getElementById('scheduleModal');
    if (modal) {
      modal.querySelector('[name="request_id"]').value = reqId;
      openModal('scheduleModal');
    }
  });
});

// ── Update session modal ──────────────────────────────────────
document.querySelectorAll('[data-edit-session]').forEach(btn => {
  btn.addEventListener('click', () => {
    const sid  = btn.dataset.sessionId;
    const date = btn.dataset.date;
    const time = btn.dataset.time;
    const dur  = btn.dataset.duration;
    const meet = btn.dataset.meeting;
    const modal = document.getElementById('editSessionModal');
    if (!modal) return;
    modal.querySelector('[name="session_date"]').value     = date || '';
    modal.querySelector('[name="start_time"]').value       = time ? time.substring(0,5) : '';
    modal.querySelector('[name="duration_minutes"]').value = dur  || 60;
    modal.querySelector('[name="meeting_details"]').value  = meet || '';
    modal.querySelector('form').action = `/sessions/${sid}/update`;
    openModal('editSessionModal');
  });
});

// ── Form loading state ─────────────────────────────────────────
document.querySelectorAll('form[data-loading]').forEach(form => {
  form.addEventListener('submit', () => {
    const btn = form.querySelector('[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> Processing…';
    }
  });
});

// ── Scroll-triggered number animation for hero stats ──────────
function animateCount(el) {
  const target = parseInt(el.dataset.target || el.textContent, 10);
  if (isNaN(target)) return;
  let start = 0;
  const step = Math.ceil(target / 40);
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start + (el.dataset.suffix || '');
    if (start >= target) clearInterval(timer);
  }, 30);
}
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('[data-animate-count]').forEach(animateCount);
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.2 });
document.querySelectorAll('.hero-stats').forEach(el => observer.observe(el));

// ── Category icon map ─────────────────────────────────────────
const CATEGORY_ICONS = {
  'Programming':     '💻',
  'Database':        '🗄️',
  'Web Development': '🌐',
  'AI/ML':           '🤖',
  'Design':          '🎨',
  'Communication':   '💬',
  'Other':           '📚',
};
document.querySelectorAll('[data-category-icon]').forEach(el => {
  el.textContent = CATEGORY_ICONS[el.dataset.categoryIcon] || '📚';
});
