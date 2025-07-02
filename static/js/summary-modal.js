

// Load summary modal fragment
document.addEventListener("DOMContentLoaded", () => {
  fetch("/static/fragments/appointment_summary_modal.html")
    .then(res => res.text())
    .then(html => {
      const container = document.createElement('div');
      container.innerHTML = html;
      document.body.appendChild(container);
    })
    .catch(err => console.error("Failed to load appointment summary modal:", err));
});

// Open the summary modal with booking details
function openSummaryModal(booking) {
  console.log("openSummaryModal called with booking:", booking);
  document.getElementById("summary-modal").dataset.bookingId = booking.id;
  document.getElementById("summary-modal").dataset.patientId = booking.patient_id || "";
  const modal = document.getElementById("summary-modal");
  // Ensure booking.date is a Date object
  const dateObj = booking.date instanceof Date ? booking.date : new Date(booking.date);
  modal.classList.toggle("wide", booking.hasTreatmentNote);

  // Build summary content
  const content = `
    <strong>Patient:</strong> ${booking.name} &nbsp;
    <strong>Therapist:</strong> ${booking.therapist}<br>
    <strong>Date:</strong> ${dateObj.toLocaleDateString()} &nbsp;
    <strong>Time:</strong> ${booking.time} &nbsp;
    <strong>Duration:</strong> ${booking.duration} mins<br>
    <strong>Notes:</strong> ${booking.notes || "None"}
  `;
  document.getElementById("summary-content").innerHTML = content;

  // Load treatment notes only if present
  const noteDiv = document.getElementById("note-details");
  if (!booking.has_note) {
    // Hide notes section when no treatment note exists
    noteDiv.style.display = 'none';
  } else {
    noteDiv.style.display = '';
    noteDiv.innerHTML = "Loading notes...";
    fetch(`/api/treatment-notes/full/${booking.id}`)
      .then(res => res.json())
      .then(data => {
        let html = "";
        if (data.treatment) {
          html += `<strong>Subjective:</strong> ${data.treatment.subjective_findings || "None"}<br>`;
          html += `<strong>Objective:</strong> ${data.treatment.objective_findings || "None"}<br>`;
          html += `<strong>Treatment:</strong> ${data.treatment.treatment || "None"}<br>`;
          html += `<strong>Plan:</strong> ${data.treatment.plan || "None"}<br>`;
        }
        if (data.billing && data.billing.length) {
          const codes = data.billing.map(e => e.code).join(", ");
          html += `<strong>Billed Codes:</strong> ${codes}<br>`;
        }
        if (data.supplementary && data.supplementary.length) {
          html += `<hr><strong>Supplementary Notes:</strong><ul>`;
          data.supplementary.forEach(n => {
            const date = new Date(n.timestamp).toLocaleString();
            html += `<li><em>${date}</em>: ${n.note}</li>`;
          });
          html += `</ul>`;
        }
        noteDiv.innerHTML = html;
      })
      .catch(err => {
        noteDiv.innerHTML = "<em>Error loading notes.</em>";
        console.error(err);
      });
  }

  // Adjust action buttons
  const sessionBtn = document.querySelector('#summary-modal .summary-actions button[onclick="goToSession()"]');
  if (sessionBtn) {
    sessionBtn.textContent = booking.hasTreatmentNote ? "Add Supplementary Note" : "Session";
    sessionBtn.style.display = "inline-block";
  }
  const editBtn = document.querySelector('#summary-modal .summary-actions button[onclick="editFromSummary()"]');
  if (editBtn) {
    editBtn.style.display = booking.hasTreatmentNote ? "none" : "inline-block";
  }

  modal.style.display = "block";
}
window.openSummaryModal = openSummaryModal;

function closeSummaryModal() {
  document.getElementById("summary-modal").style.display = "none";
}
window.closeSummaryModal = closeSummaryModal;

function goToPatientProfileFromSummary() {
  const patientId = document.getElementById("summary-modal").dataset.patientId;
  if (!patientId || isNaN(patientId)) {
    // Fallback for MDT calendar where patientId isn't provided
    if (typeof goToProfile === 'function') {
      goToProfile();
    } else {
      alert("No valid patient ID available.");
    }
    return;
  }
  window.location.href = `/patient-profile-page?id=${patientId}`;
}
window.goToPatientProfileFromSummary = goToPatientProfileFromSummary;

function goToSession() {
  const bookingId = document.getElementById("summary-modal").dataset.bookingId;
  const booking = (typeof bookings !== 'undefined') 
    ? bookings.find(b => String(b.id) === bookingId) 
    : null;
  if (!booking) {
    console.error("Supplementary note: booking not found for ID", bookingId);
    return;
  }
  if (booking.hasTreatmentNote) {
    const note = prompt("Enter supplementary note:");
    if (note && note.trim()) {
      fetch(`/api/treatment-notes/${bookingId}/supplementary_note`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note })
      }).then(res => {
        if (!res.ok) throw new Error("Failed to save supplementary note");
        alert("Supplementary note added.");
        closeSummaryModal();
      }).catch(err => alert("Error: " + err.message));
    }
  } else {
    window.location.href = `/treatment-notes-page?booking_id=${bookingId}`;
  }
}
window.goToSession = goToSession;

function editFromSummary() {
  const bookingId = document.getElementById("summary-modal").dataset.bookingId;
  const booking = window.bookings && bookings.find(b => b.id === bookingId);
  if (booking) {
    const cell = document.querySelector(`[data-day="${booking.day}"][data-time="${booking.time}"]`);
    closeSummaryModal();
    window.openModal(cell, booking);
  }
}

window.editFromSummary = editFromSummary;

function deleteFromSummary() {
  // Extract booking ID and store it on cancel modal
  const bookingId = document.getElementById("summary-modal").dataset.bookingId;
  const cancelModal = document.getElementById("cancel-modal");
  cancelModal.dataset.bookingId = bookingId;

  // Close the summary modal and open the cancel modal
  closeSummaryModal();
  cancelModal.style.display = "block";
}
window.deleteFromSummary = deleteFromSummary;

function cancelFromSummary() {
  const bookingId = document.getElementById("summary-modal").dataset.bookingId;
  window.contextTarget = document.getElementById(bookingId);
  closeSummaryModal();
  document.getElementById("cancel-modal").style.display = "block";
}
window.cancelFromSummary = cancelFromSummary;

async function confirmCancellation() {
  const reason = document.getElementById("cancel-reason").value.trim();
  if (!reason) return alert("Please enter a reason.");
  const cancelModal = document.getElementById("cancel-modal");
  const bookingId = cancelModal.dataset.bookingId;
  try {
    const response = await fetch(`/bookings/${bookingId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Delete failed');
    // Refresh calendar view
    if (typeof fetchBookings === 'function') {
      fetchBookings();
    } else if (typeof renderBookings === 'function') {
      renderBookings();
    }
  } catch (err) {
    alert('Error deleting appointment: ' + err.message);
  }
  closeCancelModal();
}
window.confirmCancellation = confirmCancellation;

function closeCancelModal() {
  document.getElementById("cancel-modal").style.display = "none";
  document.getElementById("cancel-reason").value = "";
}
window.closeCancelModal = closeCancelModal;