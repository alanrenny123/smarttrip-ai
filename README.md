# 🌟 SmartTrip AI

![SmartTrip AI Banner](https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.10-blue?style=for-the-badge&logo=python) ![Flask](https://img.shields.io/badge/Flask-API-black?style=for-the-badge&logo=flask) ![Machine Learning](https://img.shields.io/badge/Scikit_Learn-Random_Forest-F7931E?style=for-the-badge&logo=scikit-learn)

**SmartTrip AI** is a predictive travel intelligence platform that leverages machine learning to forecast tourist crowd levels, provide dynamic travel recommendations, and automatically generate optimized, multi-destination itineraries.

## 🚀 Key Features

- **Predictive Crowd Modeling:** Uses a highly accurate Random Forest Regressor (R² = 89%) trained on historical tourism data to predict visitor counts for specific dates, times, and destinations.
- **Dynamic Recommendations:** Automatically detects high-crowd times and suggests intelligent alternatives (better times to visit or lower-crowd alternative destinations).
- **Multi-Stop Trip Optimizer:** A greedy-swap algorithm that processes multiple destinations and creates a flawless vertical timeline itinerary, ensuring you visit the right places at the right time.
- **Live Weather Integration:** Connects to the Open-Meteo forecasting API to provide up-to-the-minute weather conditions and rain probabilities for any date up to 16 days in the future.
- **Premium Glassmorphic UI:** A custom-built, highly responsive frontend designed with modern aesthetics, animations, and an intuitive user experience.

## 🛠️ Technology Stack

- **Backend & API:** Python, Flask, Flask-CORS
- **Machine Learning Pipeline:** Pandas, Scikit-learn (Random Forest, Decision Trees, Gradient Boosting), Joblib
- **Frontend:** HTML5, Vanilla JavaScript, CSS3 (Custom Glassmorphism Design System)
- **External Services:** Open-Meteo API (Live Weather)
- **Deployment:** Render (Automated via Blueprint)

## 📁 Repository Structure

```text
├── backend/
│   ├── agents/          # Recommendation and Trip Optimization logic
│   ├── ml/              # Data preprocessing, training scripts, and inference pipeline
│   ├── models/          # Serialized ML models and metadata
│   ├── services/        # External API integrations (Weather)
│   └── app.py           # Main Flask API application
├── frontend/            # HTML, CSS, and JS application logic
├── render.yaml          # Automated deployment configuration
├── requirements.txt     # Python dependencies
└── README.md
```

## ⚙️ Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alanrenny123/smarttrip-ai.git
   cd smarttrip-ai
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the backend server:**
   ```bash
   python backend/app.py
   ```

4. **View the application:**
   Open your browser and navigate to `http://localhost:5000`

## 🧠 Machine Learning Details

The core intelligence of SmartTrip AI is powered by a robust ML pipeline that evaluates multiple classical regression models. Based on our dataset of 730 historical Indian tourism records across 2024–2025, the **Random Forest Regressor** was selected as the champion model. It accurately captures non-linear crowd fluctuations (e.g., weekend spikes, holiday surges, and lunch-hour dips) with high resilience to overfitting.

---
*Built with ❤️ for intelligent, stress-free travel.*
