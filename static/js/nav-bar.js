document.addEventListener('DOMContentLoaded', () => {
  fetch('/static/fragments/nav.html')
    .then(res => {
      if (!res.ok) throw new Error('Failed to fetch combined nav');
      return res.text();
    })
    .then(html => {
      const wrapper = document.createElement('div');
      wrapper.innerHTML = html;
      const topContainer = document.getElementById('top-nav');
      const bottomContainer = document.getElementById('bottom-nav');
      const topNav = wrapper.querySelector('#combined-top-nav');
      const bottomNav = wrapper.querySelector('#combined-bottom-nav');
      if (topContainer && topNav) topContainer.innerHTML = topNav.outerHTML;
      if (bottomContainer && bottomNav) bottomContainer.innerHTML = bottomNav.outerHTML;
    })
    .catch(err => console.error(err));
});

// Admin dropdown toggle for top nav
function toggleAdminMenu() {
  const dropdown = document.getElementById('admin-dropdown');
  if (!dropdown) return;
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Close top admin dropdown when clicking outside
document.addEventListener('click', (event) => {
  const isClickInside = event.target.closest('.nav-link');
  const dropdown = document.getElementById('admin-dropdown');
  if (!isClickInside && dropdown) {
    dropdown.style.display = 'none';
  }
});

// Admin dropdown toggle for bottom nav
function toggleBottomAdminMenu() {
  const dropdown = document.getElementById('bottom-admin-dropdown');
  if (!dropdown) return;
  dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
}

// Close bottom admin dropdown when clicking outside
document.addEventListener('click', (event) => {
  const dropdown = document.getElementById('bottom-admin-dropdown');
  const isClickInsideBottom = event.target.closest('.nav-link');
  if (dropdown && !isClickInsideBottom) {
    dropdown.style.display = 'none';
  }
});

// Logout handler: calls the backend and redirects to login page
function logout() {
  fetch('/logout', { credentials: 'include' })
    .then(res => {
      if (res.ok) {
        window.location.href = '/';
      } else {
        console.error('Logout failed');
      }
    })
    .catch(err => console.error('Logout error:', err));
}