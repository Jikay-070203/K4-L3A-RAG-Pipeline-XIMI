const conversation = document.querySelector('#conversation');
const composer = document.querySelector('#composer');
const queryInput = document.querySelector('#query');
const sources = document.querySelector('#sources');
const sourceCount = document.querySelector('#source-count');
const topK = document.querySelector('#top-k');
const topKValue = document.querySelector('#top-k-value');

const demoSources = [
  { title:'IELTS Writing Task 1 — Tiêu chí mẫu', source:'sample_task1_criteria.md', method:'hybrid', score:'0.92' },
  { title:'Cách luyện Coherence and Cohesion', source:'sample_article_01.md', method:'hybrid', score:'0.81' },
];

function addMessage(role, text) {
  const item = document.createElement('div');
  item.className = `message ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = role === 'user' ? 'U' : 'R';

  const bubbleWrap = document.createElement('div');
  bubbleWrap.className = 'bubble-wrap';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;

  bubbleWrap.appendChild(bubble);
  item.appendChild(avatar);
  item.appendChild(bubbleWrap);
  conversation.appendChild(item);
  conversation.scrollTop = conversation.scrollHeight;
}

function renderSources(items) {
  sourceCount.textContent = items.length;
  sources.className = '';
  sources.innerHTML = items.map((item, index) => `
    <article class="source-card">
      <div class="source-head">
        <span class="source-index">[${index + 1}]</span>
        <h3>${item.title}</h3>
      </div>
      <div class="source-meta">
        <span class="file">${item.source}</span>
        <span class="score">${item.score}</span>
      </div>
      <div class="source-meta">
        <span class="method">retrieval: ${item.method}</span>
      </div>
    </article>
  `).join('');
}

function submitQuery(text) {
  const query = text.trim();
  if (!query) return;
  document.querySelector('#welcome-card')?.remove();
  addMessage('user', query);
  addMessage('assistant', 'Đây là giao diện mẫu. Khi Task 10 hoàn thành, phần này sẽ nhận answer từ generate_with_citation() và hiển thị citation tương ứng với sources.');
  renderSources(demoSources.slice(0, Number(topK.value) >= 5 ? 2 : 1));
  queryInput.value = '';
  autoGrow();
}

/* -------- Textarea: Enter để gửi, Shift+Enter xuống dòng -------- */
function autoGrow() {
  queryInput.style.height = 'auto';
  queryInput.style.height = Math.min(queryInput.scrollHeight, 180) + 'px';
}
queryInput.addEventListener('input', autoGrow);

queryInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    submitQuery(queryInput.value);
  }
});

topK.addEventListener('input', () => { topKValue.textContent = topK.value; });
composer.addEventListener('submit', (event) => { event.preventDefault(); submitQuery(queryInput.value); });
document.querySelector('#new-chat').addEventListener('click', () => window.location.reload());
document.querySelectorAll('.suggestion').forEach((button) =>
  button.addEventListener('click', () => submitQuery(button.textContent))
);