# Mobile-First UX & Micro-Interactions Specification
**Project:** RealMap (CG-RERA Compliance Platform)
**Target Device:** Mobile First (iPhone 12/13/14/15, Android Mid-Range)
**Tone:** Professional, Trustworthy, Crisp, Regulatory-Compliant

---

## 1. Mobile Navigation & Layout

### 1.1 Bottom Navigation (Persistent)
Height: `64px` + Safe Area
Background: `rgba(255, 255, 255, 0.95)` with backdrop blur `10px`
Shadow: `0 -4px 20px rgba(0,0,0,0.04)`

**Tabs:**
1.  **Home** (Icon: Home/Dashboard) - Search entry, recent activity, news.
2.  **Check** (Icon: Shield/Search) - The core "Compliance Check" flow.
3.  **Compare** (Icon: Scales/Compare) - Side-by-side comparison of shortlisted projects.
4.  **Saved** (Icon: Bookmark/Heart) - Shortlisted projects and saved reports.

### 1.2 Top Bar (Contextual)
*   **Home/Search:** Sticky search bar with auto-suggest.
    *   *Interaction:* On scroll down, transforms from large header to compact sticky bar.
*   **Detail Page:** Transparent -> White on scroll.
    *   *Left:* Back button (large touch target `48px`).
    *   *Right:* Share, Save.

### 1.3 Floating Action Button (FAB)
*   **Context:** Visible on Home and Saved tabs.
*   **Action:** "Check Compliance" (Primary Workflow).
*   **Style:** Brand Blue (`#0ea5e9`) with white icon. Shadow `0 4px 12px rgba(14, 165, 233, 0.4)`.

---

## 2. High-Trust Mobile UI Elements

### 2.1 Compliance Score Badge
Designed to be the visual anchor of trust.
*   **Shape:** Rounded Rectangle or Shield.
*   **Typography:** Monospace numeric (e.g., "9.2") or Bold Letter Grade ("A+").
*   **Colors (Psychology):**
    *   **A+ / Excellent:** Emerald Green (`#10b981`) - "Safe, Go ahead".
    *   **B / Good:** Sky Blue (`#0ea5e9`) - "Standard, Verified".
    *   **C / Average:** Amber (`#f59e0b`) - "Caution, Check details".
    *   **D / Risk:** Rose Red (`#e11d48`) - "High Risk, Warning".

### 2.2 Verified Builder Badge
*   **Visual:** Blue tick inside a rosette or shield.
*   **Micro-interaction:** Tap to see "Verification Certificate" modal.

### 2.3 Disclaimers & Warnings
*   **Pattern:** Collapsible "Accordion" sections.
*   **Default State:** Collapsed, showing summary "3 Warnings Found".
*   **Expanded State:** Detailed list with red/orange left border.

---

## 3. Micro-Animations & Interaction Flow

**Timing Guide:**
*   **Instant:** `0ms` (Touch feedback)
*   **Fast:** `100ms` (Hover, Toggle, Opacity)
*   **Normal:** `200-250ms` (Slide-ins, Scale, Modals)
*   **Slow:** `400ms+` (Complex reveals, Progress bars)

### 3.1 Key Animations
1.  **Skeleton Loaders:** Shimmer effect (`linear-gradient` moving right) for loading states.
2.  **Progress Bar:** Smooth easing (cubic-bezier) when analyzing a project.
3.  **Slide-in Cards:** Results cards slide up from bottom (`translateY(20px)` -> `0`).
4.  **Toggle Switch:** Spring-based animation for "Verified Only" filters.
5.  **Ripple Effect:** Material-style ripple on all primary buttons (`overflow: hidden`).
6.  **Like/Save:** Heart icon scales up (`1.2`) and bounces back on tap.

### 3.2 Gestures
*   **Swipe Right:** On a project card to "Shortlist/Save".
*   **Pull to Refresh:** On Project Detail to "Update Status".
*   **Long Press:** On a card to show "Quick Preview" (Context Menu).

---

## 4. User Journey: Search → Check → Result

### 4.1 Search Stage
*   **Input:** Large text field.
*   **Suggestions:** Appear instantly as list below.
*   **Highlight:** Matching substrings bolded.
*   **Micro-interaction:** Keyboard opens, recent searches fade out, suggestions fade in.

### 4.2 Compliance Processing Stage
*   **Visual:** Full-screen overlay or large card.
*   **Animation:**
    1.  "Checking Registration..." (Spinner)
    2.  "Scraping RERA Data..." (Progress bar 30%)
    3.  "Validating Amenities..." (Progress bar 70%)
    4.  "Done" (Green Checkmark Lottie animation).

### 4.3 Result Stage
*   **Header:** Sticky "Project Summary" (Name + Score).
*   **Body:**
    *   **Risk Alerts:** Slide in first (High priority).
    *   **Detail Groups:** Accordions (Amenities, Legal, Location).
*   **CTA:** "Download Report" - Button fills with color on tap (Ripple).

---

## 5. Design Tokens (CSS Variables)

### Colors
```css
:root {
  /* Brand */
  --color-primary: #0ea5e9; /* Trust Blue */
  --color-primary-dark: #0284c7;
  --color-secondary: #64748b; /* Slate */
  
  /* Semantic */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #e11d48;
  --color-info: #3b82f6;
  
  /* Backgrounds */
  --bg-app: #f8fafc;
  --bg-card: #ffffff;
  --bg-overlay: rgba(15, 23, 42, 0.6);
  
  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
}
```

### Typography
*   **Font Family:** Inter, Roboto, or system-ui.
*   **H1 (Mobile):** `24px` / `1.2` / `700`
*   **H2 (Mobile):** `20px` / `1.3` / `600`
*   **Body:** `15px` / `1.5` / `400` (Optimized for reading)
*   **Caption:** `13px` / `1.4` / `500`

### Spacing & Radius
```css
:root {
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-full: 999px;
  
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;
}
```

### Animation
```css
:root {
  --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  --ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}
```

---

## 6. Performance Guidelines
1.  **Lazy Loading:** Images below the fold must use `loading="lazy"`.
2.  **Code Splitting:** Route-based splitting for `Compare` and `Saved` tabs.
3.  **CLS (Cumulative Layout Shift):** Reserve space for images/maps to prevent jank.
4.  **Touch Targets:** Minimum `44x44px` for all interactive elements.
