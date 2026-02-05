# Frontend Development Guide

IMPORTANT: always use latest dependencies. follow design tokens and global.css in ./src/styles/design-tokens.css and ./src/styles/global.css

## Technology Stack

- **Language**: TypeScript 5+
- **Framework**: React 18
- **Build Tool**: Vite
- **State Management**: Zustand
- **Styling**: Tailwind CSS v4
- **HTTP Client**: Fetch API / Axios
- **Testing**: Vitest + React Testing Library

## Architecture Principles

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Components have one clear purpose
   - Separate presentation from business logic
   - Custom hooks encapsulate specific functionality
   - Services handle API communication only

2. **Open/Closed Principle (OCP)**
   - Components accept props for customization
   - Use composition over inheritance
   - Extend behavior through props and children

3. **Liskov Substitution Principle (LSP)**
   - Component interfaces are consistent
   - Props follow predictable patterns
   - Polymorphic components work interchangeably

4. **Interface Segregation Principle (ISP)**
   - Small, focused prop interfaces
   - Components don't require unused props
   - Optional props for flexibility

5. **Dependency Inversion Principle (DIP)**
   - Components depend on abstractions (types/interfaces)
   - Services use dependency injection patterns
   - Mock implementations for testing

### DRY (Don't Repeat Yourself)

- Eliminate code duplication
- Extract reusable components and hooks
- Create shared utility functions
- Use composition to avoid repeating patterns
- Centralize constants and configuration
- Share types across components

### YAGNI (You Aren't Gonna Need It)

- Build features when needed, not speculatively
- Avoid premature abstractions
- Start with simple components, refactor when patterns emerge
- No unused props or configuration options

### KISS (Keep It Simple, Stupid)

- Prefer simple, readable code
- Avoid over-engineering
- Clear component hierarchies
- Straightforward data flows

## Code Organization

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/              # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   └── features/            # Feature-specific components
│   │       ├── SlideEditor/
│   │       │   ├── SlideEditor.tsx
│   │       │   ├── SlideCanvas.tsx
│   │       │   └── SlideToolbar.tsx
│   │       └── SlideList/
│   │           ├── SlideList.tsx
│   │           └── SlideCard.tsx
│   ├── services/                # API communication
│   │   ├── api.ts               # Base API client
│   │   └── slideService.ts      # Slide-related API calls
│   ├── stores/                  # Zustand stores
│   │   ├── slideStore.ts        # Slide state management
│   │   └── uiStore.ts           # UI state (modals, loading)
│   ├── types/                   # TypeScript types
│   │   ├── slide.ts
│   │   └── api.ts
│   ├── hooks/                   # Custom React hooks
│   │   ├── useSlides.ts
│   │   └── useDebounce.ts
│   ├── utils/                   # Utility functions
│   │   ├── format.ts
│   │   └── validation.ts
│   ├── App.tsx                  # Root component
│   ├── main.tsx                 # Application entry
│   └── index.css                # Global styles
├── public/                      # Static assets
└── index.html                   # HTML template
```

### Directory Responsibilities

**components/common/**
- Reusable UI components
- No business logic
- Highly composable
- Well-documented props

**components/features/**
- Feature-specific components
- Organized by feature domain
- Can use stores and services
- Compose common components

**services/**
- API communication layer
- HTTP request/response handling
- Error transformation
- No state management

**stores/**
- Global state management
- Business logic for state updates
- Derived state (selectors)
- Persist state if needed

**hooks/**
- Reusable React hooks
- Encapsulate component logic
- Side effect management
- State and lifecycle logic

**types/**
- TypeScript interfaces and types
- Shared across the application
- API contracts
- Domain models

**utils/**
- Pure utility functions
- No side effects
- Easily testable
- Framework-agnostic

## Best Practices

### React Patterns

1. **Functional Components**
```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  variant = 'primary',
  disabled = false
}) => {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {label}
    </button>
  );
};
```

2. **Custom Hooks**
```typescript
export const useSlides = () => {
  const slides = useSlideStore(state => state.slides);
  const fetchSlides = useSlideStore(state => state.fetchSlides);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSlides = async () => {
      setLoading(true);
      try {
        await fetchSlides();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    loadSlides();
  }, [fetchSlides]);

  return { slides, loading, error };
};
```

3. **Component Composition**
```typescript
export const SlideEditor: React.FC = () => {
  return (
    <div className="slide-editor">
      <SlideToolbar />
      <SlideCanvas />
      <SlideProperties />
    </div>
  );
};
```

### TypeScript Patterns

1. **Strict Type Safety**
```typescript
// Enable strict mode in tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

