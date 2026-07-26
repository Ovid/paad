---
name: agentic-a11y
description: Use when auditing a user-facing app — web, mobile (iOS/Android/React Native/Flutter), desktop, CLI, or games — for accessibility barriers or WCAG 2.2 conformance, before shipping UI changes, or in response to concerns about screen-reader, keyboard, low-vision, motor, cognitive, or photosensitive users. Not for general bug hunting or code correctness.
---

**On invocation:** announce "Running paad:agentic-a11y v1.21.0" before anything else.

# Accessibility Audit

Multi-agent accessibility audit of user-facing code across any platform. Dispatches specialist agents in parallel — each focused on a different disability category — verifies findings to filter false positives, maps every issue to specific accessibility criteria, and produces a persistent report with concrete fix recommendations.

**Conformance target:** WCAG 2.2 AA as baseline (applied via WCAG2ICT for non-web platforms). AAA criteria are flagged as bonus recommendations. Platform-specific guidelines (Apple HIG Accessibility, Android Accessibility, Xbox Accessibility Guidelines) are referenced where applicable.

**This is a technique skill.** Follow the phases in order. Do not skip verification.

**Pre-flight:**

```dot
digraph preflight {
  "Conversation has history?" [shape=diamond];
  "User-facing code exists?" [shape=diamond];
  "Proceed to Phase 1" [shape=box];
  "STOP: recommend new session" [shape=box, style=bold];
  "STOP: no user-facing code" [shape=box, style=bold];

  "Conversation has history?" -> "STOP: recommend new session" [label="yes"];
  "Conversation has history?" -> "User-facing code exists?" [label="no"];
  "User-facing code exists?" -> "STOP: no user-facing code" [label="no"];
  "User-facing code exists?" -> "Proceed to Phase 1" [label="yes"];
}
```

**Audit flow:**

```dot
digraph audit_flow {
  "Scope size?" [shape=diamond];
  "Platform has framework-specific a11y pitfalls?" [shape=diamond];
  "Existing a11y tooling already catches it?" [shape=diamond];
  "Tooling misconfigured or finding suppressed?" [shape=diamond];
  "Barrier handled elsewhere?" [shape=diamond];
  "Confidence >= 60?" [shape=diamond];
  "Cited criterion correct?" [shape=diamond];
  "Reported by multiple specialists?" [shape=diamond];
  "AAA criterion?" [shape=diamond];

  "Detect platform(s), stack, tooling, steering files, manifest" [shape=box];
  "Partition files across 2 instances of each specialist" [shape=box];
  "Dispatch the 5 core specialists in parallel" [shape=box];
  "Dispatch the 5 core specialists + Platform-Specific Patterns in parallel" [shape=box];
  "DROP the finding" [shape=box];
  "Correct the criterion" [shape=box];
  "Assign severity: critical / serious / moderate / minor" [shape=box];
  "Merge duplicates, note the agreeing specialists" [shape=box];
  "List under Minor Issues & AAA Recommendations, prefix [AAA]" [shape=box];
  "Place under its severity section" [shape=box];
  "Write report to paad/a11y-reviews/a11y-<timestamp>.md" [shape=box];
  "Report location, counts by severity, Quick Wins guidance" [shape=box];
  "STOP: report is the deliverable — do NOT auto-fix" [shape=box, style=bold];

  "Detect platform(s), stack, tooling, steering files, manifest" -> "Scope size?";
  "Scope size?" -> "Platform has framework-specific a11y pitfalls?" [label="small (<20) / medium (20-100)"];
  "Scope size?" -> "Partition files across 2 instances of each specialist" [label="large (100+ user-facing files)"];
  "Partition files across 2 instances of each specialist" -> "Platform has framework-specific a11y pitfalls?";
  "Platform has framework-specific a11y pitfalls?" -> "Dispatch the 5 core specialists + Platform-Specific Patterns in parallel" [label="yes"];
  "Platform has framework-specific a11y pitfalls?" -> "Dispatch the 5 core specialists in parallel" [label="no"];
  "Dispatch the 5 core specialists in parallel" -> "Existing a11y tooling already catches it?";
  "Dispatch the 5 core specialists + Platform-Specific Patterns in parallel" -> "Existing a11y tooling already catches it?";

  "Existing a11y tooling already catches it?" -> "Tooling misconfigured or finding suppressed?" [label="yes — specialists check this"];
  "Existing a11y tooling already catches it?" -> "Barrier handled elsewhere?" [label="no"];
  "Tooling misconfigured or finding suppressed?" -> "DROP the finding" [label="no — do not re-flag what tooling already catches"];
  "Tooling misconfigured or finding suppressed?" -> "Barrier handled elsewhere?" [label="yes"];
  "Barrier handled elsewhere?" -> "DROP the finding" [label="yes — parent, platform API, framework, library, system setting (verifier)"];
  "Barrier handled elsewhere?" -> "Confidence >= 60?" [label="no"];
  "Confidence >= 60?" -> "DROP the finding" [label="no"];
  "Confidence >= 60?" -> "Cited criterion correct?" [label="yes"];
  "Cited criterion correct?" -> "Assign severity: critical / serious / moderate / minor" [label="yes"];
  "Cited criterion correct?" -> "Correct the criterion" [label="no"];
  "Correct the criterion" -> "Assign severity: critical / serious / moderate / minor";
  "Assign severity: critical / serious / moderate / minor" -> "Reported by multiple specialists?";
  "Reported by multiple specialists?" -> "Merge duplicates, note the agreeing specialists" [label="yes"];
  "Reported by multiple specialists?" -> "AAA criterion?" [label="no"];
  "Merge duplicates, note the agreeing specialists" -> "AAA criterion?";
  "AAA criterion?" -> "List under Minor Issues & AAA Recommendations, prefix [AAA]" [label="yes — a recommendation, not a failure"];
  "AAA criterion?" -> "Place under its severity section" [label="no"];

  "List under Minor Issues & AAA Recommendations, prefix [AAA]" -> "Write report to paad/a11y-reviews/a11y-<timestamp>.md";
  "Place under its severity section" -> "Write report to paad/a11y-reviews/a11y-<timestamp>.md";
  "DROP the finding" -> "Write report to paad/a11y-reviews/a11y-<timestamp>.md" [label="counted under Filtered out"];
  "Write report to paad/a11y-reviews/a11y-<timestamp>.md" -> "Report location, counts by severity, Quick Wins guidance";
  "Report location, counts by severity, Quick Wins guidance" -> "STOP: report is the deliverable — do NOT auto-fix";
}
```

