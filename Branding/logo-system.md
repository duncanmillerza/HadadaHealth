# Logo System

> Complete logo variations and usage guidelines for HadadaHealth brand applications.

## Logo Variations Overview

HadadaHealth maintains a comprehensive logo system with multiple variations for different applications and contexts. Each logo serves specific use cases in the healthcare practice management ecosystem.

## Primary Logo Variations

### 1. Wordmark Logos (Horizontal Layout)

#### Wordmark Mono (`Wordmark Mono.svg`)
- **Primary use:** Main navigation bars, headers, business documents
- **Context:** Dark backgrounds (white logo on dark)
- **Best for:** Desktop applications, letterheads, signage
- **Minimum height:** 32px digital, 0.75 inches print

#### Wordmark Green (`Wordmark Green.svg`)
- **Primary use:** Light backgrounds, print materials
- **Context:** White or light-colored backgrounds
- **Best for:** Business cards, forms, light-themed interfaces
- **Minimum height:** 32px digital, 0.75 inches print

#### Wordmark White (`Wordmark White.svg`)
- **Primary use:** Dark backgrounds, colored overlays
- **Context:** Photos, dark interface themes, colored backgrounds
- **Best for:** Hero sections, dark mode interfaces, promotional materials
- **Minimum height:** 32px digital, 0.75 inches print

#### Wordmark Mono Long (`Wordmark Mono Long.svg`)
- **Primary use:** Wide layout applications
- **Context:** Extended horizontal spaces, banners
- **Best for:** Website headers, email signatures, wide promotional banners
- **Minimum height:** 24px digital, 0.5 inches print

### 2. Text-Only Variations (Typography Focus)

#### Text Green (`Text Green.svg`)
- **Primary use:** Text-heavy applications, medical documents
- **Context:** Clean, clinical documentation
- **Best for:** Clinical reports, forms, professional correspondence
- **Minimum height:** 20px digital, 0.4 inches print

#### Text Dark (`Text Dark.svg`)
- **Primary use:** High-contrast text applications
- **Context:** Light backgrounds requiring strong readability
- **Best for:** User manuals, training materials, accessibility-first designs
- **Minimum height:** 20px digital, 0.4 inches print

#### Text Green Double (`Text Green Double.svg`)
- **Primary use:** Emphasis applications, special documents
- **Context:** Certificates, awards, formal announcements
- **Best for:** Official documents, recognition materials
- **Minimum height:** 24px digital, 0.5 inches print

### 3. Stacked Variations (Vertical Layout)

#### Stacked Logo Green (`Stacked Logo Green.svg`)
- **Primary use:** Square spaces, mobile applications, social media
- **Context:** Profile images, app icons, compact layouts
- **Best for:** Social media avatars, mobile app splash screens, square signage
- **Minimum height:** 60px digital, 1 inch print

#### Stacked Logo Dark (`Stacked Logo Dark.svg`)
- **Primary use:** Light backgrounds, inverted applications
- **Context:** Light-themed mobile apps, print on light materials
- **Best for:** Light mode mobile interfaces, printed materials on light stock
- **Minimum height:** 60px digital, 1 inch print

#### Stacked Logo White (`Stacked Logo White.svg`)
- **Primary use:** Dark or colored backgrounds
- **Context:** Dark themes, photo overlays, colored backgrounds
- **Best for:** Dark mode applications, photo backgrounds, colored promotional materials
- **Minimum height:** 60px digital, 1 inch print

### 4. Monogram/Symbol Only (Icon Applications)

#### Monogram Green (`Monogram Green.svg`)
- **Primary use:** App icons, favicons, small space applications
- **Context:** Where full wordmark won't be legible
- **Best for:** Browser favicons, mobile app icons, small UI elements
- **Minimum height:** 16px digital, 0.25 inches print

#### Monogram Dark (`Monogram Dark.svg`)
- **Primary use:** Light backgrounds, high contrast needed
- **Context:** Light interface elements, monochrome applications
- **Best for:** Light-themed favicons, watermarks, minimal branding
- **Minimum height:** 16px digital, 0.25 inches print

#### Monogram White (`Monogram White.svg`)
- **Primary use:** Dark backgrounds, overlay applications
- **Context:** Dark interfaces, photo overlays
- **Best for:** Dark-themed applications, loading screens, overlays
- **Minimum height:** 16px digital, 0.25 inches print

