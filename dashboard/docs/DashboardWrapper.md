# DashboardWrapper Component

A flexible wrapper component that handles dynamic width adjustments based on the chat panel state.

## Features

- **Dynamic Width**: Automatically adjusts dashboard width when chat panel opens/closes
- **Smooth Transitions**: CSS transitions for seamless visual experience
- **Customizable Background**: Pass custom className for background styling
- **Global State**: Uses ChatContext for state management across the app

## Usage

### Basic Usage

```tsx
import DashboardWrapper from '@/components/DashboardWrapper';

function MyDashboard() {
  return (
    <DashboardWrapper>
      <h1>My Dashboard Content</h1>
      {/* Your dashboard content here */}
    </DashboardWrapper>
  );
}
```

### With Custom Background

```tsx
<DashboardWrapper className="bg-gradient-to-br from-blue-50 to-purple-50">
  {/* Content */}
</DashboardWrapper>
```

### With Custom Container Styling

```tsx
<DashboardWrapper containerClassName="max-w-7xl">
  {/* Content */}
</DashboardWrapper>
```

## How It Works

1. The wrapper listens to the `ChatContext` for the `isChatOpen` state
2. When chat is closed: Full width (`mr-0`)
3. When chat is open: Right margin of 400px (`mr-[400px]`) to make room for the chat panel
4. Uses CSS transitions for smooth width changes

## Related Components

- **ChatPanel**: The sliding chat interface
- **ChatToggleButton**: Button to toggle chat visibility
- **ChatContext**: Global state management for chat

## Props

| Prop | Type | Description | Default |
|------|------|-------------|---------|
| `children` | ReactNode | Dashboard content | Required |
| `className` | string | Custom classes for outer wrapper | - |
| `containerClassName` | string | Custom classes for inner container | - |

## Example Integration

See `src/pages/Grants.tsx` for a complete example of how to integrate the DashboardWrapper with navigation and content.