## When NOT to Use This Skill

- **The user needs a legal conformance statement (VPAT, EN 301 549 attestation)** — this produces an engineering audit, not a certified accessibility conformance report. Say so rather than letting a report be mistaken for one.

## Arguments

`/paad:agentic-a11y` accepts optional `$ARGUMENTS`:

- `/paad:agentic-a11y` — audit all user-facing code in the repository
- `/paad:agentic-a11y src/components/` — scope the audit to a specific directory
- `/paad:agentic-a11y src/components/Modal.tsx` — audit a specific file

When a path is provided, only audit files within that scope. Still detect platform and run all specialists, but limit the file manifest accordingly.

## Pre-flight Checks

1. **Context window:** If conversation has substantive history beyond invoking this skill, tell the user: "This audit consumes significant context. Start a fresh session with `/paad:agentic-a11y` to avoid context rot." Stop and wait.
2. **User-facing code:** Scan for any of the following. If none found, tell the user: "No user-facing code detected in this repository." Stop.

| Platform | File indicators |
|----------|----------------|
| **Web** | `.html`, `.jsx`, `.tsx`, `.vue`, `.svelte`, `.ejs`, `.hbs`, `.blade.php`, `.erb`, `.jinja`, `.twig`, `.css`, `.scss`, `.less`, plus JS/TS with DOM manipulation |
| **iOS (native)** | `.swift` (SwiftUI views), `.m`/`.h` (UIKit), `.storyboard`, `.xib` |
| **Android (native)** | `.kt`/`.java` (Compose or View classes), `res/layout/*.xml` |
| **React Native** | `.jsx`/`.tsx` with `react-native` imports |
| **Flutter** | `.dart` files with `package:flutter` imports |
| **Desktop** | Electron (web stack), Qt (`.cpp`/`.qml`), WPF/WinForms (`.xaml`/`.cs`), macOS AppKit/SwiftUI, GTK |
| **CLI** | Any code producing terminal output or accepting terminal input (look for stdout/stderr writes, readline, prompt libraries, curses/ncurses, argument parsers) |
| **Game** | Unity (`.cs` scripts), Unreal (C++/Blueprints), Godot (`.gd`/`.tscn`), custom engines with rendering/input systems |

## Phase 1: Reconnaissance

Run these steps and collect results:

