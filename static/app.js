/**
 * EduTrack — Frontend Single Page Application Logic
 * Integrates directly with FastAPI CRUD endpoints and Ollama Ask-AI service.
 */

// Application State
const state = {
  students: [],
  courses: new Set(),
  activeCourse: '',
  searchQuery: '',
  currentView: 'table', // 'table' or 'grid'
  editingStudentId: null, // null for new, string for edit
  deletingStudentId: null,
  ollamaReady: false,
};

// DOM Elements
const elements = {
  // Navigation & Badges
  apiStatusDot: document.querySelector('#apiStatusBadge .status-dot'),
  apiStatusText: document.getElementById('apiStatusText'),
  aiStatusDot: document.getElementById('aiStatusDot'),
  aiStatusText: document.getElementById('aiStatusText'),
  openAiDrawerBtn: document.getElementById('openAiDrawerBtn'),
  openAddStudentModalBtn: document.getElementById('openAddStudentModalBtn'),

  // Metrics
  metricTotalStudents: document.getElementById('metricTotalStudents'),
  metricTotalCourses: document.getElementById('metricTotalCourses'),
  metricRecentAdmissions: document.getElementById('metricRecentAdmissions'),
  metricAiStatus: document.getElementById('metricAiStatus'),
  aiMetricCard: document.getElementById('aiMetricCard'),

  // Controls
  searchInput: document.getElementById('searchInput'),
  clearSearchBtn: document.getElementById('clearSearchBtn'),
  courseFilter: document.getElementById('courseFilter'),
  tableViewBtn: document.getElementById('tableViewBtn'),
  gridViewBtn: document.getElementById('gridViewBtn'),
  refreshDataBtn: document.getElementById('refreshDataBtn'),

  // Views & Containers
  tableViewContainer: document.getElementById('tableViewContainer'),
  gridViewContainer: document.getElementById('gridViewContainer'),
  studentsTableBody: document.getElementById('studentsTableBody'),
  emptyState: document.getElementById('emptyState'),
  emptyAddBtn: document.getElementById('emptyAddBtn'),

  // Add/Edit Modal
  studentModal: document.getElementById('studentModal'),
  modalTitle: document.getElementById('modalTitle'),
  modalSubtitle: document.getElementById('modalSubtitle'),
  closeModalBtn: document.getElementById('closeModalBtn'),
  cancelModalBtn: document.getElementById('cancelModalBtn'),
  studentForm: document.getElementById('studentForm'),
  modalErrorAlert: document.getElementById('modalErrorAlert'),
  saveStudentBtn: document.getElementById('saveStudentBtn'),
  saveBtnText: document.getElementById('saveBtnText'),
  saveBtnSpinner: document.getElementById('saveBtnSpinner'),

  // Form Fields
  editOriginalId: document.getElementById('editOriginalId'),
  formStudentId: document.getElementById('formStudentId'),
  formName: document.getElementById('formName'),
  formEmail: document.getElementById('formEmail'),
  formDob: document.getElementById('formDob'),
  formPhone: document.getElementById('formPhone'),
  formCourse: document.getElementById('formCourse'),
  formEnrollmentDate: document.getElementById('formEnrollmentDate'),
  formAddress: document.getElementById('formAddress'),

  // Delete Modal
  deleteModal: document.getElementById('deleteModal'),
  deleteModalPrompt: document.getElementById('deleteModalPrompt'),
  closeDeleteModalBtn: document.getElementById('closeDeleteModalBtn'),
  cancelDeleteBtn: document.getElementById('cancelDeleteBtn'),
  confirmDeleteBtn: document.getElementById('confirmDeleteBtn'),
  confirmDeleteText: document.getElementById('confirmDeleteText'),
  deleteBtnSpinner: document.getElementById('deleteBtnSpinner'),

  // AI Drawer
  aiDrawer: document.getElementById('aiDrawer'),
  closeAiDrawerBtn: document.getElementById('closeAiDrawerBtn'),
  drawerAiDot: document.getElementById('drawerAiDot'),
  drawerAiStatusText: document.getElementById('drawerAiStatusText'),
  aiChatMessages: document.getElementById('aiChatMessages'),
  aiChatForm: document.getElementById('aiChatForm'),
  aiQuestionInput: document.getElementById('aiQuestionInput'),
  sendAiBtn: document.getElementById('sendAiBtn'),

  // Toast Container
  toastContainer: document.getElementById('toastContainer'),
};

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadStudents();
  checkOllamaStatus();

  // Poll Ollama status every 8 seconds if not yet ready
  setInterval(() => {
    if (!state.ollamaReady) {
      checkOllamaStatus();
    }
  }, 8000);
});

