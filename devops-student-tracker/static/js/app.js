/**
 * DevOps Student Task Tracker - Client Interaction Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  const taskForm = document.getElementById("taskForm");
  const taskTitleInput = document.getElementById("taskTitle");
  const taskDescInput = document.getElementById("taskDesc");
  const taskCategorySelect = document.getElementById("taskCategory");
  const taskPrioritySelect = document.getElementById("taskPriority");
  const filterTabs = document.querySelectorAll(".filter-tab");
  const taskList = document.getElementById("taskList");
  const statTotal = document.getElementById("statTotal");
  const statCompleted = document.getElementById("statCompleted");
  const statPending = document.getElementById("statPending");
  const toastNotification = document.getElementById("toastNotification");

  let currentFilter = "all";

  // Show Toast
  function showToast(message, type = "success") {
    toastNotification.textContent = message;
    toastNotification.className = `toast ${type}`;
    setTimeout(() => {
      toastNotification.className = "toast hidden";
    }, 3500);
  }

  // Update Stats in UI
  function updateStats(stats) {
    if (!stats) return;
    if (statTotal) statTotal.textContent = stats.total;
    if (statCompleted) statCompleted.textContent = stats.completed;
    if (statPending) statPending.textContent = stats.pending;
  }

  // Filter tasks based on current filter tab
  function applyFilter() {
    const items = taskList.querySelectorAll(".task-item");
    let visibleCount = 0;

    items.forEach(item => {
      const status = item.getAttribute("data-status");
      if (currentFilter === "all" || currentFilter === status) {
        item.style.display = "flex";
        visibleCount++;
      } else {
        item.style.display = "none";
      }
    });

    const emptyState = document.getElementById("emptyState");
    if (visibleCount === 0 && items.length > 0) {
      if (!document.getElementById("filteredEmptyState")) {
        const div = document.createElement("div");
        div.id = "filteredEmptyState";
        div.className = "empty-state";
        div.innerHTML = `<div class="empty-icon">🔍</div><h3>No ${currentFilter} tasks</h3><p>Try switching to another filter tab.</p>`;
        taskList.appendChild(div);
      }
    } else {
      const filteredEmpty = document.getElementById("filteredEmptyState");
      if (filteredEmpty) filteredEmpty.remove();
    }
  }

  // Handle Filter Tab Clicks
  filterTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      filterTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentFilter = tab.getAttribute("data-filter");
      applyFilter();
    });
  });

  // Handle Task Form Submit
  if (taskForm) {
    taskForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const title = taskTitleInput.value.trim();
      const description = taskDescInput.value.trim();
      const category = taskCategorySelect.value;
      const priority = taskPrioritySelect.value;

      if (!title) {
        showToast("Please provide a task title", "error");
        return;
      }

      const submitBtn = document.getElementById("addTaskBtn");
      submitBtn.disabled = true;

      try {
        const response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, category, priority })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Failed to create task");
        }

        // Reset form
        taskTitleInput.value = "";
        taskDescInput.value = "";
        taskTitleInput.focus();

        // Update stats
        updateStats(data.stats);

        // Remove empty state if present
        const emptyState = document.getElementById("emptyState");
        if (emptyState) emptyState.remove();

        // Render new task in list
        renderTaskItem(data.task);
        applyFilter();
        showToast("Task added successfully!", "success");
      } catch (err) {
        showToast(err.message, "error");
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  // Render a task item
  function renderTaskItem(task) {
    const item = document.createElement("div");
    item.className = `task-item ${task.completed ? "is-completed" : ""}`;
    item.setAttribute("data-id", task.id);
    item.setAttribute("data-category", task.category);
    item.setAttribute("data-priority", task.priority);
    item.setAttribute("data-status", task.completed ? "completed" : "pending");

    item.innerHTML = `
      <div class="task-checkbox-wrap">
        <button class="task-checkbox ${task.completed ? "checked" : ""}" onclick="toggleTask(${task.id})" aria-label="Toggle task status">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </button>
      </div>
      <div class="task-body">
        <div class="task-title-row">
          <span class="task-title-text">${escapeHtml(task.title)}</span>
          <div class="task-tags">
            <span class="badge badge-category badge-${task.category.toLowerCase()}">${task.category}</span>
            <span class="badge badge-priority badge-${task.priority.toLowerCase()}">${task.priority}</span>
          </div>
        </div>
        ${task.description ? `<p class="task-desc-text">${escapeHtml(task.description)}</p>` : ""}
        <div class="task-meta">
          <span>Created: ${task.created_at}</span>
        </div>
      </div>
      <div class="task-actions">
        <button class="btn-icon delete-btn" onclick="deleteTask(${task.id})" title="Delete task" aria-label="Delete task">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            <line x1="10" y1="11" x2="10" y2="17"></line>
            <line x1="14" y1="11" x2="14" y2="17"></line>
          </svg>
        </button>
      </div>
    `;

    taskList.prepend(item);
  }

  // HTML escaping for safety
  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Global functions attached to window for inline onclicks
  window.toggleTask = async function(taskId) {
    try {
      const response = await fetch(`/api/tasks/${taskId}/toggle`, {
        method: "POST"
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to update task");

      const item = document.querySelector(`.task-item[data-id="${taskId}"]`);
      if (item) {
        const checkbox = item.querySelector(".task-checkbox");
        if (data.task.completed) {
          item.classList.add("is-completed");
          item.setAttribute("data-status", "completed");
          if (checkbox) checkbox.classList.add("checked");
        } else {
          item.classList.remove("is-completed");
          item.setAttribute("data-status", "pending");
          if (checkbox) checkbox.classList.remove("checked");
        }
      }

      updateStats(data.stats);
      applyFilter();
      showToast(data.task.completed ? "Task marked completed!" : "Task marked pending");
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  window.deleteTask = async function(taskId) {
    if (!confirm("Are you sure you want to delete this task?")) return;

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: "DELETE"
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to delete task");

      const item = document.querySelector(`.task-item[data-id="${taskId}"]`);
      if (item) {
        item.style.transform = "translateX(20px)";
        item.style.opacity = "0";
        setTimeout(() => {
          item.remove();
          // Check if no items left
          if (taskList.querySelectorAll(".task-item").length === 0) {
            taskList.innerHTML = `
              <div class="empty-state" id="emptyState">
                <div class="empty-icon">🎯</div>
                <h3>No tasks found</h3>
                <p>Add your first DevOps or Cloud Computing task above to get started!</p>
              </div>
            `;
          }
          applyFilter();
        }, 200);
      }

      updateStats(data.stats);
      showToast("Task deleted successfully", "success");
    } catch (err) {
      showToast(err.message, "error");
    }
  };
});