### 1. Platform detection

Classify the project into one or more platforms from the table above. A project may span multiple platforms (e.g., a web app with a CLI tool, or a React Native app with web support). Record all detected platforms — specialists will receive this classification.

### 2. Tech stack identification

Per detected platform:

- **Web:** Frameworks (React, Vue, Angular, Svelte, Next.js, etc.), CSS approach (Tailwind, CSS Modules, styled-components, etc.), component libraries (MUI, Radix, Headless UI, Bootstrap — note built-in a11y support)
- **iOS:** SwiftUI vs UIKit vs mixed, any a11y wrapper libraries
- **Android:** Jetpack Compose vs View system vs mixed, any a11y libraries
- **React Native:** version, any a11y libraries (e.g., `react-native-a11y`)
- **Flutter:** version, any a11y packages
- **Desktop:** framework and toolkit
- **CLI:** argument parser, output formatting library, terminal UI library (if any)
- **Game:** engine, UI system (in-engine UI, HTML overlay, custom)

### 3. Inventory user-facing code

Collect all files that produce user-facing output or handle user interaction, grouped by platform.

### 4. Check for existing a11y tooling

- **Web:** `eslint-plugin-jsx-a11y`, `eslint-plugin-vuejs-accessibility`, `axe-core`, `pa11y`, Lighthouse configs
- **iOS:** Accessibility Inspector usage, XCTest accessibility tests
- **Android:** Accessibility Scanner, Espresso accessibility checks, `AccessibilityChecks.enable()`
- **React Native:** `@testing-library/react-native` accessibility queries
- **Flutter:** `SemanticsDebugger`, accessibility-related widget tests
- **CLI:** structured output tests, `--no-color` support tests
- **Game:** accessibility options menu, remapping tests
- **CI:** any automated a11y checks in CI pipeline
- Note what's present — specialists should not re-flag issues that existing tooling already catches, unless the tooling is misconfigured or findings are suppressed

### 5. Scan for steering files

`CLAUDE.md`, `AGENTS.md`, any a11y-specific documentation or guidelines.

### 6. Estimate scope size

- **Small:** <20 user-facing files
- **Medium:** 20-100 user-facing files
- **Large:** 100+ user-facing files

### 7. Build manifest

Files to audit, grouped for specialists, annotated with detected platform(s).

**Steering file caveat:** Include in every agent prompt: "Steering files (CLAUDE.md, etc.) describe conventions but may be stale. If you find a contradiction between steering files and actual code, flag it as a finding."

## Phase 2: Specialist Audit (Parallel)

Dispatch these agents simultaneously using the Agent tool with `subagent_type: paad:paad-analyst`. Each receives: the file manifest, detected platform(s), steering file contents, existing a11y tooling notes, and their specialist focus.

### Core specialists (always dispatched)

| Agent | Focus | Who it helps |
|-------|-------|-------------|
| **Screen Reader & Assistive Tech** | Programmatic exposure of UI semantics so assistive technologies can convey structure, content, and state to users | Blind and low-vision users using screen readers (VoiceOver, TalkBack, NVDA, JAWS, Orca) |
| **Visual & Color** | Sufficient contrast, independence from color alone, support for magnification/text scaling, visible focus/selection indicators | Low-vision users, colorblind users |
| **Keyboard & Motor** | Complete operability without fine motor control — keyboard, switch, sip-and-puff, eye tracking, voice control — with adequate target sizes and no traps | Motor-impaired users, switch access users, sip-and-puff users, voice control users |
| **Cognitive & Learning** | Consistent, predictable interfaces with clear feedback, error recovery, plain language, and no unnecessary cognitive load | Users with cognitive disabilities, learning disabilities, attention disorders, memory impairments |
| **Multimedia & Temporal** | Alternatives for audio/visual content, safe motion/animation, adequate time, no seizure triggers | Deaf/hard-of-hearing users, vestibular disorders, photosensitive epilepsy, users who need more time |

### Conditional specialist

Dispatch using the Agent tool with `subagent_type: paad:paad-analyst`, exactly as for the core specialists, when the platform has framework-specific a11y pitfalls (web frameworks, SwiftUI, Compose, Flutter, React Native, game engines):

| Agent | Focus | Input |
|-------|-------|-------|
| **Platform-Specific Patterns** | Framework/platform-specific a11y pitfalls, misuse of platform a11y APIs, navigation/routing a11y, dynamic content patterns | File manifest + platform/framework detection results |