// ==========================================================================
// Event Listeners
// ==========================================================================
function setupEventListeners() {
  // Search input with debounce
  let debounceTimer;
  elements.searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const query = e.target.value.trim();
    elements.clearSearchBtn.style.display = query ? 'block' : 'none';
    debounceTimer = setTimeout(() => {
      state.searchQuery = query;
      loadStudents();
    }, 300);
  });

  elements.clearSearchBtn.addEventListener('click', () => {
    elements.searchInput.value = '';
    elements.clearSearchBtn.style.display = 'none';
    state.searchQuery = '';
    loadStudents();
  });

  // Course Filter
  elements.courseFilter.addEventListener('change', (e) => {
    state.activeCourse = e.target.value;
    loadStudents();
  });

  // Refresh
  elements.refreshDataBtn.addEventListener('click', () => {
    loadStudents();
    checkOllamaStatus();
    showToast('Data refreshed', 'info');
  });

  // View Toggle
  elements.tableViewBtn.addEventListener('click', () => setView('table'));
  elements.gridViewBtn.addEventListener('click', () => setView('grid'));

  // Modals
  elements.openAddStudentModalBtn.addEventListener('click', () => openStudentModal());
  elements.emptyAddBtn.addEventListener('click', () => openStudentModal());
  elements.closeModalBtn.addEventListener('click', closeStudentModal);
  elements.cancelModalBtn.addEventListener('click', closeStudentModal);
  elements.studentForm.addEventListener('submit', handleStudentFormSubmit);

  // Delete Modal
  elements.closeDeleteModalBtn.addEventListener('click', closeDeleteModal);
  elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
  elements.confirmDeleteBtn.addEventListener('click', handleConfirmDelete);

  // AI Drawer
  elements.openAiDrawerBtn.addEventListener('click', openAiDrawer);
  elements.aiMetricCard.addEventListener('click', openAiDrawer);
  elements.closeAiDrawerBtn.addEventListener('click', closeAiDrawer);
  elements.aiChatForm.addEventListener('submit', handleAiChatSubmit);

  // AI Prompt Chips delegation
  elements.aiChatMessages.addEventListener('click', (e) => {
    if (e.target.classList.contains('chip')) {
      const promptText = e.target.dataset.prompt;
      if (promptText) {
        elements.aiQuestionInput.value = promptText;
        elements.aiChatForm.dispatchEvent(new Event('submit'));
      }
    }
  });

  // Close modals on escape key or clicking backdrop
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeStudentModal();
      closeDeleteModal();
      closeAiDrawer();
    }
  });

  elements.studentModal.addEventListener('click', (e) => {
    if (e.target === elements.studentModal) closeStudentModal();
  });

  elements.deleteModal.addEventListener('click', (e) => {
    if (e.target === elements.deleteModal) closeDeleteModal();
  });

  elements.aiDrawer.addEventListener('click', (e) => {
    if (e.target === elements.aiDrawer) closeAiDrawer();
  });
}

