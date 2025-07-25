

function openBookingsModal(patientId) {
  fetch(`/api/patient/${patientId}/bookings`)
    .then(res => res.json())
    .then(bookings => {
      const tbody = document.getElementById("bookings-modal-body");
      tbody.innerHTML = "";

      bookings.forEach(b => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${b.date || ""}</td>
          <td>${b.time || ""}</td>
          <td>${b.profession || ""}</td>
          <td>${b.therapist || ""}</td>
          <td>${b.billing_done ? "✅" : "❌"}</td>
          <td>${b.notes_done ? "✅" : "❌"}</td>
        `;
        tbody.appendChild(row);
      });

      document.getElementById("bookings-modal").style.display = "flex";
    })
    .catch(err => console.error("Failed to load bookings:", err));
}