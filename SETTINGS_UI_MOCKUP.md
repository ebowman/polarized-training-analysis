# Settings Page UI Mockup Specification

## Visual Design Guidelines

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ PolarFlow Settings                                      [X Close]│
├─────────────────┬───────────────────────────────────────────────┤
│                 │                                                 │
│  ⚙️ General      │  General Settings                             │
│                 │  ─────────────────────────                     │
│  🚴 Sports      │                                                 │
│                 │  Strava Configuration                           │
│  🤖 AI Providers│  ┌─────────────────────────────────────────┐   │
│                 │  │ Client ID:     [167076...............]   │   │
│  📝 Prompts     │  │ Client Secret: [••••••••••••••••fde0]   │   │
│                 │  └─────────────────────────────────────────┘   │
│  🔧 Advanced    │                                                 │
│                 │  Training Metrics                               │
│                 │  ┌─────────────────────────────────────────┐   │
│                 │  │ Max Heart Rate: [171] bpm                │   │
│                 │  │ FTP:            [301] watts              │   │
│                 │  │ LTHR:           [153] bpm                │   │
│                 │  └─────────────────────────────────────────┘   │
│                 │                                                 │
├─────────────────┴───────────────────────────────────────────────┤
│ [💾 Save Changes]  [↩️ Reset]  [📥 Export]  Status: ✅ Saved     │
└─────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Navigation Sidebar (Left Panel)
- **Width**: 200px fixed
- **Background**: Light gray (#f5f5f5)
- **Items**:
  - Icon + Label format
  - Active state: Blue background (#007bff), white text
  - Hover state: Light blue background (#e3f2fd)
  - Padding: 12px 16px per item

#### 2. Content Area (Right Panel)
- **Padding**: 24px
- **Max width**: 800px (centered in larger screens)
- **Section headers**: 
  - Font size: 24px
  - Bottom border: 2px solid #e0e0e0
  - Margin bottom: 20px

#### 3. Form Controls

##### Input Fields
```
┌─────────────────────────────────────┐
│ Label Text                          │
│ ┌─────────────────────────────────┐ │
│ │ Input value here                │ │
│ └─────────────────────────────────┘ │
│ Helper text or validation message   │
└─────────────────────────────────────┘
```
- Border: 1px solid #ccc
- Focus: Blue border (#007bff)
- Error: Red border (#dc3545)
- Padding: 8px 12px

##### API Key Fields
```
┌─────────────────────────────────────┐
│ OpenAI API Key                      │
│ ┌─────────────────────────────┐👁️  │
│ │ ••••••••••••••••••••••FJ3zL│    │
│ └─────────────────────────────┘    │
│ ✅ Valid API key                    │
└─────────────────────────────────────┘
```
- Masked by default
- Toggle visibility button
- Validation indicator

### Section-Specific Designs

#### General Settings
```
General Settings
────────────────

Strava API Configuration
┌──────────────────────────────────────────────┐
│ Client ID      [___________________________] │
│ Client Secret  [•••••••••••••••••••••] 👁️    │
│                                              │
│ [🔗 Get Strava API Credentials]              │
└──────────────────────────────────────────────┘

Training Zones Configuration  
┌──────────────────────────────────────────────┐
│ Max Heart Rate    [___] bpm    ❓            │
│ FTP               [___] watts  ❓            │
│ LTHR              [___] bpm    ❓            │
│                                              │
│ 📊 FTP Test Data (Optional)                  │
│ ├─ Average HR:    [___] bpm                 │
│ ├─ Max HR:        [___] bpm                 │
│ └─ Average Power: [___] watts               │
└──────────────────────────────────────────────┘
```

#### Sports Configuration
```
Sports Configuration
────────────────────

┌─ Sport Selector ─────────────────────────────┐
│ [🚴 Cycling ▼] [➕ Add Sport]                │
└──────────────────────────────────────────────┘

Zone Configuration
┌──────────────────────────────────────────────┐
│ Zone Model: [Percentage-based ▼]            │
│                                              │
│ Power Zones                                  │
│ ┌────────────┬─────────┬─────────┬────────┐ │
│ │ Zone Name  │ Lower % │ Upper % │ Polar  │ │
│ ├────────────┼─────────┼─────────┼────────┤ │
│ │ Recovery   │ 0       │ 55      │ Zone 1 │ │
│ │ Endurance  │ 56      │ 75      │ Zone 1 │ │
│ │ Tempo      │ 76      │ 90      │ Zone 2 │ │
│ │ Threshold  │ 91      │ 105     │ Zone 2 │ │
│ │ VO2 Max    │ 106     │ 120     │ Zone 3 │ │
│ └────────────┴─────────┴─────────┴────────┘ │
│                                              │
│ [➕ Add Zone] [📊 Preview Zones]             │
└──────────────────────────────────────────────┘
```

#### AI Providers
```
AI Provider Configuration
─────────────────────────

Provider Selection
┌──────────────────────────────────────────────┐
│ AI Provider Mode: [Auto (with fallback) ▼]  │
│                                              │
│ ┌─ Primary Provider ────────────────────┐   │
│ │ [OpenAI ▼]                            │   │
│ │ API Key: [••••••••••••••••••FJ3zL] 👁️ │   │
│ │ Status: ✅ Connected                   │   │
│ │ [Test Connection]                      │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ ┌─ Fallback Provider ───────────────────┐   │
│ │ [Claude/Anthropic ▼]                  │   │
│ │ API Key: [••••••••••••••••••GQAA] 👁️  │   │
│ │ Status: ✅ Connected                   │   │
│ │ [Test Connection]                      │   │
│ └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

#### Prompt Templates
```
Prompt Template Management
──────────────────────────

┌─ Template List ──────────────────────────────┐
│ 📄 Main Analysis Prompt         [Edit] [⬇️]  │
│ 📄 Recovery Recommendations     [Edit] [⬇️]  │
│ 📄 Workout Planning             [Edit] [⬇️]  │
│                                              │
│ [➕ New Template] [📤 Import]                │
└──────────────────────────────────────────────┘

Template Editor
┌──────────────────────────────────────────────┐
│ Template Name: [Main Analysis Prompt_____]   │
│                                              │
│ ┌─ Variables ────────────────────────────┐   │
│ │ {{sport}} - Current sport              │   │
│ │ {{volume}} - Training volume           │   │
│ │ {{zones}} - Zone distribution          │   │
│ │ [➕ Add Variable]                       │   │
│ └─────────────────────────────────────────┘   │
│                                              │
│ Template Content:                            │
│ ┌─────────────────────────────────────────┐  │
│ │ Analyze the training data for           │  │
│ │ {{sport}} with a focus on polarized    │  │
│ │ training distribution...                │  │
│ │                                         │  │
│ │                                         │  │
│ └─────────────────────────────────────────┘  │
│                                              │
│ [📋 Copy] [👁️ Preview] [💾 Save Template]    │
└──────────────────────────────────────────────┘
```

### Color Palette
- **Primary Blue**: #007bff
- **Success Green**: #28a745
- **Warning Yellow**: #ffc107
- **Danger Red**: #dc3545
- **Light Gray**: #f5f5f5
- **Border Gray**: #dee2e6
- **Text Primary**: #212529
- **Text Secondary**: #6c757d

### Typography
- **Headers**: Inter or system font, 600 weight
- **Body**: Inter or system font, 400 weight
- **Monospace**: 'Courier New' or 'Monaco' for JSON/code

### Interactive Elements

#### Buttons
- **Primary**: Blue background, white text, 4px radius
- **Secondary**: White background, gray border, 4px radius
- **Hover**: Darken background by 10%
- **Active**: Darken background by 20%
- **Disabled**: Gray background, reduced opacity

#### Tooltips
- Show on hover over ❓ icons
- Dark background with white text
- Arrow pointing to trigger element

#### Validation States
- **Valid**: Green checkmark ✅
- **Invalid**: Red X ❌
- **Warning**: Yellow triangle ⚠️
- **Loading**: Spinning circle ⏳

### Responsive Behavior
- **Desktop (>1200px)**: Full layout as shown
- **Tablet (768-1200px)**: Collapsible sidebar
- **Mobile (<768px)**: 
  - Top navigation instead of sidebar
  - Full-width content
  - Stacked form fields

### Animation Guidelines
- **Transitions**: 200ms ease-in-out
- **Loading states**: Pulse animation
- **Success feedback**: Brief green flash
- **Error feedback**: Shake animation

### Accessibility Requirements
- All form inputs must have labels
- Focus indicators on all interactive elements
- ARIA labels for icon buttons
- Keyboard navigation support
- Screen reader friendly structure