# 🏠 Real Estate Listing Analysis Assistant

A Python-based MVP (Minimum Viable Product) designed to help users discover, filter, store, and analyze residential property listings through a simple and interactive Streamlit interface.

The application collects property listings from supported sources, applies budget-based filtering, stores results in a local SQLite database, and can optionally leverage OpenAI models to provide intelligent ranking and analysis.

---

## ✨ Features

* 🔍 Search and retrieve residential property listings
* 💰 Filter properties based on a maximum budget
* 🗄️ Store listings locally using SQLite
* 📊 Intelligent ranking and prioritization
* 🤖 Optional AI-powered analysis using OpenAI models
* 🌐 Modular architecture for adding new listing providers
* 🎨 Simple and user-friendly Streamlit interface

---

## 🚀 Getting Started

### Prerequisites

Ubuntu/Debian users may need to install the Python virtual environment package before creating a virtual environment:

```bash
sudo apt install python3-venv
```

### Installation

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

streamlit run app.py
```

The application will start locally and can be accessed through your web browser.

---

## 🤖 AI-Powered Analysis

To enable intelligent property analysis and ranking, add your OpenAI API key to the `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

When no API key is provided, the application will continue to function normally using a basic price-based ranking strategy.

---

## 🏗️ Architecture

The project follows a modular architecture:

```text
app/
├── providers/      # Listing source integrations
├── analyzers/      # AI and ranking logic
├── database/       # SQLite persistence layer
├── ui/             # Streamlit interface
└── services/       # Business logic
```

This design makes it easy to add new data sources without modifying the user interface or analysis components.

---

## ⚠️ Important Notes

### Data Source Disclaimer

The current integration uses a defensive client implementation for publicly available search responses. It is **not** an officially supported partner API.

For production environments, developers should:

* Verify official API availability
* Review terms of service
* Respect rate limits
* Obtain required permissions and licenses

### Property Verification

Listings should not be considered legally authoritative information.

Before making any purchasing decisions, users should independently verify:

* Property ownership
* Legal documentation
* Building permits
* Property condition
* Final sale price

### Provider Extensions

Adding support for additional listing platforms is straightforward. New providers can be implemented independently without requiring changes to the UI or ranking engine.

---

## 🔮 Future Improvements

* Multi-source property aggregation
* Advanced AI scoring models
* Property comparison tools
* Neighborhood analysis
* Historical price tracking
* Interactive maps
* Export to Excel and PDF
* Personalized recommendation engine

---

## 📄 License

This project is provided for educational and research purposes. Please ensure compliance with the terms and conditions of any external data sources used.
