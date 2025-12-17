# Dashboard Layout System

A comprehensive layout system for building consistent dashboard pages with minimal boilerplate.

## Components Overview

### 🎯 DashboardLayout (Recommended)
**The all-in-one solution** - Use this for all your dashboard pages!

Combines `TopBar` + `DashboardWrapper` into a single component.

```tsx
import DashboardLayout from '@/components/DashboardLayout';

function MyPage() {
  return (
    <DashboardLayout>
      <h1>My Page Title</h1>
      {/* Your page content */}
    </DashboardLayout>
  );
}
```

### 🔧 Individual Components

If you need more control, you can use these components separately:

#### TopBar
Navigation bar with logo, chat toggle, and user menu.

```tsx
import TopBar from '@/components/TopBar';
<TopBar />
```

#### DashboardWrapper
Handles dynamic width based on chat state.

```tsx
import DashboardWrapper from '@/components/DashboardWrapper';
<DashboardWrapper>
  {/* Content */}
</DashboardWrapper>
```

#### ChatPanel
The sliding chat interface (already included in App.tsx).

#### ChatToggleButton
Button to toggle chat (already in TopBar).

## Quick Start

### For New Pages

```tsx
import DashboardLayout from '@/components/DashboardLayout';

export default function MyDashboard() {
  return (
    <DashboardLayout>
      {/* Just add your content here! */}
      <h1>Dashboard Title</h1>
      <div>Your content...</div>
    </DashboardLayout>
  );
}
```

### With Custom Styling

```tsx
<DashboardLayout 
  className="bg-gradient-to-br from-blue-50 to-purple-50"
  containerClassName="max-w-7xl"
>
  {/* Content */}
</DashboardLayout>
```

## Features

✅ **Automatic Chat Integration** - Width adjusts when chat opens/closes  
✅ **Consistent Navigation** - TopBar included automatically  
✅ **Smooth Transitions** - Professional animations  
✅ **Customizable** - Pass className for styling  
✅ **Type Safe** - Full TypeScript support  

## Props

### DashboardLayout Props

| Prop | Type | Description | Default |
|------|------|-------------|---------|
| `children` | ReactNode | Page content | Required |
| `className` | string | Custom classes for wrapper | - |
| `containerClassName` | string | Custom classes for container | - |

## Architecture

```
DashboardLayout
├── TopBar
│   ├── Logo (AICOE)
│   ├── ChatToggleButton
│   └── User Dropdown Menu
└── DashboardWrapper
    └── {children} (Your Content)
```

## Chat System

The chat system is integrated globally:

- **ChatContext**: Global state for chat open/close
- **ChatPanel**: Fixed panel that slides in from right (400px)
- **ChatToggleButton**: In TopBar to toggle visibility
- **Dynamic Width**: Dashboard automatically adjusts when chat opens

### Chat State

Access chat state anywhere:

```tsx
import { useChatContext } from '@/contexts/ChatContext';

function MyComponent() {
  const { isChatOpen, toggleChat, openChat, closeChat } = useChatContext();
  
  return <button onClick={toggleChat}>Toggle Chat</button>;
}
```

## Example: Complete Page

```tsx
import { useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import { Button } from '@/components/ui/button';

export default function ExamplePage() {
  const [data, setData] = useState([]);

  return (
    <DashboardLayout>
      {/* Page Title */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">My Dashboard</h1>
      </div>

      {/* Page Content */}
      <div className="space-y-4">
        {/* Your components here */}
      </div>
    </DashboardLayout>
  );
}
```

## Best Practices

1. **Always use DashboardLayout** for consistency
2. **Keep layout logic in components** - Don't repeat TopBar/wrapper code
3. **Use className props** for custom styling
4. **Leverage chat context** for integrated features

## Migration Guide

If you have existing pages with separate TopBar and DashboardWrapper:

**Before:**
```tsx
<>
  <TopBar />
  <DashboardWrapper>
    {/* content */}
  </DashboardWrapper>
</>
```

**After:**
```tsx
<DashboardLayout>
  {/* content */}
</DashboardLayout>
```

## See Also

- `src/pages/Grants.tsx` - Complete example implementation
- `src/components/TopBar.tsx` - Navigation bar source
- `src/components/DashboardWrapper.tsx` - Wrapper source
- `src/contexts/ChatContext.tsx` - Chat state management
