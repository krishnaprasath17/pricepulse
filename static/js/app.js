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
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setActiveCategory(e.target.dataset.category);
                this.currentFilters.category = e.target.dataset.category;
                this.loadProducts();
            });
        });

        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', this.debounce((e) => {
            this.currentFilters.search = e.target.value;
            this.loadProducts();
        }, 300));

        const heroSearch = document.getElementById('heroSearch');
        heroSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performHeroSearch();
            }
        });

        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.currentFilters.sort = e.target.value;
            this.loadProducts();
        });

        document.getElementById('brandFilter').addEventListener('change', (e) => {
            this.currentFilters.brands = Array.from(e.target.selectedOptions).map(option => option.value);
            this.loadProducts();
        });

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
            this.hideLoading();

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
        const imagesByCategory = {
            'Phones': '/static/images/modern_smartphone_mo_eaff691a_1760789607574.jpg',
            'Laptops': '/static/images/modern_laptop_comput_85fcc696_1760789607574.jpg',
            'Headphones': '/static/images/modern_wireless_head_af4d6f0f_1760789607575.jpg'
        };

        return imagesByCategory[product.category] || imagesByCategory['Phones'];
    }

    createProductCard(product) {
        const bestPrice = Math.min(product.amazonPrice, product.flipkartPrice);
        const amazonPriceClass = product.amazonPrice === bestPrice ? 'best-price' : 'higher-price';
        const flipkartPriceClass = product.flipkartPrice === bestPrice ? 'best-price' : 'higher-price';
        const isSelected = this.compareProducts.some(p => p.productName === product.productName);
        const canCompare = this.compareProducts.length < 4 || isSelected;

        const imgSrc = this.getImageForProduct(product);

        const amazonCouponBadge = product.amazonCoupon ? 
            `<div class="coupon-badge position-absolute top-0 start-0 m-2 badge bg-warning text-dark" title="${product.amazonCoupon}">
                <i class="fas fa-tag"></i> Amazon Coupon
            </div>` : '';
        
        const flipkartCouponBadge = product.flipkartCoupon ? 
            `<div class="coupon-badge position-absolute top-0 end-0 m-2 badge bg-info text-dark" title="${product.flipkartCoupon}">
                <i class="fas fa-tag"></i> Flipkart Coupon
            </div>` : '';

        return `
        <div class="col-lg-4 col-md-6 mb-4">
            <div class="card product-card h-100 shadow-sm fade-in">
                <div class="product-image position-relative overflow-hidden">
                    ${amazonCouponBadge}
                    ${flipkartCouponBadge}
                    <img src="${imgSrc}" alt="${product.productName}" class="w-100 h-100 object-fit-cover product-img" onerror="this.onerror=null;this.src='/static/images/modern_smartphone_mo_eaff691a_1760789607574.jpg'">
                    <div class="image-overlay d-flex flex-column justify-content-between p-2">
                        <div></div>
                        <div class="d-flex justify-content-between align-items-end">
                            <div class="price-mini bg-white text-dark px-2 py-1 rounded shadow-sm">
                                ₹${bestPrice.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="product-name text-truncate-2">${product.productName}</h6>
                    ${product.brand ? `<p class="product-brand">${product.brand}</p>` : ''}
                    
                    ${product.amazonCoupon || product.flipkartCoupon ? `
                        <div class="coupon-info mb-2">
                            ${product.amazonCoupon ? `<small class="text-warning d-block"><i class="fas fa-ticket-alt"></i> Amazon: ${product.amazonCoupon}</small>` : ''}
                            ${product.flipkartCoupon ? `<small class="text-info d-block"><i class="fas fa-ticket-alt"></i> Flipkart: ${product.flipkartCoupon}</small>` : ''}
                        </div>
                    ` : ''}
                    
                    <div class="price-container mt-auto">
                        <div class="price-section">
                            <div class="platform-name">Amazon</div>
                            <div class="price ${amazonPriceClass}">₹${product.amazonPrice.toLocaleString()}</div>
                        </div>
                        <div class="price-section">
                            <div class="platform-name">Flipkart</div>
                            <div class="price ${flipkartPriceClass}">₹${product.flipkartPrice.toLocaleString()}</div>
                        </div>
                    </div>
                    
                    <div class="d-grid gap-2 mt-3">
                        <a href="${product.amazonUrl}" target="_blank" class="btn btn-warning buy-button btn-sm">
                            <i class="fab fa-amazon me-1"></i> Buy on Amazon
                        </a>
                        <a href="${product.flipkartUrl}" target="_blank" class="btn btn-info buy-button btn-sm">
                            <i class="fas fa-shopping-cart me-1"></i> Buy on Flipkart
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
            const productIds = this.compareProducts.map(p => p.id);
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ productIds })
            });

            const comparisonData = await response.json();
            this.renderComparisonModal(comparisonData);

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
                                <div class="comparison-product-image">
                                    <img src="${this.getImageForProduct(p)}" alt="${p.productName}" class="w-100 h-100 object-fit-cover rounded">
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
                                ${p.amazonCoupon ? `<div class="text-warning small mt-1"><i class="fas fa-ticket-alt"></i> ${p.amazonCoupon}</div>` : ''}
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
                                ${p.flipkartCoupon ? `<div class="text-info small mt-1"><i class="fas fa-ticket-alt"></i> ${p.flipkartCoupon}</div>` : ''}
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
                                <div class="text-success small mt-1">Save ₹${p.priceDifference.toLocaleString()}</div>
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

document.addEventListener('DOMContentLoaded', function() {
    window.pricePulseApp = new PricePulseApp();
});