### Agent prompt template

Each specialist agent prompt must include:
- The list of files to audit (from their manifest group)
- Contents of files in their audit scope
- The detected platform(s)
- Steering file contents with the staleness caveat
- Existing a11y tooling notes
- Instruction: "You are an accessibility specialist focused on [FOCUS AREA]. The detected platform(s) for this project: [PLATFORMS]. Your goal is to find accessibility barriers that affect [USER GROUP]. For each finding report: file:line, what's wrong, which accessibility criterion it violates (WCAG 2.2 criterion where applicable, or platform-specific guideline), the conformance level (A/AA/AAA), who is affected and how, a concrete code-level fix, and your confidence (0-100). Only report findings with confidence >= 60. Do not modify any file in the repository. You may run read-only commands (existing tests, linters, type checkers) unchanged — their caches and build output are fine. If confirming a finding would require changing code, do not — cap that finding's confidence at 79 and state what would confirm it."

### Platform-specific checks per specialist

Include the relevant platform section(s) in each specialist's prompt based on detected platform(s).

#### Screen Reader & Assistive Tech

**Web:** (1) Correct ARIA roles, states, and properties on custom components; (2) semantic HTML (headings, landmarks, lists, tables) over generic `div`/`span`; (3) heading hierarchy without skipped levels; (4) meaningful alt text (not filenames or "image"); (5) programmatically associated form labels; (6) `aria-live` regions for dynamic content; (7) link/button purpose clear from text or accessible name; (8) status messages via `role="status"` or `aria-live`.

**iOS:** (1) `accessibilityLabel` set on all interactive and meaningful elements; (2) `accessibilityTraits` / SwiftUI `.accessibilityAddTraits()` correctly applied (`.button`, `.header`, `.image`, etc.); (3) `accessibilityHint` for non-obvious actions; (4) `isAccessibilityElement` grouping — containers group related info, decorative elements excluded; (5) `accessibilityValue` for sliders/progress; (6) `UIAccessibility.post(.screenChanged, ...)` and `.layoutChanged` notifications for dynamic updates; (7) custom actions via `accessibilityCustomActions`; (8) SwiftUI: `.accessibilityElement(children: .combine)` for logical grouping.

**Android:** (1) `contentDescription` on all interactive and meaningful elements; (2) `importantForAccessibility` set correctly — decorative elements marked `no`; (3) `labelFor` connecting labels to inputs; (4) `accessibilityLiveRegion` for dynamic content; (5) `accessibilityHeading` on section headers; (6) Compose: `semantics { }` block with appropriate properties, `contentDescription`, `heading()`, `stateDescription`; (7) custom `AccessibilityNodeInfo` actions where needed; (8) `ViewCompat.setAccessibilityDelegate` for custom views.

**React Native:** (1) `accessibilityLabel` on all interactive elements; (2) `accessibilityRole` set correctly (`button`, `header`, `link`, `image`, etc.); (3) `accessibilityState` for toggles, disabled, expanded states; (4) `accessibilityHint` for non-obvious actions; (5) `accessibilityLiveRegion` for dynamic updates; (6) `accessibilityElementsHidden` for decorative content; (7) `AccessibilityInfo.announceForAccessibility()` for dynamic state changes.

**Flutter:** (1) `Semantics` widget wrapping meaningful UI with `label`, `button`, `header`, `image` properties; (2) `excludeSemantics: true` on decorative elements; (3) `MergeSemantics` for logically grouped content; (4) `SemanticsService.announce()` for dynamic updates; (5) `tooltip` properties on `IconButton` and similar; (6) `semanticsLabel` on `Text` where displayed text differs from meaning.

**CLI:** (1) Structured, parseable output (not just visual formatting with boxes/lines); (2) information not conveyed solely by position/layout — screen readers linearize output; (3) progress indication via text updates, not just spinners or progress bars that rely on cursor repositioning; (4) error messages written to stderr with clear text (not just color/emoji).

**Game:** (1) UI elements have text alternatives available for screen reader narration mode; (2) menu items narrated with name, type, and state; (3) game state changes announced; (4) narration option in settings if not always-on.

#### Visual & Color

**Web:** Contrast ratios — AA: 4.5:1 normal text, 3:1 large text (18pt+/14pt+ bold), 3:1 UI components and graphics. AAA: 7:1/4.5:1. Check CSS custom properties and theme values. Flag color-only meaning (error states, status indicators, required fields, links distinguished only by color). Reflow at 320px width. Text spacing override support. `prefers-contrast` media query support.