// ==========================================================================
// API Operations: Students CRUD
// ==========================================================================
async function loadStudents() {
  try {
    const params = new URLSearchParams();
    if (state.activeCourse) params.append('course', state.activeCourse);
    if (state.searchQuery) params.append('name', state.searchQuery);

    const url = `/students${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);

    if (!response.ok) throw new Error('Failed to fetch students list');

    const data = await response.json();
    state.students = data;

    // Extract unique courses for dropdown filter if not already populated
    if (!state.activeCourse && !state.searchQuery) {
      updateCoursesDropdown(data);
    }

    updateMetrics(data);
    renderStudents(data);
  } catch (error) {
    console.error('Error loading students:', error);
    showToast('Could not load student records from server', 'error');
  }
}

function updateCoursesDropdown(studentsList) {
  const currentSelected = elements.courseFilter.value;
  const courses = new Set();
  studentsList.forEach(s => {
    if (s.course && s.course.trim()) courses.add(s.course.trim());
  });

  elements.courseFilter.innerHTML = '<option value="">All Courses</option>';
  Array.from(courses).sort().forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    elements.courseFilter.appendChild(opt);
  });
  elements.courseFilter.value = currentSelected;
}

function updateMetrics(studentsList) {
  elements.metricTotalStudents.textContent = studentsList.length;

  const courses = new Set(studentsList.map(s => s.course).filter(Boolean));
  elements.metricTotalCourses.textContent = courses.size;

  const currentYear = new Date().getFullYear();
  const recent = studentsList.filter(s => {
    if (!s.enrollment_date) return false;
    return new Date(s.enrollment_date).getFullYear() >= currentYear - 1;
  });
  elements.metricRecentAdmissions.textContent = recent.length;
}

function renderStudents(studentsList) {
  if (studentsList.length === 0) {
    elements.tableViewContainer.style.display = 'none';
    elements.gridViewContainer.style.display = 'none';
    elements.emptyState.style.display = 'block';
    return;
  }

  elements.emptyState.style.display = 'none';

  if (state.currentView === 'table') {
    elements.tableViewContainer.style.display = 'block';
    elements.gridViewContainer.style.display = 'none';
    renderTableRows(studentsList);
  } else {
    elements.tableViewContainer.style.display = 'none';
    elements.gridViewContainer.style.display = 'grid';
    renderCards(studentsList);
  }
}

function renderTableRows(studentsList) {
  elements.studentsTableBody.innerHTML = '';
  studentsList.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="student-id-tag">${escapeHtml(s.student_id)}</span></td>
      <td class="student-name-cell">${escapeHtml(s.name)}</td>
      <td>${s.course ? `<span class="course-badge">${escapeHtml(s.course)}</span>` : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${escapeHtml(s.email)}</td>
      <td>${escapeHtml(s.dob || '—')}</td>
      <td>${escapeHtml(s.phone || '—')}</td>
      <td>${escapeHtml(s.enrollment_date || '—')}</td>
      <td class="text-right">
        <div class="table-actions">
          <button class="action-btn edit" title="Edit student" onclick="handleEditClick('${s.student_id}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="action-btn delete" title="Delete student" onclick="handleDeleteClick('${s.student_id}', '${escapeHtml(s.name)}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </td>
    `;
    elements.studentsTableBody.appendChild(tr);
  });
}

function renderCards(studentsList) {
  elements.gridViewContainer.innerHTML = '';
  studentsList.forEach(s => {
    const card = document.createElement('div');
    card.className = 'student-card';
    card.innerHTML = `
      <div>
        <div class="student-card-header">
          <span class="student-id-tag">${escapeHtml(s.student_id)}</span>
          ${s.course ? `<span class="course-badge">${escapeHtml(s.course)}</span>` : ''}
        </div>
        <h4 class="card-title">${escapeHtml(s.name)}</h4>
      </div>

      <div class="card-details">
        <div class="card-detail-item">
          <span>✉️</span>
          <span>${escapeHtml(s.email)}</span>
        </div>
        <div class="card-detail-item">
          <span>🎂</span>
          <span>DOB: ${escapeHtml(s.dob || '—')}</span>
        </div>
        ${s.phone ? `
          <div class="card-detail-item">
            <span>📞</span>
            <span>${escapeHtml(s.phone)}</span>
          </div>` : ''
        }
        <div class="card-detail-item">
          <span>📅</span>
          <span>Enrolled: ${escapeHtml(s.enrollment_date || '—')}</span>
        </div>
      </div>

      <div class="card-footer">
        <span style="font-size:0.75rem; color:var(--text-muted);">PK ID #${s.id}</span>
        <div class="table-actions">
          <button class="action-btn edit" title="Edit student" onclick="handleEditClick('${s.student_id}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button class="action-btn delete" title="Delete student" onclick="handleDeleteClick('${s.student_id}', '${escapeHtml(s.name)}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
    `;
    elements.gridViewContainer.appendChild(card);
  });
}

function setView(view) {
  state.currentView = view;
  elements.tableViewBtn.classList.toggle('active', view === 'table');
  elements.gridViewBtn.classList.toggle('active', view === 'grid');
  renderStudents(state.students);
}

