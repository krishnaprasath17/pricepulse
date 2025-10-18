# Design Guidelines: Product Price Comparison Platform

## Design Approach

**Selected Approach:** Design System with E-commerce Visual Enhancement
- **Primary System:** Material Design principles for clarity and information hierarchy
- **Visual Inspiration:** Amazon/Flipkart card aesthetics for familiar e-commerce patterns
- **Rationale:** This utility-focused comparison tool requires efficient data display and clear filtering while maintaining visual appeal through product imagery and smooth interactions

## Color Palette

### Core Colors
**Light Mode:**
- Primary: 220 90% 56% (Trust blue - reminiscent of both platforms)
- Secondary: 39 100% 50% (Flipkart orange accent)
- Success: 142 71% 45% (Savings/better price indicator)
- Background: 0 0% 98%
- Surface: 0 0% 100%
- Text Primary: 220 13% 18%
- Text Secondary: 220 9% 46%

**Dark Mode:**
- Primary: 220 90% 65%
- Secondary: 39 100% 60%
- Success: 142 71% 55%
- Background: 222 47% 11%
- Surface: 217 33% 17%
- Text Primary: 210 40% 98%
- Text Secondary: 215 20% 65%

### Semantic Colors
- Amazon Indicator: 39 100% 50%
- Flipkart Indicator: 220 90% 56%
- Price Savings: 142 71% 45%
- Warning (Similar Price): 48 96% 53%

## Typography

**Font Stack:** Inter (via Google Fonts CDN)

**Hierarchy:**
- Hero/Page Title: 3xl to 4xl, font-bold, tracking-tight
- Section Headers: 2xl, font-semibold
- Product Names: lg to xl, font-medium
- Prices: xl to 2xl, font-bold (primary prices), lg font-medium (comparison)
- Body Text: base, font-normal
- Labels/Metadata: sm, font-medium, uppercase tracking-wide for categories
- Filter Text: sm, font-normal

## Layout System

**Spacing Primitives:** Use Tailwind units of 2, 3, 4, 6, 8, 12, 16, 20
- Micro spacing: p-2, gap-2 (tight elements)
- Standard spacing: p-4, gap-4, m-4 (cards, form elements)
- Section spacing: py-8, py-12, py-16 (vertical rhythm)
- Large gaps: gap-6, gap-8 (product grid)

**Grid System:**
- Desktop (lg): 3-column product grid (grid-cols-3)
- Tablet (md): 2-column grid (grid-cols-2)
- Mobile: Single column (grid-cols-1)
- Filter Sidebar: Fixed 280px width on desktop, drawer on mobile
- Container: max-w-7xl mx-auto px-4

## Component Library

### Navigation Header
- Sticky top navigation with backdrop blur
- Logo left, category pills center, search right
- Height: h-16
- Shadow on scroll: shadow-md transition

### Category Filter Pills
- Horizontal scroll on mobile
- Active state: Primary background with white text
- Inactive: Surface background with hover lift
- Icons: Laptop, Phone, Headphones from Heroicons
- Spacing: gap-3 between pills

### Product Comparison Cards
**Structure:**
- White surface (dark mode: surface color)
- Rounded: rounded-xl
- Border: border border-gray-200/dark:border-gray-700
- Padding: p-6
- Shadow: shadow-sm hover:shadow-xl transition-all duration-300

**Card Layout:**
- Product image top (aspect-square, object-cover)
- Category badge (absolute top-4 left-4)
- Product name (2 lines max, text-ellipsis)
- Price comparison section (2-column grid)
- Platform links (flex gap-3)
- Savings badge (absolute top-4 right-4 if applicable)

**Hover Effects:**
- Transform: hover:-translate-y-1
- Shadow elevation increase
- Image subtle zoom: hover:scale-105 on image container
- Border color shift to primary