**iOS:** (1) Dynamic Type support (`UIFontMetrics`, SwiftUI `.dynamicTypeSize`), test with all type sizes including accessibility sizes; (2) Bold Text support (`UIAccessibility.isBoldTextEnabled`); (3) Increase Contrast (`UIAccessibility.isDarkerSystemColorsEnabled`); (4) Reduce Transparency support; (5) sufficient contrast ratios in custom themes (same ratios as web); (6) color-only information has shape/icon/text alternatives; (7) SF Symbols accessibility variants.

**Android:** (1) `sp` units for text (scales with user preference); (2) test at 200% font scale; (3) High Contrast Text setting support; (4) sufficient contrast in custom themes; (5) color-only meaning has alternatives; (6) Magnification gesture compatibility (no content hidden at 200%+ zoom); (7) custom views render correctly with font scaling.

**React Native:** (1) Font scaling support — not disabled via `allowFontScaling={false}` unless justified; (2) layout accommodates scaled text without overflow/truncation; (3) contrast ratios on all custom-themed elements; (4) color-only meaning has alternatives.

**Flutter:** (1) `MediaQuery.textScaleFactorOf(context)` respected — UI tested at 2.0 scale; (2) contrast ratios met in custom `ThemeData`; (3) color-only meaning has alternatives; (4) `MediaQuery.boldTextOf(context)` support; (5) `MediaQuery.highContrastOf(context)` support.

**CLI:** (1) `--no-color` flag or `NO_COLOR` env var support; (2) information not conveyed by color alone — use labels, prefixes, symbols alongside color (e.g., `[ERROR]` not just red text); (3) supports `TERM` detection for capability; (4) works in high-contrast terminal themes.

**Game:** (1) Colorblind mode(s) — at minimum deuteranopia (red-green), ideally also protanopia and tritanopia; (2) UI element outlines/patterns supplement color; (3) font size options or UI scaling; (4) high contrast UI option; (5) brightness/gamma controls; (6) important game elements distinguishable by shape, not just color.

#### Keyboard & Motor

**Web:** (1) Every interactive element reachable and activatable via keyboard; (2) no keyboard traps (focus can escape every modal, dropdown, overlay); (3) logical focus order matching visual layout; (4) visible focus indicators (not suppressed by `outline: none` without replacement); (5) skip navigation links; (6) custom widgets follow WAI-ARIA Authoring Practices keyboard patterns; (7) click targets at least 24x24 CSS px (AA), recommend 44x44 (AAA); (8) drag-and-drop has click/keyboard alternative; (9) single-character shortcuts remappable or only active on focus; (10) `pointer-events`, `user-select` not disabling expected interactions.

**iOS:** (1) Full Keyboard Access support — all actions reachable via external keyboard; (2) Switch Control compatibility — all interactive elements in accessibility tree with correct order; (3) AssistiveTouch custom gesture alternatives for complex gestures; (4) minimum 44x44pt tap targets (Apple HIG); (5) no gesture-only actions without alternatives (e.g., swipe-to-delete must have edit button); (6) custom gesture recognizers don't block Switch Control; (7) `accessibilityActivationPoint` set for non-standard hit areas.

**Android:** (1) Full keyboard navigation — `android:focusable`, logical `nextFocusDown/Up/Left/Right`; (2) Switch Access compatibility — all interactive elements focusable with adequate ordering; (3) minimum 48x48dp touch targets (Material Design); (4) no gesture-only actions without alternatives; (5) `android:importantForAccessibility` not hiding interactive elements; (6) custom views implement `onKeyDown`/`onKeyUp` for keyboard users; (7) TalkBack gesture alternatives for complex interactions.

**React Native:** (1) `accessible={true}` on all interactive elements; (2) `accessibilityActions` for custom actions; (3) `onMagicTap`, `onEscape` handlers where appropriate (iOS); (4) minimum touch target sizes (48x48dp Android / 44x44pt iOS); (5) gesture-based interactions have tap alternatives.

**Flutter:** (1) All interactive widgets have `Semantics` with tap/long press actions; (2) minimum touch targets via `MaterialTapTargetSize.padded`; (3) `FocusNode` and `FocusTraversalGroup` for logical keyboard order; (4) `RawKeyboardListener`/`KeyboardListener` for keyboard shortcuts; (5) no `IgnorePointer`/`AbsorbPointer` hiding accessible interactions; (6) custom `GestureDetector` actions have keyboard alternatives.