// ==========================================================================
// Add / Edit Modal Logic
// ==========================================================================
function openStudentModal(student = null) {
  state.editingStudentId = student ? student.student_id : null;
  elements.modalErrorAlert.style.display = 'none';
  elements.studentForm.reset();

  if (student) {
    elements.modalTitle.textContent = 'Edit Student Profile';
    elements.modalSubtitle.textContent = `Update details for student ${student.student_id}.`;
    elements.saveBtnText.textContent = 'Save Changes';

    elements.editOriginalId.value = student.student_id;
    elements.formStudentId.value = student.student_id;
    elements.formName.value = student.name;
    elements.formEmail.value = student.email;
    elements.formDob.value = student.dob || '';
    elements.formPhone.value = student.phone || '';
    elements.formCourse.value = student.course || '';
    elements.formEnrollmentDate.value = student.enrollment_date || '';
    elements.formAddress.value = student.address || '';
  } else {
    elements.modalTitle.textContent = 'Add New Student';
    elements.modalSubtitle.textContent = 'Fill in student details. Duplicate IDs and emails are validated.';
    elements.saveBtnText.textContent = 'Create Student';

    elements.editOriginalId.value = '';
    // Auto populate today's date for enrollment
    elements.formEnrollmentDate.value = new Date().toISOString().split('T')[0];
  }

  elements.studentModal.style.display = 'flex';
  elements.formStudentId.focus();
}

function closeStudentModal() {
  elements.studentModal.style.display = 'none';
  elements.modalErrorAlert.style.display = 'none';
}

async function handleStudentFormSubmit(e) {
  e.preventDefault();
  elements.modalErrorAlert.style.display = 'none';

  const payload = {
    student_id: elements.formStudentId.value.trim(),
    name: elements.formName.value.trim(),
    email: elements.formEmail.value.trim(),
    dob: elements.formDob.value,
    phone: elements.formPhone.value.trim() || null,
    course: elements.formCourse.value.trim() || null,
    enrollment_date: elements.formEnrollmentDate.value || null,
    address: elements.formAddress.value.trim() || null,
  };

  // UI loading state
  elements.saveBtnText.style.display = 'none';
  elements.saveBtnSpinner.style.display = 'inline-block';
  elements.saveStudentBtn.disabled = true;

  try {
    const isEdit = Boolean(state.editingStudentId);
    const url = isEdit ? `/students/${encodeURIComponent(state.editingStudentId)}` : '/students';
    const method = isEdit ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (!response.ok) {
      // Show 400 Bad Request or validation errors
      const errorMsg = result.detail || 'An error occurred while saving the record.';
      elements.modalErrorAlert.textContent = typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg);
      elements.modalErrorAlert.style.display = 'block';
      return;
    }

    closeStudentModal();
    showToast(isEdit ? `Student ${payload.student_id} updated!` : `Student ${payload.student_id} created successfully!`, 'success');
    loadStudents();
  } catch (err) {
    elements.modalErrorAlert.textContent = 'Server connection failed. Please check if backend is running.';
    elements.modalErrorAlert.style.display = 'block';
  } finally {
    elements.saveBtnText.style.display = 'inline';
    elements.saveBtnSpinner.style.display = 'none';
    elements.saveStudentBtn.disabled = false;
  }
}

// Global hook for row/card edit button
window.handleEditClick = function(studentId) {
  const student = state.students.find(s => s.student_id === studentId);
  if (student) {
    openStudentModal(student);
  }
};

// ==========================================================================
// Delete Modal Logic
// ==========================================================================
window.handleDeleteClick = function(studentId, studentName) {
  state.deletingStudentId = studentId;
  elements.deleteModalPrompt.innerHTML = `Are you sure you want to permanently delete <strong>${escapeHtml(studentName)}</strong> (${escapeHtml(studentId)})?`;
  elements.deleteModal.style.display = 'flex';
};

function closeDeleteModal() {
  elements.deleteModal.style.display = 'none';
  state.deletingStudentId = null;
}

