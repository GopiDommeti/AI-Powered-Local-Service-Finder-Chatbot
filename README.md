# 🔍 Local Service Finder Bot

A Streamlit-based chatbot that helps users discover local services (AC repair, plumbers, electricians, etc.) using JustDial data, ChromaDB vector database, and Google Gemini AI.

## 🎯 Features

- **🔍 Smart Search**: Semantic search through local service listings
- **🤖 AI-Powered Responses**: Intelligent recommendations using Gemini AI
- **📊 Real-time Filters**: Filter by category, location, and price
- **💬 Chat Interface**: Natural language queries and responses
- **📱 Responsive UI**: Beautiful Streamlit interface with service cards
- **⚡ Vector Database**: Fast semantic search with ChromaDB
- **🕷️ Web Scraping**: Data collection from JustDial using Firecrawl

## 🏗️ Architecture

```
User Query → Streamlit UI → Vector Search → Gemini AI → Formatted Response
                ↓
            ChromaDB (Vector Database)
                ↓
            JustDial Data (via Firecrawl)
```

## 📦 Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Google Gemini API
- **Vector Database**: ChromaDB
- **Web Scraping**: Firecrawl
- **Data Processing**: Pandas, BeautifulSoup4
- **Environment**: Python 3.8+

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
```

### 3. Get API Keys

- **Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Firecrawl API Key**: Visit [Firecrawl](https://firecrawl.dev) (optional for live data)

### 4. Run the Application

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## 📁 Project Structure

```
newai/
├── app.py                 # Main Streamlit application
├── justdial_scraper.py    # JustDial data scraper using Firecrawl
├── vector_db.py          # ChromaDB vector database operations
├── test_scraper.py       # Test script for scraper functionality
├── requirements.txt      # Python dependencies
├── sample_services.json  # Sample data for development
├── chroma_db/           # ChromaDB database files
└── README.md            # Project documentation
```

## 🎮 Usage

### Basic Usage

1. **Start the app**: `streamlit run app.py`
2. **Ask questions** like:
   - "Show me AC repair services under ₹500 in Madhapur"
   - "Find plumbers near me"
   - "Best electricians with good ratings"

### Advanced Features

- **Filters**: Use sidebar filters for category, location, and price
- **Chat History**: View previous conversations
- **Service Cards**: Detailed service information with ratings and contact details

## 🔧 Configuration

### Rate Limits

The app uses Gemini's free tier with these limits:
- **Per minute**: 15 requests, 15,000 input tokens
- **Per day**: 1,500 requests, 1,500,000 input tokens

### Database

- **Storage**: Local ChromaDB database
- **Location**: `./chroma_db/` directory
- **Sample Data**: Automatically loaded on first run

## 📊 Data Sources

### Current Setup
- **Sample Data**: 5 services across 3 categories (AC Repair, Plumber, Electrician)
- **Locations**: Hyderabad area
- **Data Format**: JSON with name, address, phone, rating, price, category

### Live Data (Optional)
To use live JustDial data:
1. Get a Firecrawl API key
2. Update the scraper configuration
3. Run data collection scripts

## 🛠️ Development

### Adding New Data

```python
# Load custom data
from vector_db import ServiceVectorDB

db = ServiceVectorDB()
db.load_from_json("your_data.json")
```

### Customizing Search

```python
# Advanced search with filters
services = db.search_services(
    query="AC repair",
    n_results=10,
    category_filter="AC Repair",
    max_price=500,
    location_filter="Hyderabad"
)
```

### Extending Categories

Add new service categories by:
1. Updating the scraper with new JustDial URLs
2. Adding category-specific parsing logic
3. Updating the UI filters

## 🚀 Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud dashboard

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 🔍 Troubleshooting

### Common Issues

1. **Rate Limit Errors**
   - Wait a few minutes between requests
   - Consider upgrading to paid Gemini plan

2. **Database Errors**
   - Check ChromaDB installation
   - Verify sample data exists

3. **API Key Issues**
   - Verify `.env` file exists
   - Check API key validity

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Future Enhancements

- [ ] **Real-time Scraping**: Live JustDial data updates
- [ ] **More Categories**: Expand service categories
- [ ] **Location Services**: GPS-based location detection
- [ ] **Reviews Integration**: User reviews and ratings
- [ ] **Booking System**: Direct service booking
- [ ] **Multi-language**: Support for regional languages
- [ ] **Mobile App**: Native mobile application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **JustDial**: For service data
- **Firecrawl**: For web scraping capabilities
- **ChromaDB**: For vector database functionality
- **Google Gemini**: For AI/LLM capabilities
- **Streamlit**: For the web framework

## 📞 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the documentation
3. Open an issue on GitHub

---

**Happy Service Finding! 🔍✨**