**CLI:** (1) Keyboard-only by nature, but check: interactive prompts (e.g., fuzzy finders, multi-select) navigable with arrow keys and enter; (2) Ctrl-C always exits; (3) no mouse-only interactions in TUI; (4) tab completion where appropriate; (5) long-running operations cancellable via keyboard.

**Game:** (1) Fully remappable controls; (2) multiple input device support (keyboard, mouse, controller, touch); (3) one-handed mode or alternative layouts; (4) no quick-time events without alternatives or adjustable timing; (5) auto-aim/aim assist option; (6) adjustable input sensitivity/dead zones; (7) hold-vs-toggle options for sustained inputs; (8) copilot/co-pilot mode if multiplayer.

#### Cognitive & Learning

**All platforms:** (1) Consistent navigation patterns across screens/pages; (2) consistent identification of common elements; (3) clear error messages identifying the problem and suggesting a fix; (4) labels and instructions on all form inputs; (5) predictable behavior — no unexpected context changes on focus or input; (6) adequate time — adjustable/extendable timeouts, warnings before expiry; (7) help in a consistent, findable location; (8) no unnecessary re-entry of previously provided information; (9) accessible authentication — no cognitive function tests (CAPTCHAs) without alternatives.

**Web additionally:** (1) `lang` attribute on `<html>` and `lang` attributes on content in other languages; (2) multiple ways to find pages (nav, search, sitemap); (3) breadcrumbs or location indicator.

**iOS/Android additionally:** (1) Back navigation always works predictably; (2) undo support for destructive actions; (3) confirmation dialogs for irreversible operations.

**CLI additionally:** (1) `--help` with clear, complete documentation; (2) confirmation prompts for destructive commands (with `--yes`/`-y` to skip); (3) meaningful exit codes; (4) consistent flag naming conventions (e.g., `--verbose` not `-v` in one command and `--debug` in another).

**Game additionally:** (1) Tutorial or onboarding; (2) difficulty options including easy/story mode; (3) objective tracking/quest log; (4) adjustable game speed; (5) pause in single-player; (6) clear visual/audio feedback for actions; (7) option to simplify UI.

#### Multimedia & Temporal

**All platforms:** (1) Pre-recorded video has captions; (2) pre-recorded audio has transcript; (3) no content flashes more than 3 times per second; (4) auto-playing media has pause/stop control; (5) moving/blinking/scrolling content can be paused; (6) no time limits, or limits are adjustable/extendable with warning.

**Web additionally:** `prefers-reduced-motion` media query respected — all CSS animations/transitions have reduced or disabled alternatives. Audio descriptions for pre-recorded video (AA). `<video>`/`<audio>` elements have controls. No `autoplay` without mute.

**iOS additionally:** `UIAccessibility.isReduceMotionEnabled` / SwiftUI `.accessibilityReduceMotion` checked and respected — simplify or remove animations. `UIAccessibility.isVideoAutoplayEnabled` respected.

**Android additionally:** `Settings.Global.ANIMATOR_DURATION_SCALE` respected (set to 0 disables animations). `View.IMPORTANT_FOR_AUTOFILL` for form timing.

**React Native additionally:** `AccessibilityInfo.isReduceMotionEnabled()` checked — `Animated` and `LayoutAnimation` respect user preference.

**Flutter additionally:** `MediaQuery.disableAnimationsOf(context)` or `MediaQuery.reduceMotionOf(context)` checked and respected.

**CLI additionally:** No seizure-inducing rapid terminal updates (e.g., fast flickering progress bars). Long-running operations show progress without rapid screen clearing.

**Game additionally:** (1) Subtitle options with size/background/speaker-identification controls; (2) visual indicators for important audio cues (directional indicators, closed captions for sound effects); (3) screen shake toggle; (4) motion blur toggle; (5) field-of-view slider (reduces motion sickness); (6) photosensitivity mode reducing flashes/strobe effects.

### Platform-Specific Patterns agent (conditional)

Include relevant examples:

**React:** `key` on lists affecting screen readers, missing `aria-live` on state changes, portal focus traps, `onClick` on non-interactive elements without role/keyboard handling.

**Vue:** `v-html` with no a11y review, missing `aria` bindings on dynamic attributes, router `afterEach` not announcing navigation.

**Angular:** `cdkTrapFocus` misconfiguration, `aria-describedby` with `*ngIf` removing referenced elements.

