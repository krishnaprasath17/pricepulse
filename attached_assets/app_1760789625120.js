// PricePulse JavaScript Application

class PricePulseApp {
    constructor() {
        this.currentFilters = {
            category: 'All',
            search: '',
            sort: 'name',
            brands: [],
            minPrice: null,
            maxPrice: null
        };
        this.compareProducts = [];
        this.allProducts = [];
        this.allBrands = [];

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProducts();
        this.loadBrands();
    }

    setupEventListeners() {
        // Category filter buttons
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setActiveCategory(e.target.dataset.category);
                this.currentFilters.category = e.target.dataset.category;
                this.loadProducts();
            });
        });

        // Search input
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', this.debounce((e) => {
            this.currentFilters.search = e.target.value;
            this.loadProducts();
        }, 300));

        // Hero search
        const heroSearch = document.getElementById('heroSearch');
        heroSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performHeroSearch();
            }
        });

        // Sort select
        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.currentFilters.sort = e.target.value;
            this.loadProducts();
        });

        // Brand filter
        document.getElementById('brandFilter').addEventListener('change', (e) => {
            this.currentFilters.brands = Array.from(e.target.selectedOptions).map(option => option.value);
            this.loadProducts();
        });

        // Price range filters
        document.getElementById('minPrice').addEventListener('input', this.debounce((e) => {
            this.currentFilters.minPrice = e.target.value ? parseFloat(e.target.value) : null;
            this.loadProducts();
        }, 500));

        document.getElementById('maxPrice').addEventListener('input', this.debounce((e) => {
            this.currentFilters.maxPrice = e.target.value ? parseFloat(e.target.value) : null;
            this.loadProducts();
        }, 500));
    }

    async loadProducts() {
        try {
            this.showLoading();

            const params = new URLSearchParams();
            if (this.currentFilters.category && this.currentFilters.category !== 'All') {
                params.append('category', this.currentFilters.category);
            }
            if (this.currentFilters.search) {
                params.append('search', this.currentFilters.search);
            }
            if (this.currentFilters.sort) {
                params.append('sort', this.currentFilters.sort);
            }
            if (this.currentFilters.brands.length > 0) {
                this.currentFilters.brands.forEach(brand => params.append('brands', brand));
            }
            if (this.currentFilters.minPrice !== null) {
                params.append('min_price', this.currentFilters.minPrice);
            }
            if (this.currentFilters.maxPrice !== null) {
                params.append('max_price', this.currentFilters.maxPrice);
            }

            const response = await fetch(`/api/products?${params.toString()}`);
            const products = await response.json();

            this.allProducts = products;
            this.renderProducts(products);
            this.updateResultsCount(products.length);

        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products. Please try again.');
        }
    }

    async loadBrands() {
        try {
            const params = new URLSearchParams();
            if (this.currentFilters.category && this.currentFilters.category !== 'All') {
                params.append('category', this.currentFilters.category);
            }

            const response = await fetch(`/api/brands?${params.toString()}`);
            const brands = await response.json();

            this.allBrands = brands;
            this.renderBrandFilter(brands);

        } catch (error) {
            console.error('Error loading brands:', error);
        }
    }

    renderProducts(products) {
        const grid = document.getElementById('productsGrid');
        const noResults = document.getElementById('noResults');

        if (products.length === 0) {
            grid.innerHTML = '';
            noResults.classList.remove('d-none');
            return;
        }

        noResults.classList.add('d-none');

        grid.innerHTML = products.map(product => this.createProductCard(product)).join('');

        // Add event listeners to compare checkboxes
        document.querySelectorAll('.compare-checkbox input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const productName = e.target.dataset.productName;
                const product = products.find(p => p.productName === productName);

                if (e.target.checked) {
                    this.addToComparison(product);
                } else {
                    this.removeFromComparison(productName);
                }
            });
        });
    }

    getImageForProduct(product) {
        // Map categories to available stock images
        const imagesByCategory = {
            'Phones': [
                '/static/images/modern_smartphone_mo_eaff691a.jpg'
            ],
            'Laptops': [
                '/static/images/modern_laptop_comput_85fcc696.jpg'
            ],
            'Headphones': [
                '/static/images/modern_wireless_head_af4d6f0f.jpg'
            ]
        };

        const category = product.category || 'Phones';
        const list = imagesByCategory[category] || Object.values(imagesByCategory).flat();

        // Choose an image deterministically based on product name
        const key = (product.productName || product.id || Math.random()).toString();
        let hash = 0;
        for (let i = 0; i < key.length; i++) {
            hash = ((hash << 5) - hash) + key.charCodeAt(i);
            hash |= 0; // Convert to 32bit int
        }
        const idx = Math.abs(hash) % list.length;
        return list[idx];
    }

    createProductCard(product) {
            const bestPrice = Math.min(product.amazonPrice, product.flipkartPrice);
            const amazonPriceClass = product.amazonPrice === bestPrice ? 'best-price' : 'higher-price';
            const flipkartPriceClass = product.flipkartPrice === bestPrice ? 'best-price' : 'higher-price';
            const isSelected = this.compareProducts.some(p => p.productName === product.productName);
            const canCompare = this.compareProducts.length < 4 || isSelected;

            const imgSrc = this.getImageForProduct(product);

            // Coupon display
            const hasCoupon = product.couponCode && product.couponCode.length > 0;
            let couponBadge = '';
            if (hasCoupon) {
                couponBadge = `<div class="coupon-badge position-absolute top-0 start-0 m-2 badge bg-success">${product.couponCode}</div>`;
            }

            return `
            <div class="col-lg-4 col-md-6 mb-4">
                <div class="card product-card h-100 shadow-sm fade-in">
                    <div class="product-image position-relative overflow-hidden">
                        ${couponBadge}
                        <img src="${imgSrc}" alt="${product.productName}" class="w-100 h-100 object-fit-cover product-img" onerror="this.onerror=null;this.src='/static/images/modern_smartphone_mo_eaff691a.jpg'">
                        <div class="image-overlay d-flex flex-column justify-content-between p-2">
                            <div class="d-flex justify-content-end">
                                <!-- brand badge removed -->
                            </div>
                            <div class="d-flex justify-content-between align-items-end">
                                    <div class="price-mini bg-white text-dark px-2 py-1 rounded shadow-sm">
                                    ₹${bestPrice.toLocaleString()}
                                </div>
                                <button class="btn btn-sm btn-outline-light quick-view" data-product-name="${product.productName}">Quick view</button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h6 class="product-name text-truncate-2">${product.productName}</h6>
                        <!-- product brand removed -->
                        
                        <div class="price-container mt-auto">
                            <div class="price-section">
                                <div class="platform-name">Amazon</div>
                                <div>
                                    ${product.amazonDiscountedPrice ? `
                                        <div class="original-price text-muted"><s>₹${product.amazonPrice.toLocaleString()}</s></div>
                                        <div class="price ${amazonPriceClass} text-success">₹${product.amazonDiscountedPrice.toLocaleString()}</div>
                                    ` : `
                                        <div class="price ${amazonPriceClass}">₹${product.amazonPrice.toLocaleString()}</div>
                                    `}
                                </div>
                            </div>
                            <div class="price-section">
                                <div class="platform-name">Flipkart</div>
                                <div>
                                    ${product.flipkartDiscountedPrice ? `
                                        <div class="original-price text-muted"><s>₹${product.flipkartPrice.toLocaleString()}</s></div>
                                        <div class="price ${flipkartPriceClass} text-success">₹${product.flipkartDiscountedPrice.toLocaleString()}</div>
                                    ` : `
                                        <div class="price ${flipkartPriceClass}">₹${product.flipkartPrice.toLocaleString()}</div>
                                    `}
                                </div>
                            </div>
                        </div>
                        
                        <div class="d-grid gap-2 mt-3">
                            <a href="${product.amazonUrl}" target="_blank" class="btn btn-warning buy-button btn-sm">
                                <i class="fab fa-amazon me-1"></i> Amazon
                            </a>
                            <a href="${product.flipkartUrl}" target="_blank" class="btn btn-info buy-button btn-sm">
                                <i class="fas fa-shopping-cart me-1"></i> Flipkart
                            </a>
                        </div>
                        
                        <div class="compare-checkbox mt-2">
                            <label class="form-check-label d-flex align-items-center gap-2">
                                <input type="checkbox" class="form-check-input" 
                                       data-product-name="${product.productName}"
                                       ${isSelected ? 'checked' : ''}
                                       ${!canCompare ? 'disabled' : ''}>
                                <small>Add to comparison</small>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderBrandFilter(brands) {
        const brandFilter = document.getElementById('brandFilter');
        brandFilter.innerHTML = brands.map(brand =>
            `<option value="${brand}">${brand}</option>`
        ).join('');
    }

    addToComparison(product) {
        if (this.compareProducts.length >= 4) {
            this.showAlert('You can compare up to 4 products at once.', 'warning');
            return;
        }

        if (!this.compareProducts.some(p => p.productName === product.productName)) {
            this.compareProducts.push(product);
            this.updateCompareBar();
        }
    }

    removeFromComparison(productName) {
        this.compareProducts = this.compareProducts.filter(p => p.productName !== productName);
        this.updateCompareBar();
    }

    updateCompareBar() {
        const compareBar = document.getElementById('compareBar');
        const compareCount = document.getElementById('compareCount');
        const compareBtn = document.getElementById('compareBtn');

        if (this.compareProducts.length > 0) {
            compareBar.classList.remove('d-none');
            compareCount.textContent = this.compareProducts.length;
            compareBtn.disabled = this.compareProducts.length < 2;
        } else {
            compareBar.classList.add('d-none');
        }

        // Update checkboxes in the grid
        document.querySelectorAll('.compare-checkbox input[type="checkbox"]').forEach(checkbox => {
            const productName = checkbox.dataset.productName;
            const isSelected = this.compareProducts.some(p => p.productName === productName);
            const canCompare = this.compareProducts.length < 4 || isSelected;

            checkbox.checked = isSelected;
            checkbox.disabled = !canCompare;
        });
    }

    async showComparison() {
        if (this.compareProducts.length < 2) {
            this.showAlert('Please select at least 2 products to compare.', 'warning');
            return;
        }

        try {
            const productIds = this.compareProducts.map(p => p.id || 0);
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ productIds })
            });

            const comparisonData = await response.json();
            // Server returns an object { comparison: [...], overallBest: {...} }
            // Extract the array for the modal renderer which expects an array.
            const products = Array.isArray(comparisonData) ? comparisonData : (comparisonData.comparison || []);
            this.renderComparisonModal(products);

            // Optionally, you can surface overallBest to the user (not implemented in modal yet)
            // const overallBest = comparisonData.overallBest;

            const modal = new bootstrap.Modal(document.getElementById('comparisonModal'));
            modal.show();

        } catch (error) {
            console.error('Error comparing products:', error);
            this.showAlert('Failed to compare products. Please try again.', 'danger');
        }
    }

    renderComparisonModal(products) {
            const content = document.getElementById('comparisonContent');

            if (products.length === 0) {
                content.innerHTML = '<p class="text-center text-muted">No products to compare.</p>';
                return;
            }

            const table = `
            <div class="table-responsive">
                <table class="table table-bordered comparison-table">
                    <thead>
                        <tr>
                            <th>Product</th>
                            ${products.map(p => `
                                <th>
                                    <div class="comparison-product-image overflow-hidden">
                                        <img src="${this.getImageForProduct(p)}" alt="${p.productName}" class="w-100 h-100 object-fit-cover" onerror="this.onerror=null;this.src='/static/images/modern_smartphone_mo_eaff691a.jpg'">
                                    </div>
                                    <div class="comparison-product-name mt-2">${p.productName}</div>
                                    <div class="text-muted small">${p.brand || 'Unknown Brand'}</div>
                                </th>
                            `).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Amazon Price</strong></td>
                            ${products.map(p => `
                                <td>
                                    <div class="comparison-price ${p.amazonPrice === p.bestPrice ? 'best-price' : 'higher-price'}">
                                        ₹${p.amazonPrice.toLocaleString()}
                                    </div>
                                    ${p.amazonDiscountedPrice ? `<div class="text-success small mt-1">After coupon: ₹${p.amazonDiscountedPrice.toLocaleString()}</div>` : ''}
                                    <a href="${p.amazonUrl}" target="_blank" class="btn btn-sm btn-warning mt-2">
                                        <i class="fab fa-amazon me-1"></i> Buy
                                    </a>
                                </td>
                            `).join('')}
                        </tr>
                        <tr>
                            <td><strong>Flipkart Price</strong></td>
                            ${products.map(p => `
                                <td>
                                    <div class="comparison-price ${p.flipkartPrice === p.bestPrice ? 'best-price' : 'higher-price'}">
                                        ₹${p.flipkartPrice.toLocaleString()}
                                    </div>
                                    ${p.flipkartDiscountedPrice ? `<div class="text-success small mt-1">After coupon: ₹${p.flipkartDiscountedPrice.toLocaleString()}</div>` : ''}
                                    <a href="${p.flipkartUrl}" target="_blank" class="btn btn-sm btn-info mt-2">
                                        <i class="fas fa-shopping-cart me-1"></i> Buy
                                    </a>
                                </td>
                            `).join('')}
                        </tr>
                        <tr>
                            <td><strong>Best Platform</strong></td>
                            ${products.map(p => `
                                <td>
                                    <span class="badge bg-success">${p.bestPlatform}</span>
                                    ${p.couponCode ? `<div class="small mt-2 text-success">Coupon: <strong>${p.couponCode}</strong> (${p.couponType} ${p.couponAmount || ''})</div>` : ''}
                                </td>
                            `).join('')}
                        </tr>
                        <tr>
                            <td><strong>Price Difference</strong></td>
                            ${products.map(p => `
                                <td>
                                    <div class="price-difference ${p.amazonPrice < p.flipkartPrice ? 'savings' : 'extra-cost'}">
                                        ₹${p.priceDifference.toLocaleString()}
                                    </div>
                                    <small class="text-muted">
                                        ${p.amazonPrice < p.flipkartPrice ? 'Save on Amazon' : 'Save on Flipkart'}
                                    </small>
                                </td>
                            `).join('')}
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        content.innerHTML = table;
    }
    
    setActiveCategory(category) {
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
    }
    
    updateResultsCount(count) {
        document.getElementById('resultsCount').textContent = 
            `${count} ${count === 1 ? 'Product' : 'Products'} Found`;
    }
    
    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('d-none');
        document.getElementById('productsGrid').innerHTML = '';
    }
    
    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('d-none');
    }
    
    showError(message) {
        this.hideLoading();
        this.showAlert(message, 'danger');
    }
    
    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
    
    clearFilters() {
        this.currentFilters = {
            category: 'All',
            search: '',
            sort: 'name',
            brands: [],
            minPrice: null,
            maxPrice: null
        };
        
        // Reset UI elements
        this.setActiveCategory('All');
        document.getElementById('searchInput').value = '';
        document.getElementById('sortSelect').value = 'name';
        document.getElementById('brandFilter').value = '';
        document.getElementById('minPrice').value = '';
        document.getElementById('maxPrice').value = '';
        
        this.loadProducts();
    }
    
    applyFilters() {
        this.loadProducts();
    }
    
    clearComparison() {
        this.compareProducts = [];
        this.updateCompareBar();
        
        // Uncheck all compare checkboxes
        document.querySelectorAll('.compare-checkbox input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
            checkbox.disabled = false;
        });
    }
    
    performHeroSearch() {
        const heroSearch = document.getElementById('heroSearch');
        const searchInput = document.getElementById('searchInput');
        
        this.currentFilters.search = heroSearch.value;
        searchInput.value = heroSearch.value;
        this.loadProducts();
        
        // Scroll to products section
        document.getElementById('products').scrollIntoView({ behavior: 'smooth' });
    }
    
    performSearch() {
        this.performHeroSearch();
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Global functions for HTML onclick handlers
function clearFilters() {
    window.pricePulseApp.clearFilters();
}

function applyFilters() {
    window.pricePulseApp.applyFilters();
}

function clearComparison() {
    window.pricePulseApp.clearComparison();
}

function showComparison() {
    window.pricePulseApp.showComparison();
}

function performSearch() {
    window.pricePulseApp.performSearch();
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.pricePulseApp = new PricePulseApp();
});