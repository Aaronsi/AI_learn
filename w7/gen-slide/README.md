# GenSlides - AI Image Slide Generator

Transform your text into beautiful AI-generated slide images using Volcano Ark's Doubao-Seed-1.8 model.

## Features

- 🎨 **AI-Powered Image Generation**: Create stunning visuals from text descriptions
- 🎯 **Style Consistency**: Set a reference style to keep all slides visually coherent
- 📝 **Easy Slide Management**: Add, edit, reorder, and delete slides with intuitive UI
- 🎬 **Fullscreen Presentation**: Present your slides in carousel mode
- 💾 **Local Storage**: All data stored locally, no database required
- 💰 **Cost Tracking**: Monitor AI generation costs per project

## Technology Stack

### Backend
- **Language**: Python 3.12+
- **Package Manager**: uv
- **Framework**: FastAPI
- **AI Model**: Volcano Ark Doubao-Seed-1.8

### Frontend
- **Language**: TypeScript
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand

## Prerequisites

- Python 3.12 or higher
- Node.js 18 or higher
- uv (Python package manager)
- Volcano Ark API key

## Installation

### 1. Install uv (if not already installed)

**Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd gen-slide

# Install Python dependencies using uv
uv sync

# Configure backend environment
cd backend
cp .env.example .env
# Edit .env and add your Volcano Ark API key
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

## Running the Application

### Backend Server

**Option 1: Using startup scripts (recommended)**

Windows:
```bash
start-backend.bat
```

Linux/Mac:
```bash
./start-backend.sh
```

**Option 2: Using uv directly**
```bash
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: http://localhost:8000

### Frontend Development Server

```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3003

## Project Structure

```
gen-slide/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── routers/           # API routes
│   │   ├── services/          # Business logic
│   │   └── models/            # Data models
│   ├── slides/                # Slide data storage
│   └── .env                   # Environment configuration
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── stores/            # Zustand state management
│   │   ├── services/          # API services
│   │   └── styles/            # CSS and design tokens
│   └── package.json
├── pyproject.toml             # Python dependencies (uv)
├── uv.lock                    # Locked dependencies
├── start-backend.bat          # Windows startup script
└── start-backend.sh           # Linux/Mac startup script
```

## Usage

1. **Create a Project**: Visit `http://localhost:3003/your-project-name`
2. **Add Slides**: Click "Add Your First Slide" in the sidebar
3. **Edit Content**: Double-click any slide to edit its text
4. **Set Style**: Choose a visual style for consistency across slides
5. **Generate Images**: Click "Generate Image" to create visuals from text
6. **Present**: Click the "Play" button to present in fullscreen mode

## Development

### Adding Python Dependencies

```bash
# Add a runtime dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Sync dependencies
uv sync
```

### Backend Development

See [backend/CLAUDE.md](backend/CLAUDE.md) for detailed backend development guidelines.

### Frontend Development

See [frontend/CLAUDE.md](frontend/CLAUDE.md) for detailed frontend development guidelines.

## API Documentation

Once the backend is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend (.env)

```bash
ARK_API_KEY=your_volcano_ark_api_key
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
MODEL_ID=doubao-seed-1-8-251228
HOST=0.0.0.0
PORT=8000
SLIDES_BASE_PATH=./slides
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