**Svelte:** Reactive declarations removing focus targets, `use:action` without a11y side effects.

**SwiftUI:** `.accessibilityRepresentation` missing on custom controls, `@AccessibilityFocusState` not managing focus on navigation, `.accessibilityRotor` not used for long content, List/ForEach not providing per-item actions.

**Jetpack Compose:** `Modifier.semantics` not applied to custom composables, `LazyColumn` items missing individual semantics, `AlertDialog` not moving focus on show, `ModalBottomSheet` not trapping focus, `clickable` without `role` parameter.

**Flutter:** `CustomPainter` without `SemanticsBuilder`, `Navigator` transitions not announcing new routes, `Hero` animations conflicting with semantics, `PlatformView` breaking a11y tree.

**React Native:** `FlatList`/`SectionList` items not individually accessible, `Modal` not managing focus, platform-specific props missing (`accessibilityLanguage` iOS only, `accessibilityLiveRegion` Android emphasis).

**Game engines (Unity):** UI Toolkit vs UGUI a11y gaps, `EventSystem` not handling keyboard/controller navigation, `TextMeshPro` not exposing text to accessibility APIs.

**Scaling for large scope (100+ files):** Partition files across 2 instances of each specialist.

## Phase 3: Verification

After all specialists complete, dispatch a single **Verifier** agent using the Agent tool with `subagent_type: paad:paad-analyst`, passing all findings. The verifier:

1. For each finding, reads the actual current code at the referenced file:line
2. Confirms the accessibility barrier exists and isn't handled elsewhere (e.g., by a parent component, a platform API, a framework feature, a component library, or a system-level setting)
3. Drops false positives and findings below 60% confidence
4. Confirms the correct accessibility criterion is cited
5. Assigns severity:
   - **Critical** — Complete barrier: users with the affected disability cannot use this feature at all
   - **Serious** — Major difficulty: the feature is usable but with significant hardship or workarounds
   - **Moderate** — Friction: causes confusion or extra effort but does not block task completion
   - **Minor** — Best practice improvement or AAA enhancement
6. Deduplicates findings flagged by multiple specialists (note which specialists agreed — cross-specialist agreement increases confidence)

**Verifier prompt must include:** "You are verifying accessibility findings. For each finding, read the actual code and confirm the barrier exists. Be skeptical — the platform, framework, or component library may already handle accessibility automatically. On iOS, UIKit provides some accessibility by default for standard controls. On Android, standard Material components include accessibility support. A finding reported by multiple specialists is more likely real. Ensure the cited criterion is correct. Do not modify any file in the repository. You may run read-only commands (existing tests, linters, type checkers) unchanged — their caches and build output are fine. If confirming a finding would require changing code, do not — treat the barrier as unconfirmed and drop it as you would any other false positive, rather than lowering the finding's confidence or severity."

## Phase 4: Report

Write verified findings to `paad/a11y-reviews/a11y-<YYYY-MM-DD-HH-MM-SS>.md`.

Create the `paad/a11y-reviews/` directory if it doesn't exist.

**Report template:**