### 5. Colored Symbol Variations

#### Logo Green (`Logo Green.svg`)
- **Primary use:** Brand accent, secondary branding
- **Context:** Supporting brand elements, accent graphics
- **Best for:** Website elements, promotional graphics, brand accents
- **Minimum height:** 24px digital, 0.5 inches print

#### Logo Blue (`Logo Blue.svg`)
- **Primary use:** Secondary brand applications
- **Context:** When primary green conflicts with content
- **Best for:** Healthcare charts, alternative branding contexts
- **Minimum height:** 24px digital, 0.5 inches print

#### Logo Red (`Logo Red.svg`)
- **Primary use:** Alert/urgent contexts only
- **Context:** Emergency communications, urgent notifications
- **Best for:** Alert systems, urgent healthcare communications (use sparingly)
- **Minimum height:** 24px digital, 0.5 inches print

#### Mobile Icon (`Mobile Icon.svg`)
- **Primary use:** Mobile app icons, PWA manifests, app store listings
- **Context:** Square/rounded square app icon formats
- **Best for:** iOS/Android app icons, PWA installations, app store graphics
- **Format:** 999x999px with integrated rounded corners (rx="200")
- **Background:** Primary green (#2D6356) optimized for app icon display
- **Minimum size:** 16x16px, optimal at 512x512px and above

## Usage Guidelines by Context

### Digital Applications

#### Website Headers (Desktop)
- **Use:** `Wordmark Green.svg` or `Wordmark White.svg`
- **Size:** 40-48px height
- **Clear space:** 32px all sides

#### Website Headers (Mobile)
- **Use:** `Monogram Green.svg` or `Stacked Logo Green.svg`
- **Size:** 32-40px height
- **Clear space:** 16px all sides

#### App Icons
- **Use:** `Monogram Green.svg` (primary) or `Stacked Logo Green.svg`
- **Size:** Following platform guidelines (16x16 to 512x512px)
- **Background:** Transparent or brand-appropriate solid color

#### Social Media Profiles
- **Use:** `Stacked Logo Green.svg` or `Monogram Green.svg`
- **Size:** Platform-specific (typically 400x400px)
- **Background:** White or transparent

#### Email Signatures
- **Use:** `Wordmark Green.svg` or `Text Green.svg`
- **Size:** 120-150px width maximum
- **Format:** PNG or SVG with transparent background

### Print Applications

#### Business Cards
- **Use:** `Text Green.svg` or `Wordmark Green.svg`
- **Size:** 0.75-1 inch width
- **Placement:** Top left or bottom right

#### Letterheads
- **Use:** `Wordmark Green.svg` or `Text Green.svg`
- **Size:** 1-1.5 inch width
- **Placement:** Top left corner

#### Clinical Documents
- **Use:** `Text Green.svg` or `Monogram Green.svg`
- **Size:** 0.5-0.75 inch
- **Placement:** Header or footer, subtle presence

#### Signage
- **Use:** `Wordmark Green.svg` or `Stacked Logo Green.svg`
- **Size:** Minimum 6 inches width for readability
- **Material:** High contrast with background

## Color Usage Rules

### When to Use Green Variations
- Primary brand communications
- Healthcare-focused materials
- Professional medical contexts
- Trust and reliability messaging

### When to Use White Variations
- Dark backgrounds (navigation bars, headers)
- Photo overlays
- High-contrast scenarios
- Dark mode interfaces

### When to Use Dark/Mono Variations
- Light backgrounds requiring contrast
- Monochrome printing
- High-accessibility applications
- Minimal design aesthetics

### When to Use Alternative Colors (Blue/Red)
- **Blue:** Secondary contexts, non-medical applications
- **Red:** Emergency communications only (use sparingly)
- **Never use:** For primary brand communications

## Implementation Examples

### Mobile Navigation Center Button
```html
<a href="#" class="mobile-nav-link home-logo">
  <!-- Light mode logo -->
  <svg viewBox="0 0 1000 1000" fill="none" class="logo-light">
    <circle cx="500" cy="500" r="500" fill="#96364C"/>
    <path d="M873 366.183C854.864 291.315..." stroke="white" stroke-width="30"/>
  </svg>
  <!-- Dark mode logo -->
  <svg viewBox="0 0 1000 1000" fill="none" class="logo-dark">
    <circle cx="500" cy="500" r="500" fill="#2D6356"/>
    <path d="M873 366.183C854.864 291.315..." stroke="white" stroke-width="30"/>
  </svg>
  <span>Home</span>
</a>
```

```css
.mobile-nav-link.home-logo {
  position: relative;
  margin-top: -32px; /* Creates overlap above nav bar */
  opacity: 1 !important; /* Always full opacity */
}

.mobile-nav-link.home-logo svg {
  width: 68px;
  height: 68px;
  opacity: 1;
  transition: transform 0.2s ease;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
}

.mobile-nav-link.home-logo:hover svg {
  transform: scale(1.05);
  filter: drop-shadow(0 6px 12px rgba(0, 0, 0, 0.2));
}

/* Logo visibility based on theme */
.logo-light { display: block; }
.logo-dark { display: none; }

[data-theme="dark"] .logo-light { display: none; }
[data-theme="dark"] .logo-dark { display: block; }
```

### Clinical Document Headers
```html
<div class="document-header">
  <svg viewBox="0 0 776 855" style="width: 20px; height: 24px;">
    <path d="M761 294.183C742.864..." stroke="#2D6356" stroke-width="30"/>
  </svg>
  <div>
    <strong>Treatment Assessment</strong>
    <p>Patient ID: HH-2025-0847</p>
  </div>
</div>
```

### Loading Screens
```html
<div class="loading-screen">
  <svg viewBox="0 0 776 855" style="width: 48px; height: 56px;">
    <path d="M761 294.183..." stroke="white" stroke-width="30"/>
  </svg>
  <p>Loading...</p>
</div>
```

### Email Signatures
```html
<div class="email-signature">
  <svg viewBox="0 0 2928 251" style="width: 120px; height: auto;">
    <path d="M203.2 0.225V251H169.25..." fill="#2D6356"/>
  </svg>
  <div class="contact-info">
    <p><strong>Dr. Sarah Johnson</strong></p>
    <p>Physiotherapist</p>
  </div>
</div>
```

## Technical Specifications

### File Format Guidelines
- **Digital:** SVG preferred (scalable, crisp at all sizes)
- **Print:** SVG or high-resolution PNG (300 DPI minimum)
- **Email:** PNG with transparent background
- **Web:** SVG with PNG fallback

### Clear Space Requirements
- **Minimum clear space:** Equal to the height of the Hadada bird symbol
- **Optimal clear space:** 1.5x the height of the logo
- **Never place:** Within the clear space zone

### Size Limitations
- **Minimum digital:** 16px height (monogram only)
- **Minimum print:** 0.25 inches height
- **Maximum:** No maximum, but ensure proportional scaling
- **Readability threshold:** Text should be legible at minimum sizes

## Logo Don'ts

### Never Do
- ❌ Stretch or distort proportions
- ❌ Change colors outside approved palette
- ❌ Add effects (drop shadows, outlines, gradients)
- ❌ Place on busy backgrounds without sufficient contrast
- ❌ Recreate or modify the logo artwork
- ❌ Use low-resolution versions for print
- ❌ Place multiple logo variations on same page
- ❌ Use red variation for non-emergency communications

### Always Do
- ✅ Maintain original proportions
- ✅ Use appropriate variation for context
- ✅ Ensure sufficient contrast with background
- ✅ Maintain clear space requirements
- ✅ Use highest quality version available
- ✅ Test legibility at intended size
- ✅ Consider accessibility in color choices

## Healthcare-Specific Considerations

### Clinical Documentation
- Use minimal, professional variations (`Text Green.svg`, `Monogram Green.svg`)
- Ensure POPIA compliance in patient-facing materials
- Maintain medical professionalism in all applications

### Patient-Facing Materials
- Use trustworthy variations (`Wordmark Green.svg`, `Stacked Logo Green.svg`)
- Ensure accessibility for all patients (contrast, size)
- Consider multilingual contexts in South Africa

### Multi-Disciplinary Applications
- Maintain consistency across all healthcare disciplines
- Logo should not favor any single therapy type
- Universal healthcare appeal in all variations

---

**Related Files:**
- [Color System](color-system.md) - Logo color specifications
- [Dark Mode](dark-mode.md) - Theme-specific logo usage
- [Mobile Navigation](components/navigation.md) - Logo integration examples

*This logo system ensures consistent brand application across all HadadaHealth healthcare practice management interfaces while maintaining clinical professionalism and accessibility.*