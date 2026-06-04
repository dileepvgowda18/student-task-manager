const authCard = document.getElementById('auth-card');
const tasksCard = document.getElementById('tasks-card');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const authForm = document.getElementById('auth-form');
const authMessage = document.getElementById('auth-message');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const authSubmit = document.getElementById('auth-submit');
const welcomeText = document.getElementById('welcome-text');
const logoutButton = document.getElementById('logout-button');
const taskForm = document.getElementById('task-form');
const taskTitleInput = document.getElementById('task-title');
const taskDescriptionInput = document.getElementById('task-description');
const taskList = document.getElementById('task-list');

let isLoginMode = true;

function setActiveTab(loginMode) {
  isLoginMode = loginMode;
  loginTab.classList.toggle('active', loginMode);
  registerTab.classList.toggle('active', !loginMode);
  authSubmit.textContent = loginMode ? 'Login' : 'Register';
  authMessage.textContent = '';
}

loginTab.addEventListener('click', () => setActiveTab(true));
registerTab.addEventListener('click', () => setActiveTab(false));

async function apiRequest(path, options = {}) {
  const response = await fetch(`/api/${path}`, {
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed.');
  }
  return data;
}

async function checkSession() {
  try {
    const data = await apiRequest('user');
    if (data.user) {
      showTasks(data.user.username);
      return true;
    }
  } catch (error) {
    console.warn(error);
  }
  showAuth();
  return false;
}

function showAuth() {
  authCard.classList.remove('hidden');
  tasksCard.classList.add('hidden');
}

function showTasks(username) {
  authCard.classList.add('hidden');
  tasksCard.classList.remove('hidden');
  welcomeText.textContent = `Welcome, ${username}`;
  authMessage.textContent = '';
  loadTasks();
}

authForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  authMessage.textContent = 'Processing...';

  const payload = {
    username: usernameInput.value.trim(),
    password: passwordInput.value.trim(),
  };

  const action = isLoginMode ? 'login' : 'register';
  try {
    const data = await apiRequest(action, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    showTasks(data.username);
  } catch (error) {
    authMessage.textContent = error.message;
  }
});

logoutButton.addEventListener('click', async () => {
  await apiRequest('logout', { method: 'POST' });
  showAuth();
});

taskForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = taskTitleInput.value.trim();
  const description = taskDescriptionInput.value.trim();
  if (!title) return;

  try {
    await apiRequest('tasks', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
    taskTitleInput.value = '';
    taskDescriptionInput.value = '';
    loadTasks();
  } catch (error) {
    console.error(error);
  }
});

async function loadTasks() {
  taskList.innerHTML = '<p>Loading tasks...</p>';
  try {
    const data = await apiRequest('tasks');
    if (!data.tasks.length) {
      taskList.innerHTML = '<p class="message">No tasks yet. Add one above!</p>';
      return;
    }
    taskList.innerHTML = '';
    data.tasks.forEach(renderTask);
  } catch (error) {
    taskList.innerHTML = `<p class="message">${error.message}</p>`;
  }
}

function renderTask(task) {
  const item = document.createElement('article');
  item.className = 'task-item';

  const titleRow = document.createElement('div');
  titleRow.className = 'task-main';

  const title = document.createElement('h3');
  title.className = `task-title${task.completed ? ' completed' : ''}`;
  title.textContent = task.title;

  const actions = document.createElement('div');
  actions.className = 'task-actions';

  const completeButton = document.createElement('button');
  completeButton.type = 'button';
  completeButton.className = 'complete-btn';
  completeButton.textContent = task.completed ? 'Mark Incomplete' : 'Complete';
  completeButton.addEventListener('click', () => toggleComplete(task.id, !task.completed));

  const deleteButton = document.createElement('button');
  deleteButton.type = 'button';
  deleteButton.className = 'delete-btn';
  deleteButton.textContent = 'Delete';
  deleteButton.addEventListener('click', () => removeTask(task.id));

  actions.appendChild(completeButton);
  actions.appendChild(deleteButton);
  titleRow.appendChild(title);
  titleRow.appendChild(actions);

  const description = document.createElement('p');
  description.className = 'task-description';
  description.textContent = task.description || 'No description provided.';

  const meta = document.createElement('p');
  meta.className = 'task-description';
  meta.textContent = `Created: ${new Date(task.created_at).toLocaleString()}`;

  item.appendChild(titleRow);
  item.appendChild(description);
  item.appendChild(meta);
  taskList.appendChild(item);
}

async function toggleComplete(taskId, completed) {
  try {
    await apiRequest(`tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify({ completed }),
    });
    loadTasks();
  } catch (error) {
    console.error(error);
  }
}

async function removeTask(taskId) {
  try {
    await apiRequest(`tasks/${taskId}`, {
      method: 'DELETE',
    });
    loadTasks();
  } catch (error) {
    console.error(error);
  }
}

checkSession();
