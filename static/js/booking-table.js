// Sorting logic for booking table
let sortDirection = 1;
let lastSortedColumn = null;

function sortBookingsTable(columnIndex) {
  const table = document.querySelector(".booking-table");
  const tbody = table.querySelector("tbody");
  const headers = table.querySelectorAll("th");
  const rows = Array.from(tbody.querySelectorAll("tr"));

  // Reset all headers and remove arrows
  headers.forEach((th, i) => {
    th.textContent = th.textContent.replace(/[\u25B2\u25BC]/g, "").trim();
    // Arrow will be added to sorted column below
  });

  // Toggle direction
  if (lastSortedColumn === columnIndex) {
    sortDirection *= -1;
  } else {
    sortDirection = 1;
    lastSortedColumn = columnIndex;
  }

  // Add arrow to sorted column
  headers.forEach((th, i) => {
    if (i === columnIndex) {
      th.textContent += sortDirection === 1 ? " ▲" : " ▼";
    }
  });

  // Sort
  const sortedRows = rows.slice().sort((a, b) => {
    const aText = a.children[columnIndex].textContent.trim().toLowerCase();
    const bText = b.children[columnIndex].textContent.trim().toLowerCase();
    return aText.localeCompare(bText) * sortDirection;
  });

  sortedRows.forEach(row => tbody.appendChild(row));
}
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("booking-modal");
    const backdrop = document.getElementById("booking-modal-backdrop");
    const closeBtn = document.getElementById("close-booking-modal");
    const form = document.getElementById("booking-form");
    // Wire up close button for the view bookings modal
    const closeBookingsBtn = document.getElementById("close-bookings-modal");
    if (closeBookingsBtn) {
      closeBookingsBtn.addEventListener("click", () => {
        const modal = document.getElementById("booking-modal");
        const backdrop = document.getElementById("booking-modal-backdrop");
        if (modal) modal.style.display = "none";
        if (backdrop) backdrop.style.display = "none";
      });
    }
  
    window.openBookingModal = function (bookingData = {}) {
      document.getElementById("booking-id").value = bookingData.id || "";
      document.getElementById("booking-name").value = bookingData.name || "";
      document.getElementById("booking-date").value = bookingData.date || "";
      document.getElementById("booking-time").value = bookingData.time || "";
      document.getElementById("booking-duration").value = bookingData.duration || 15;
      document.getElementById("booking-notes").value = bookingData.notes || "";

      const therapistSelect = document.getElementById("booking-therapist");
      therapistSelect.innerHTML = ""; // Clear before refill
      (window.allTherapists || []).forEach(therapist => {
        const option = document.createElement("option");
        option.value = therapist.id;
        option.textContent = therapist.name;
        if (bookingData.therapist_id == therapist.id) option.selected = true;
        therapistSelect.appendChild(option);
      });

      modal.style.display = "block";
      backdrop.style.display = "block";

      // Open patient modal if bookingData.patient is provided
      if (bookingData.patient) {
        if (typeof openPatientModal === "function") {
          openPatientModal(bookingData.patient);
        } else {
          console.warn("openPatientModal is not defined.");
        }
      }
    };
  
    function closeBookingModal() {
      modal.style.display = "none";
      backdrop.style.display = "none";
    }
  
    if (closeBtn) closeBtn.addEventListener("click", closeBookingModal);
    if (backdrop) backdrop.addEventListener("click", closeBookingModal);
    if (form) form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const booking = {
        id: document.getElementById("booking-id").value,
        name: document.getElementById("booking-name").value,
        date: document.getElementById("booking-date").value,
        time: document.getElementById("booking-time").value || document.getElementById("start-time").value,
        duration: parseInt(document.getElementById("booking-duration").value),
        therapist_id: document.getElementById("booking-therapist").value,
        notes: document.getElementById("booking-notes").value,
        appointment_type_id: document.getElementById("appointment-type-id")?.value || null,
        appointment_type_color: document.getElementById("appointment-type-color")?.value || null
      };
  
      // Post or patch booking here
      await fetch(`/api/bookings${booking.id ? '/' + booking.id : ''}`, {
        method: booking.id ? "PATCH" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(booking)
      });
  
      closeBookingModal();
      location.reload(); // Or refetch bookings instead of full reload
    });
  });

  window.openBookingsModal = async function(patientId) {
    const modal = document.getElementById("booking-modal");
    const backdrop = document.getElementById("booking-modal-backdrop");
    const tableBody = document.getElementById("booking-table-body");
    if (!tableBody) {
      console.error("Missing table body element for booking table");
      return;
    }
    tableBody.innerHTML = "";

    try {
      const response = await fetch(`/api/patient/${patientId}/bookings`);
      if (!response.ok) throw new Error("Failed to fetch bookings");
      const bookings = await response.json();

      bookings.forEach(b => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td style="padding: 0.75rem;">${b.date}</td>
          <td style="padding: 0.75rem;">${b.time}</td>
          <td style="padding: 0.75rem;">${b.profession || '-'}</td>
          <td style="padding: 0.75rem;">${b.therapist_name || '-'}</td>
          <td style="padding: 0.75rem;">${b.billing_completed ? "✅" : "❌"}</td>
          <td style="padding: 0.75rem;">${b.notes_completed ? "✅" : "❌"}</td>
        `;
        tableBody.appendChild(row);
      });

      modal.style.display = "block";
      backdrop.style.display = "block";
    } catch (err) {
      console.error("Failed to load bookings:", err);
      tableBody.innerHTML = `<tr><td colspan="6" style="padding: 1rem;">Error loading bookings.</td></tr>`;
    }
  };