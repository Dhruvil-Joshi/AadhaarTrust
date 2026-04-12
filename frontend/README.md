# AadhaarTrust Frontend

Modern React + TypeScript frontend for Aadhaar card verification.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Environment variables:**
   Create a `.env` file (optional):
   ```env
   VITE_API_URL=http://localhost:8000/api/v1
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   ```

## Features

- 🎨 Modern UI with purple theme
- 📱 Fully responsive design
- ⚡ Real-time progress updates
- 📊 Detailed validation results
- 📥 Report downloads (PDF, HTML, JSON)
- 🔄 Automatic status polling

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── hooks/          # Custom React hooks
│   ├── types/          # TypeScript types
│   └── config/         # Configuration
├── public/
└── package.json
```

## Pages

- `/` - Landing page
- `/upload` - Image upload
- `/validation/:jobId` - Progress tracking
- `/results/:jobId` - Results dashboard
- `/admin/manual-review` - Manual review (admin)