```markdown
# Accessibility Audit: <project-name>

**Date:** YYYY-MM-DD HH:MM:SS
**Commit:** <full-sha>
**Platform(s):** <detected platforms>
**Tech stack:** <frameworks, libraries, engines>
**Files audited:** N
**Existing a11y tooling:** <list or "none found">
**Conformance target:** WCAG 2.2 AA via WCAG2ICT (AAA noted as recommendations)
**Platform guidelines referenced:** <e.g., Apple HIG Accessibility, Material Design Accessibility, Xbox Accessibility Guidelines, or "N/A">

## Executive Summary

2-3 sentences: overall accessibility posture, highest-severity findings, estimated conformance level (A / partial AA / AA / partial AAA).

## Impact Summary by User Group

Brief summary of how the codebase affects each group:
- **Screen reader users:** <1-2 sentences>
- **Low-vision users:** <1-2 sentences>
- **Colorblind users:** <1-2 sentences>
- **Motor-impaired users (keyboard/switch/sip-and-puff):** <1-2 sentences>
- **Cognitive and learning disabilities:** <1-2 sentences>
- **Deaf and hard-of-hearing users:** <1-2 sentences>
- **Vestibular and photosensitive users:** <1-2 sentences>

## Critical Issues (Complete Barriers)

### [C1] <title>
- **File:** `path/to/file:line`
- **Platform:** <which platform this applies to>
- **Barrier:** What's wrong
- **Criterion:** <WCAG criterion or platform guideline> — Level <A/AA>
- **Affects:** Who is blocked and how
- **Fix:** Concrete code-level recommendation
- **Confidence:** High/Medium
- **Found by:** <specialist name(s)>

(Repeat for each critical issue, or "None found.")

## Serious Issues (Major Difficulty)

(Same structure as Critical, or "None found.")

## Moderate Issues (Friction)

(Same structure, or "None found.")

## Minor Issues & AAA Recommendations

One-line entries with criterion reference. Omit section if none.
Mark AAA items with [AAA] prefix.

## Conformance Checklist

For each WCAG principle, list criteria checked and their status. For non-web platforms, criteria are interpreted via WCAG2ICT. Mark criteria that do not apply to the detected platform as "N/A" with brief explanation.

### Perceivable
| Criterion | Level | Status | Finding |
|-----------|-------|--------|---------|
| 1.1.1 Non-text Content | A | Pass / Fail / Partial / N/A / Not assessed | #ID or — |
(continue for all Perceivable criteria assessed)

### Operable
(same table format)

### Understandable
(same table format)

### Robust
(same table format)

### Platform-Specific Guidelines
| Guideline | Status | Finding |
|-----------|--------|---------|
| <e.g., Apple HIG: Dynamic Type> | Pass / Fail / Partial | #ID or — |
(list platform-specific guidelines checked beyond WCAG, or omit section if web-only)

## Quick Wins

Top 5 fixes that would have the largest positive impact for the least effort. Each entry: what to fix, which findings it addresses, estimated effort (small/medium/large).

## Audit Metadata

- **Agents dispatched:** <list with focus areas>
- **Platform(s) detected:** <list>
- **Scope:** <files audited>
- **Raw findings:** N (before verification)
- **Verified findings:** M (after verification)
- **Filtered out:** N - M
- **By severity:** X critical, Y serious, Z moderate, W minor
- **By conformance level:** X Level A, Y Level AA, Z Level AAA
- **Steering files consulted:** <list or "none found">
- **Existing a11y tooling:** <list or "none found">
```

## Common Mistakes

These patterns produce low-quality audits. Avoid them:

| Mistake | What to do instead |
|---------|-------------------|
| Single-agent audit | Always dispatch 5+ specialist agents in parallel via Agent tool — each disability has unique concerns that a generalist misses |
| Skipping verification | Always run verifier — platforms and component libraries handle many a11y patterns automatically, producing false positives without verification |
| Assuming web platform | Detect the actual platform(s) first — iOS, Android, Flutter, CLI, and games all have different a11y APIs and patterns |
| Flagging issues handled by platform defaults | Standard UIKit controls, Material components, and Flutter widgets have built-in a11y — only flag if misused, overridden, or missing |
| Generic findings without file:line | Every finding must reference exact code location — "add alt text" or "add contentDescription" is not actionable |
| Wrong criteria | Verify the correct WCAG criterion or platform guideline is cited — misattribution erodes trust in the report |
| Ignoring styling/theming | Many a11y issues live in styles (contrast, focus indicators, text sizing, elements hidden from assistive tech) regardless of platform |
| Only checking static/declarative UI | Dynamic content, navigation transitions, and programmatic UI changes are where the hardest a11y bugs hide on every platform |
| Treating AAA as required | AAA items are recommendations, not failures — present them as enhancements to avoid overwhelming teams |
| Ignoring reduced-motion preferences | Every platform has a reduce-motion setting — `prefers-reduced-motion` (web/CSS), `isReduceMotionEnabled` (iOS), `ANIMATOR_DURATION_SCALE` (Android), `disableAnimations` (Flutter) — vestibular disorders cause real physical symptoms |
| Applying web patterns to native | ARIA is a web technology. Native platforms have their own accessibility APIs — don't recommend ARIA attributes for iOS/Android code |
| Ignoring CLI accessibility | CLI tools are user-facing too — color-only output, unstructured text, and missing `--no-color` support are real barriers |

## Post-Audit

After writing the report:
1. Tell the user the report location and finding counts by severity
2. Tell them: "To address these findings, work through the Quick Wins first, then tackle Critical and Serious issues. Fix each issue with a per-fix commit. If you have the [superpowers](https://github.com/obra/superpowers/) plugin installed, you can use the `receiving-code-review` skill and point it at this report for a guided workflow."
3. Do **not** auto-fix anything. The report is the deliverable.
