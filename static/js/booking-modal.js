document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("booking-modal");
    const backdrop = document.getElementById("booking-modal-backdrop");
    const closeBtn = document.getElementById("close-booking-modal");
    const form = document.getElementById("booking-form");
  
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
    };
  
    function closeBookingModal() {
      modal.style.display = "none";
      backdrop.style.display = "none";
    }
  
    closeBtn.addEventListener("click", closeBookingModal);
    backdrop.addEventListener("click", closeBookingModal);
  
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const booking = {
        id: document.getElementById("booking-id").value,
        name: document.getElementById("booking-name").value,
        date: document.getElementById("booking-date").value,
        time: document.getElementById("booking-time").value,
        duration: parseInt(document.getElementById("booking-duration").value),
        therapist_id: document.getElementById("booking-therapist").value,
        notes: document.getElementById("booking-notes").value
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