// Анимация появления при скролле
function initReveal() {
  const els = document.querySelectorAll('.reveal');
  els.forEach(el => el.classList.add('animate'));

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: .15 });
  els.forEach(el => observer.observe(el));

  // Херо появляется сразу с микро-задержкой для плавности
  setTimeout(() => {
    document.querySelector('.hero')?.classList.add('visible');
  }, 80);
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  const form = document.getElementById('contact-form');
  const submitBtn = document.getElementById('submit-btn');
  const result = document.getElementById('result');
  const nameInput = document.getElementById('name');
  const phoneInput = document.getElementById('phone');
  const emailInput = document.getElementById('email');
  const commentInput = document.getElementById('comment');
  const charCount = document.getElementById('char-count');

  // Счётчик символов
  commentInput.addEventListener('input', () => {
    charCount.textContent = `${commentInput.value.length} / 3000`;
  });

  // Проверка здоровья при загрузке
  fetchHealth();

  // Отправка формы
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const payload = {
      name: nameInput.value.trim(),
      phone: phoneInput.value.trim(),
      email: emailInput.value.trim(),
      comment: commentInput.value.trim(),
    };

    // Валидация на клиенте
    let valid = true;
    if (payload.name.length < 2 || payload.name.length > 100) {
      showError('name', 'Имя должно быть от 2 до 100 символов');
      valid = false;
    }
    if (!/^\+?\d{7,15}$/.test(payload.phone)) {
      showError('phone', 'Неверный формат телефона');
      valid = false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(payload.email)) {
      showError('email', 'Неверный формат email');
      valid = false;
    }
    if (payload.comment.length < 10 || payload.comment.length > 3000) {
      showError('comment', 'Сообщение должно быть от 10 до 3000 символов');
      valid = false;
    }
    if (!valid) return;

    submitBtn.classList.add('loading');

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok) {
        showResult(data);
        form.reset();
        charCount.textContent = '0 / 3000';
      } else if (res.status === 429) {
        showError('comment', 'Превышен лимит запросов. Подождите минуту.');
      } else if (res.status === 422) {
        handleValidationError(data);
      } else {
        showError('comment', 'Ошибка сервера. Попробуйте позже.');
      }
    } catch {
      showError('comment', 'Сетевая ошибка. Проверьте подключение.');
    } finally {
      submitBtn.classList.remove('loading');
    }
  });
});

function showError(field, msg) {
  const el = document.getElementById(`${field}-error`);
  const input = document.getElementById(field);
  if (el) el.textContent = msg;
  if (input) input.classList.add('error');
}

function clearErrors() {
  document.querySelectorAll('.error').forEach(el => el.textContent = '');
  document.querySelectorAll('input.error, textarea.error').forEach(el => el.classList.remove('error'));
}

function handleValidationError(data) {
  if (data.detail) {
    data.detail.forEach(err => {
      const field = err.loc?.[err.loc.length - 1] || 'comment';
      showError(field, err.msg);
    });
  }
}

function showResult(data) {
  const result = document.getElementById('result');
  result.style.display = 'block';

  const d = data.data || data;
  const sentiment = d.sentiment || 'unknown';
  const reason = d.reason || '—';
  const name = d.name || '—';
  const email = d.email || '—';

  document.getElementById('result-icon').className = `result-icon ${sentiment}`;
  document.getElementById('result-title').textContent = data.success ? 'Сообщение отправлено' : 'Ошибка';
  document.getElementById('result-subtitle').textContent = data.success
    ? (sentiment === 'unknown' ? 'AI-анализ временно недоступен' : 'Анализ тональности завершён')
    : 'Произошла ошибка при обработке';
  document.getElementById('result-sentiment').textContent = translateSentiment(sentiment);
  document.getElementById('result-reason').textContent = reason;
  document.getElementById('result-name').textContent = name;
  document.getElementById('result-email').textContent = email;

  result.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function translateSentiment(s) {
  const map = { positive: 'Позитивная', neutral: 'Нейтральная', negative: 'Негативная', unknown: 'Не определена' };
  return map[s] || s;
}

async function fetchHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    const healthDot = document.getElementById('health-dot');
    const aiDot = document.getElementById('ai-dot');
    const healthStatus = document.getElementById('health-status');
    const aiStatus = document.getElementById('ai-status');

    healthDot.className = 'status-dot ' + (data.status === 'здоров' ? 'green' : 'red');
    healthStatus.textContent = data.status === 'здоров' ? 'Работает' : 'Недоступен';
    aiDot.className = 'status-dot ai ' + (data.ai_status === 'доступен' ? 'green' : 'red');
    aiStatus.textContent = data.ai_status === 'доступен' ? 'Доступен' : 'Недоступен';
  } catch {
    // молча пропускаем ошибку
  }
}