2. **Type Definitions**
```typescript
export interface Slide {
  id: number;
  topic: string;
  content: SlideContent[];
  createdAt: string;
  updatedAt: string;
}

export interface SlideContent {
  type: 'title' | 'text' | 'image' | 'code';
  content: string;
  style?: Record<string, string>;
}
```

3. **API Response Types**
```typescript
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  error: string;
  details?: Record<string, string[]>;
}
```

### Zustand State Management

1. **Store Definition**
```typescript
interface SlideStore {
  slides: Slide[];
  currentSlide: Slide | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchSlides: () => Promise<void>;
  createSlide: (data: SlideCreateRequest) => Promise<void>;
  updateSlide: (id: number, data: SlideUpdateRequest) => Promise<void>;
  deleteSlide: (id: number) => Promise<void>;
  setCurrentSlide: (slide: Slide | null) => void;
}

export const useSlideStore = create<SlideStore>((set, get) => ({
  slides: [],
  currentSlide: null,
  loading: false,
  error: null,

  fetchSlides: async () => {
    set({ loading: true, error: null });
    try {
      const slides = await slideService.getAll();
      set({ slides, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  },

  createSlide: async (data) => {
    const slide = await slideService.create(data);
    set(state => ({ slides: [...state.slides, slide] }));
  },

  setCurrentSlide: (slide) => set({ currentSlide: slide })
}));
```

2. **Selector Pattern**
```typescript
// Use selectors to avoid unnecessary re-renders
const slides = useSlideStore(state => state.slides);
const loading = useSlideStore(state => state.loading);

// Derived state
const slideCount = useSlideStore(state => state.slides.length);
```

3. **Store Slicing**
```typescript
// Separate concerns into different stores
const useSlideStore = create(/* slide state */);
const useUIStore = create(/* UI state */);
const useAuthStore = create(/* auth state */);
```

## Concurrency Handling

### Async Operations

1. **API Calls**
```typescript
const fetchSlides = async () => {
  setLoading(true);
  try {
    const response = await slideService.getAll();
    setSlides(response.data);
  } catch (error) {
    handleError(error);
  } finally {
    setLoading(false);
  }
};
```

2. **Parallel Requests**
```typescript
const loadInitialData = async () => {
  try {
    const [slides, templates, settings] = await Promise.all([
      slideService.getAll(),
      templateService.getAll(),
      settingsService.get()
    ]);
    // Update state with all results
  } catch (error) {
    handleError(error);
  }
};
```

3. **Race Conditions**
```typescript
// Use AbortController for cancellable requests
const useSlideSearch = (query: string) => {
  const [results, setResults] = useState<Slide[]>([]);

  useEffect(() => {
    const controller = new AbortController();

    const search = async () => {
      try {
        const data = await slideService.search(query, {
          signal: controller.signal
        });
        setResults(data);
      } catch (error) {
        if (error.name !== 'AbortError') {
          handleError(error);
        }
      }
    };

    search();

    return () => controller.abort();
  }, [query]);

  return results;
};
```

### Debouncing and Throttling

```typescript
export const useDebounce = <T,>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// Usage
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounce(searchTerm, 500);

useEffect(() => {
  if (debouncedSearch) {
    performSearch(debouncedSearch);
  }
}, [debouncedSearch]);
```

### Loading States

```typescript
interface LoadingState {
  isLoading: boolean;
  isError: boolean;
  error: string | null;
}

const useAsyncOperation = <T,>(
  operation: () => Promise<T>
): [() => Promise<void>, LoadingState] => {
  const [state, setState] = useState<LoadingState>({
    isLoading: false,
    isError: false,
    error: null
  });

  const execute = async () => {
    setState({ isLoading: true, isError: false, error: null });
    try {
      await operation();
      setState({ isLoading: false, isError: false, error: null });
    } catch (error) {
      setState({
        isLoading: false,
        isError: true,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  return [execute, state];
};
```

## Error Handling

### Error Boundaries

```typescript
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error reporting service
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-container">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### API Error Handling

```typescript
// services/api.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public details?: Record<string, string[]>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const handleApiError = (error: unknown): never => {
  if (error instanceof ApiError) {
    throw error;
  }

  if (error instanceof Error) {
    throw new ApiError(500, error.message);
  }

  throw new ApiError(500, 'An unknown error occurred');
};

