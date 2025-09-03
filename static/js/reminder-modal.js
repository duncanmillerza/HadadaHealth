function openReminderModal(reminder = null) {
  const form = document.getElementById("reminder-form");
  form.reset();

  document.getElementById("reminder-modal-title").textContent = reminder ? "Edit Reminder" : "Add Reminder";
  form.dataset.editing = reminder ? "true" : "false";
  form.dataset.reminderId = reminder?.id || "";

  if (reminder) {
    form.title.value = reminder.title || "";
    form.description.value = reminder.description || "";
    form.due_date.value = reminder.due_date?.split("T")[0] || "";
    form.colour.value = reminder.colour || "#2D6356";
    form.priority.value = reminder.priority || "normal";
    form.visibility.value = reminder.visibility || "private";
    form.notify.checked = !!reminder.notify;
    form.notify_at.value = reminder.notify_at || "";
  }
  const modalContent = document.querySelector("#reminder-modal .modal-content");
  if (modalContent) {
    modalContent.style.maxWidth = "500px";
    modalContent.style.margin = "5vh auto";
    modalContent.style.background = "white";
    modalContent.style.padding = "2em";
    modalContent.style.borderRadius = "8px";
    modalContent.style.boxShadow = "0 4px 8px rgba(0,0,0,0.2)";
    modalContent.style.maxHeight = "90vh";
    modalContent.style.overflowY = "auto";
  }
  document.getElementById("reminder-modal").style.display = "block";
}

function closeReminderModal() {
  document.getElementById("reminder-modal").style.display = "none";
}

function initReminderModal() {
  const form = document.getElementById("reminder-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const isEditing = form.dataset.editing === "true";
    const reminderId = form.dataset.reminderId;

    const data = {
      title: form.title.value,
      description: form.description.value,
      due_date: form.due_date.value,
      colour: form.colour.value,
      priority: form.priority.value,
      visibility: form.visibility.value,
      notify: form.notify.checked ? 1 : 0,
      notify_at: form.notify_at.value
    };

    const url = isEditing ? `/reminders/${reminderId}` : "/reminders";
    const method = isEditing ? "PUT" : "POST";

    try {
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        alert("Reminder saved!");
        closeReminderModal();
        if (typeof populateReminders === "function") {
          populateReminders();
        }
      } else {
        const err = await res.json();
        alert("Error: " + err.detail);
      }
    } catch (err) {
      alert("Failed to save reminder.");
      console.error(err);
    }
  });
}

function openReminderViewModal(reminder) {
  const titleEl = document.getElementById("reminder-view-title");
  titleEl.textContent = reminder.title || "Reminder";
  titleEl.style.textAlign = "center";
  titleEl.style.fontSize = "2rem";
  titleEl.style.padding = "0.75rem 1rem";
  titleEl.style.color = "white";
  titleEl.style.backgroundColor = reminder.colour || "#2D6356";
  titleEl.style.borderRadius = "8px";

  const fields = [
    ["reminder-view-description", reminder.description],
    ["reminder-view-due-date", reminder.due_date],
    ["reminder-view-recurrence", reminder.recurrence || "None"],
    ["reminder-view-completed", reminder.completed ? "Yes" : "No"],
    ["reminder-view-completed-at", reminder.completed_at],
    ["reminder-view-priority", reminder.priority],
    ["reminder-view-visibility", reminder.visibility],
    ["reminder-view-notify", reminder.notify ? "Yes" : "No"],
    ["reminder-view-notify-at", reminder.notify_at],
    ["reminder-view-patient-id", reminder.patient_id],
    ["reminder-view-therapist-id", reminder.therapist_id],
    ["reminder-view-appointment-id", reminder.appointment_id],
    ["reminder-view-created-by", reminder.created_by_user_id],
    ["reminder-view-created-at", reminder.timestamp],
  ];

  fields.forEach(([id, value]) => {
    const el = document.getElementById(id);
    const p = el?.closest("p");
    if (value == null || value === "") {
      if (p) p.style.display = "none";
    } else {
      if (el) el.textContent = value;
      if (p) p.style.display = "";
    }
  });

  const colourBox = document.getElementById("reminder-view-colour-box");
  if (colourBox) colourBox.style.backgroundColor = reminder.colour || "#2D6356";

  const modalViewContent = document.querySelector("#reminder-view-modal .modal-content");
  if (modalViewContent) {
    modalViewContent.style.maxWidth = "500px";
    modalViewContent.style.margin = "5vh auto";
    modalViewContent.style.background = "white";
    modalViewContent.style.padding = "2em";
    modalViewContent.style.borderRadius = "8px";
    modalViewContent.style.boxShadow = "0 4px 8px rgba(0,0,0,0.2)";
    modalViewContent.style.maxHeight = "90vh";
    modalViewContent.style.overflowY = "auto";
  }

  document.getElementById("reminder-view-modal").style.display = "block";
}

function closeReminderViewModal() {
  document.getElementById("reminder-view-modal").style.display = "none";
}