# Quick Start Guide - Phase 21 Frontend

## 🚀 Getting Started

### Prerequisites
- Node.js v18+ (v24.19.0 installed ✓)
- npm (comes with Node.js)
- Python backend running on port 8000

### Installation

```bash
# Navigate to frontend directory
cd c:\Users\Administrator\Desktop\FIFA2026\frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:3000` in your browser.

## 🔧 Configuration

### Backend API URL
Edit `.env` file:
```
VITE_API_URL=http://localhost:8000
```

## 📋 What's Implemented

### Pages (All Ready to Use)
| Page | Route | Status |
|------|-------|--------|
| Home | `/` | ✅ Complete |
| Match Intelligence | `/matches` | ✅ Complete |
| Season Oracle | `/oracle` | ✅ Complete |
| Teams | `/teams` | ✅ Complete |
| Players | `/players` | ✅ Complete |
| Beat the AI | `/beat-ai` | ✅ Complete |

### Features
- ✅ Dark/light theme toggle
- ✅ Responsive mobile layout
- ✅ Search & filtering
- ✅ API integration ready
- ✅ Charts & visualizations
- ✅ Leaderboards
- ✅ Countdown timers
- ✅ Smooth animations

## 🧪 Testing Checklist

After `npm run dev`, test:

- [ ] Home page loads with hero section
- [ ] Navigation works (all 6 pages accessible)
- [ ] Dark mode toggle works
- [ ] Mobile menu works on small screens
- [ ] Search works on Teams and Players pages
- [ ] Filters work on Match Intelligence page
- [ ] Charts display on Season Oracle page
- [ ] Beat the AI predictions input works
- [ ] All links are clickable

## 🔌 API Integration

The frontend is ready to connect to these endpoints:

```
GET  /health                    → Health check
GET  /model-info               → Model metadata
POST /predict                  → Single prediction
POST /predict/bulk             → Batch predictions
GET  /gameweek/current         → Current gameweek
GET  /gameweek/{gw}            → Specific gameweek
GET  /oracle/projections       → Season simulations
GET  /teams                    → All teams
GET  /teams/{id}              → Specific team
GET  /teams/search?q=         → Search teams
GET  /players                 → All players
GET  /players/{id}            → Specific player
GET  /players/search?q=       → Search players
POST /beat-ai/submit          → Submit predictions
GET  /beat-ai/leaderboard     → Rankings
```

## 📁 File Structure

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── MatchIntelligence.tsx
│   │   ├── SeasonOracle.tsx
│   │   ├── Teams.tsx
│   │   ├── Players.tsx
│   │   └── BeatTheAI.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   ├── App.css
│   ├── index.css
│   └── main.tsx
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── package.json
├── .env
└── IMPLEMENTATION_COMPLETE.md
```

## 🛠️ Available Commands

```bash
# Development
npm run dev          # Start dev server (http://localhost:3000)

# Production
npm run build        # Build for production
npm run preview      # Preview production build

# Linting
npm run lint         # Run ESLint
```

## 🎨 Design Highlights

### Colors
- Primary: Blue → Purple gradient
- Success: Green → Emerald
- Danger: Red → Rose
- Warning: Yellow → Orange

### Fonts
- Body: Inter
- Headings: Poppins

### Theme
- Dark mode by default
- Light mode available via toggle

## 📱 Responsive Breakpoints

- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

All pages are optimized for each breakpoint.

## 🔗 Navigation Structure

```
Home (/)
├── Match Intelligence (/matches)
├── Season Oracle (/oracle)
├── Teams (/teams)
├── Players (/players)
├── Beat the AI (/beat-ai)
└── Dark Mode Toggle
```

## 🚨 Troubleshooting

### "npm command not found"
```bash
# Use PowerShell RemoteSigned execution policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
```

### Port 3000 already in use
```bash
# Change port in vite.config.ts:
server: {
  port: 3001  // Use different port
}
```

### API not connecting
1. Ensure backend is running: `python -m src.api.main`
2. Check `.env` has correct API URL
3. Check CORS headers in FastAPI backend

### Styles not loading
```bash
# Rebuild Tailwind CSS
npm install
npm run dev
```

## 📊 Sample Data

The frontend includes sample data for:
- ✅ 4 featured match predictions
- ✅ 20 Premier League teams
- ✅ 8 top players
- ✅ 5 sample leaderboard entries
- ✅ Season projections for top teams

This data displays immediately while waiting for real API data.

## 🚀 Next: Connect Backend

1. Start backend:
   ```bash
   cd ..  # Go to project root
   python -m src.api.main
   ```

2. Frontend will automatically:
   - Connect to API
   - Load real predictions
   - Display actual gameweek fixtures
   - Show real team/player data
   - Calculate live probabilities

## 📞 Support

For issues:
1. Check console errors (F12 → Console tab)
2. Verify backend is running
3. Check .env configuration
4. Review network tab for API calls

## ✨ What's Next

After getting the frontend running:

1. ✅ Test all 6 pages
2. ✅ Verify search/filter works
3. ✅ Check API calls in Network tab
4. ✅ Test on mobile device
5. ✅ Test dark/light mode
6. ✅ Make predictions on Beat the AI page
7. ✅ Deploy to production

## 🎯 Key Features to Showcase

- Premium dark-themed design
- Real-time countdown timers
- Interactive probability charts
- Smooth page transitions
- Complete search/filtering
- Leaderboard system
- Mobile responsive layout
- Professional typography
- Data visualization

---

**Everything is ready! Run `npm install && npm run dev` to start.** 🎉