// services/slideService.ts
export const slideService = {
  async getAll(): Promise<Slide[]> {
    try {
      const response = await fetch('/api/slides');

      if (!response.ok) {
        const error = await response.json();
        throw new ApiError(
          response.status,
          error.error || 'Failed to fetch slides',
          error.details
        );
      }

      const data = await response.json();
      return data.data;
    } catch (error) {
      handleApiError(error);
    }
  }
};
```

### User-Facing Error Messages

```typescript
export const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
        return 'Invalid request. Please check your input.';
      case 404:
        return 'Resource not found.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return error.message;
    }
  }

  return 'An unexpected error occurred.';
};

// Usage in component
const handleSubmit = async () => {
  try {
    await slideService.create(formData);
    toast.success('Slide created successfully');
  } catch (error) {
    toast.error(getErrorMessage(error));
  }
};
```

### Form Validation

```typescript
interface ValidationError {
  field: string;
  message: string;
}

export const validateSlideForm = (data: SlideFormData): ValidationError[] => {
  const errors: ValidationError[] = [];

  if (!data.topic || data.topic.trim().length === 0) {
    errors.push({ field: 'topic', message: 'Topic is required' });
  }

  if (data.topic && data.topic.length > 200) {
    errors.push({ field: 'topic', message: 'Topic must be less than 200 characters' });
  }

  return errors;
};
```

## Logging

### Console Logging

```typescript
// utils/logger.ts
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

class Logger {
  private isDevelopment = import.meta.env.DEV;

  private log(level: LogLevel, message: string, data?: unknown) {
    if (!this.isDevelopment && level === 'debug') {
      return;
    }

    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;

    switch (level) {
      case 'debug':
        console.debug(prefix, message, data);
        break;
      case 'info':
        console.info(prefix, message, data);
        break;
      case 'warn':
        console.warn(prefix, message, data);
        break;
      case 'error':
        console.error(prefix, message, data);
        break;
    }
  }

  debug(message: string, data?: unknown) {
    this.log('debug', message, data);
  }

  info(message: string, data?: unknown) {
    this.log('info', message, data);
  }

  warn(message: string, data?: unknown) {
    this.log('warn', message, data);
  }

  error(message: string, error?: unknown) {
    this.log('error', message, error);
  }
}

export const logger = new Logger();
```

### Usage Patterns

```typescript
// Log API calls
const fetchSlides = async () => {
  logger.info('Fetching slides');
  try {
    const slides = await slideService.getAll();
    logger.info('Slides fetched successfully', { count: slides.length });
    return slides;
  } catch (error) {
    logger.error('Failed to fetch slides', error);
    throw error;
  }
};

// Log user actions
const handleSlideCreate = async (data: SlideCreateRequest) => {
  logger.debug('Creating slide', { topic: data.topic });
  await slideService.create(data);
  logger.info('Slide created', { topic: data.topic });
};

// Log component lifecycle
useEffect(() => {
  logger.debug('SlideEditor mounted');
  return () => {
    logger.debug('SlideEditor unmounted');
  };
}, []);
```

### What to Log

- API requests and responses
- User actions (clicks, form submissions)
- State changes (in development)
- Errors with full context
- Performance metrics

### What NOT to Log

- Sensitive user data
- Authentication tokens
- Personal information
- Large data structures in production

## Testing

### Component Testing

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders with label', () => {
    render(<Button label="Click me" onClick={() => {}} />);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button label="Click me" onClick={handleClick} />);

    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button label="Click me" onClick={() => {}} disabled />);
    expect(screen.getByText('Click me')).toBeDisabled();
  });
});
```

### Hook Testing

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useSlides } from './useSlides';

describe('useSlides', () => {
  it('fetches slides on mount', async () => {
    const { result } = renderHook(() => useSlides());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.slides).toHaveLength(3);
    });
  });
});
```

## Performance Optimization

### Memoization

```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive components
export const SlideCard = memo<SlideCardProps>(({ slide, onEdit }) => {
  return <div>{slide.topic}</div>;
});

// Memoize expensive computations
const sortedSlides = useMemo(() => {
  return slides.sort((a, b) => a.createdAt.localeCompare(b.createdAt));
}, [slides]);

// Memoize callbacks
const handleEdit = useCallback((id: number) => {
  editSlide(id);
}, [editSlide]);
```

### Code Splitting

```typescript
import { lazy, Suspense } from 'react';

const SlideEditor = lazy(() => import('./components/features/SlideEditor'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <SlideEditor />
    </Suspense>
  );
}
```

## Configuration

### Environment Variables

```typescript
// vite-env.d.ts
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_TITLE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Usage
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
```

## Security

- Sanitize user input before rendering
- Use Content Security Policy
- Validate data from API
- Avoid inline scripts
- Use HTTPS for API calls
- Store sensitive data securely (not in localStorage)
