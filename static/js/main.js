// Aura Archives - Main JavaScript

// CSRF Cookie helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    // Fallback: read the CSRF token from the <meta> tag if the cookie is unavailable.
    if (!cookieValue && name === 'csrftoken') {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) cookieValue = meta.getAttribute('content');
    }
    return cookieValue;
}

// Toast notification
function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), duration);
}

// Add to cart (global)
function addToCart(productId, variantId = null, qty = 1) {
    fetch('/shop/cart/add/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ product_id: productId, variant_id: variantId, quantity: qty })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                if (typeof _updateCartBadge === 'function') _updateCartBadge(data.cart_count);
                else { const b = document.getElementById('cart-badge'); if (b) b.textContent = data.cart_count; }
                if (typeof closeQuickView === 'function') closeQuickView();
                if (typeof openCartDrawer === 'function') openCartDrawer();
                else showToast(data.message || 'Added to cart!');
            } else {
                showToast(data.message || 'Could not add to cart');
            }
        })
        .catch(() => showToast('Something went wrong'));
}

// Toggle wishlist (global)
function toggleWishlist(productId) {
    fetch('/wishlist/toggle/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ product_id: productId })
    })
        .then(r => {
            if (r.status === 403 || r.redirected) {
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                return;
            }
            return r.json();
        })
        .then(data => {
            if (data && data.success) showToast(data.message);
        });
}

// Dark mode toggle
function toggleDarkMode() {
    const html = document.documentElement;
    const isDark = html.classList.toggle('dark');
    localStorage.setItem('darkMode', isDark);
}

// Initialize dark mode on load
(function () {
    if (localStorage.getItem('darkMode') === 'true') {
        document.documentElement.classList.add('dark');
    }
})();