async function handleConfirmDelete() {
  if (!state.deletingStudentId) return;

  elements.confirmDeleteText.style.display = 'none';
  elements.deleteBtnSpinner.style.display = 'inline-block';
  elements.confirmDeleteBtn.disabled = true;

  try {
    const response = await fetch(`/students/${encodeURIComponent(state.deletingStudentId)}`, {
      method: 'DELETE',
    });

    if (response.status === 204 || response.ok) {
      showToast(`Student ${state.deletingStudentId} deleted successfully.`, 'success');
      closeDeleteModal();
      loadStudents();
    } else {
      const err = await response.json();
      showToast(err.detail || 'Could not delete record.', 'error');
    }
  } catch (error) {
    showToast('Failed to communicate with server.', 'error');
  } finally {
    elements.confirmDeleteText.style.display = 'inline';
    elements.deleteBtnSpinner.style.display = 'none';
    elements.confirmDeleteBtn.disabled = false;
  }
}

// ==========================================================================
// Ollama AI Assistant Logic
// ==========================================================================
async function checkOllamaStatus() {
  try {
    const res = await fetch('/ask-ai/status');
    if (!res.ok) throw new Error('API error');
    const data = await res.json();

    state.ollamaReady = data.ollama_available;

    if (data.ollama_available) {
      elements.aiStatusDot.className = 'status-dot green';
      elements.aiStatusText.textContent = 'Ollama Ready';
      elements.drawerAiDot.className = 'status-dot green';
      elements.drawerAiStatusText.textContent = `Ollama Online (${data.default_model})`;
      elements.metricAiStatus.textContent = 'Active (Ready)';
    } else {
      elements.aiStatusDot.className = 'status-dot amber';
      elements.aiStatusText.textContent = 'Ollama Loading...';
      elements.drawerAiDot.className = 'status-dot amber';
      elements.drawerAiStatusText.textContent = 'Ollama model is loading / downloading...';
      elements.metricAiStatus.textContent = 'Connecting...';
    }
  } catch (e) {
    elements.aiStatusDot.className = 'status-dot red';
    elements.aiStatusText.textContent = 'AI Offline';
  }
}

function openAiDrawer() {
  elements.aiDrawer.style.display = 'flex';
  elements.aiQuestionInput.focus();
}

function closeAiDrawer() {
  elements.aiDrawer.style.display = 'none';
}

async function handleAiChatSubmit(e) {
  e.preventDefault();
  const question = elements.aiQuestionInput.value.trim();
  if (!question) return;

  // Append user message
  appendChatMessage(question, 'user');
  elements.aiQuestionInput.value = '';

  // Show typing indicator
  const typingIndicator = appendTypingIndicator();
  elements.sendAiBtn.disabled = true;

  try {
    const response = await fetch('/ask-ai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();
    removeTypingIndicator(typingIndicator);

    if (response.ok) {
      appendChatMessage(data.answer, 'bot', {
        records: data.records_analyzed,
        model: data.model,
      });
    } else {
      const errMsg = data.detail || 'Could not fetch response from Ollama.';
      appendChatMessage(`⚠️ ${errMsg}`, 'bot');
    }
  } catch (err) {
    removeTypingIndicator(typingIndicator);
    appendChatMessage('⚠️ Network error connecting to AI backend. Please verify your connection.', 'bot');
  } finally {
    elements.sendAiBtn.disabled = false;
  }
}

function appendChatMessage(text, sender, meta = null) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${sender}`;

  if (sender === 'bot') {
    msgDiv.innerHTML = `
      <div class="bot-avatar">🤖</div>
      <div class="message-bubble">
        <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
        ${meta ? `<span class="message-meta">Grounded on ${meta.records} records via ${meta.model}</span>` : ''}
      </div>
    `;
  } else {
    msgDiv.innerHTML = `
      <div class="message-bubble">
        <p>${escapeHtml(text)}</p>
      </div>
    `;
  }

  elements.aiChatMessages.appendChild(msgDiv);
  elements.aiChatMessages.scrollTop = elements.aiChatMessages.scrollHeight;
}

function appendTypingIndicator() {
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-message bot typing';
  typingDiv.innerHTML = `
    <div class="bot-avatar">🤖</div>
    <div class="message-bubble">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  elements.aiChatMessages.appendChild(typingDiv);
  elements.aiChatMessages.scrollTop = elements.aiChatMessages.scrollHeight;
  return typingDiv;
}

function removeTypingIndicator(typingElement) {
  if (typingElement && typingElement.parentNode) {
    typingElement.parentNode.removeChild(typingElement);
  }
}

// ==========================================================================
// Toast Notifications
// ==========================================================================
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${escapeHtml(message)}</span>`;

  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 4000);
}

// Utility: HTML Escaping
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