### Price Comparison Display
- Side-by-side platform cards within product card
- Amazon: Left column with orange accent border-l-4
- Flipkart: Right column with blue accent border-l-4
- Price typography: text-2xl font-bold
- Strike-through for higher price
- Savings calculation: Success color, font-semibold

### Filter Sidebar (Desktop) / Drawer (Mobile)
**Filter Groups:**
- Category (checkboxes with icons)
- Price Range (dual range slider)
- Platform (Amazon, Flipkart, Both)
- Sort Options (dropdown)

**Styling:**
- Background: Surface color
- Dividers between groups: border-b border-gray-200
- Active filters: Primary color with white text pills
- Clear filters: Text button top-right

### Search Bar
- Rounded: rounded-full
- Icon: Magnifying glass (Heroicons) left
- Placeholder: "Search products..."
- Focus: ring-2 ring-primary
- Width: w-96 on desktop, full on mobile

### Platform Badges
- Small circular logos/initials
- Amazon: Orange background, white text "A"
- Flipkart: Blue background, white text "F"
- Size: w-8 h-8, positioned top-right of product image

### Call-to-Action Buttons
- Primary CTA (View on Platform): Primary background, rounded-lg, px-4 py-2
- Secondary CTA (Compare): Outline variant with primary border
- External link icon: Arrow-top-right (Heroicons)
- Hover: Slight scale-105 transform

### Savings Badge
- Absolute positioned top-right on cards
- Success background: bg-green-500
- Rounded: rounded-full
- Padding: px-3 py-1
- Text: text-xs font-bold text-white
- Format: "Save ₹XXX" or "XX% OFF"

### Empty States
- Icon: Shopping cart or filter (Heroicons)
- Message: text-xl font-medium text-gray-500
- Suggestion text below: text-sm text-gray-400
- Center aligned with py-16

## Animations

**Global Transitions:**
- Card hover: transition-all duration-300 ease-out
- Image zoom: transition-transform duration-500
- Filter drawer: transition-transform duration-300
- Skeleton loading: animate-pulse for data loading

**Micro-interactions:**
- Checkbox/Radio: Scale animation on select
- Button press: Scale-95 on active state
- Link hover: Underline animation from left

## Images

### Hero Section
**Type:** Abstract gradient background with overlay
- Subtle geometric pattern or mesh gradient
- Colors: Blend of primary blue and secondary orange
- Height: 40vh on desktop, 30vh on mobile
- Content: Centered - Main headline, subheadline, search bar
- No large product image (reserve for product cards)

### Product Images
**Source:** Use placeholder service initially - https://placehold.co/400x400/png?text=[Category]
- Laptops: Generic laptop illustration/photo
- Phones: Generic smartphone illustration/photo  
- Headphones: Generic headphones illustration/photo
- Aspect ratio: 1:1 (square)
- Size: 400x400px rendered
- Position: Top of each product card
- Treatment: rounded-t-xl on cards, object-cover

### Category Icons
**Source:** Heroicons (solid variant)
- Laptop: ComputerDesktopIcon
- Phone: DevicePhoneMobileIcon
- Headphones: SpeakerWaveIcon
- Size: w-6 h-6 for pills, w-12 h-12 for empty states
- Color: Primary color or white on active state

### Platform Logos
- Simplified circular badges with initials
- OR use actual logo SVGs if available (small, 24x24px)
- Positioned: top-right corner of product images with slight overlap

## Responsive Behavior

**Breakpoints:**
- Mobile: Base (320px+)
- Tablet: md (768px+)
- Desktop: lg (1024px+)
- Wide: xl (1280px+)

**Mobile Adaptations:**
- Stack filter sidebar as bottom drawer
- Horizontal scroll category pills
- Single column product grid
- Condensed price comparison (vertical stack)
- Floating filter button (bottom-right, fixed)

**Desktop Enhancements:**
- Multi-column grid maximized
- Sidebar filters always visible
- Hover states fully enabled
- Comparison table view option (data-dense)