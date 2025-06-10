# OpenSancton - Risk Intelligence Platform

OpenSancton is a comprehensive risk intelligence platform that provides real-time risk assessment for individuals and companies. It combines multiple data sources including sanctions lists, web intelligence, and graph database analysis to deliver accurate risk assessments.

## Features

- **Real-time Risk Assessment**: Analyze individuals and companies for potential risks
- **Multiple Data Sources**: Integration with OpenSanctions, web search, and graph database
- **AI-Powered Analysis**: Advanced AI analysis of search results and connections
- **Graph Database**: Neo4j-based relationship analysis and visualization
- **RESTful API**: Easy integration with existing systems
- **Docker Support**: Containerized deployment for easy setup

## System Architecture

```
OpenSancton/
├── app.py                 # Main application entry point
├── config.py             # Configuration settings
├── docker-compose.yml    # Docker compose configuration
├── Dockerfile           # Docker build instructions
├── requirements.txt     # Python dependencies
├── services/           # Core services
│   ├── ai_service.py   # AI analysis service
│   ├── risk_service.py # Risk assessment orchestration
│   ├── web_search_service.py # Web intelligence gathering
│   └── opensanctions_service.py # Sanctions list integration
├── graph/              # Graph database operations
│   └── neo4j_service.py # Neo4j database service
└── utils/              # Utility functions
    ├── risk_calculator.py # Risk score calculation
    ├── cache.py        # Caching mechanism
    └── errors.py       # Error handling
```

## Data Flow

1. **Input Processing**
   - Accepts person or company data through REST API
   - Validates and normalizes input data
   - Generates unique entity IDs

2. **Risk Assessment Pipeline**
   - Sanctions List Check
   - Web Intelligence Gathering
   - AI Analysis
   - Graph Database Analysis
   - Risk Score Calculation

3. **Response Generation**
   - Comprehensive risk assessment
   - Risk indicators and scores
   - Supporting evidence
   - Recommendations

## API Endpoints

### Risk Assessment
```http
POST /api/check_risk
Content-Type: application/json

{
    "person": {
        "name": "John Doe",
        "address": "123 Main St",
        "phone": "+1-555-0123"
    },
    "company": {
        "name": "Example Corp",
        "address": "456 Business Ave",
        "phone": "+1-555-0124"
    }
}
```

### Graph Data
```http
GET /api/entity/{entity_id}/graph
```

### Statistics
```http
GET /api/statistics
```

## Setup and Installation

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Neo4j Database

### Environment Variables
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
SERPER_API_KEY=your_serper_key
PERPLEXITY_API_KEY=your_perplexity_key
```

### Docker Setup
1. Clone the repository
2. Configure environment variables
3. Run with Docker Compose:
```bash
docker-compose up -d
```

### Manual Setup
1. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the application:
```bash
python app.py
```

## Data Sources

### OpenSanctions
- Integration with OpenSanctions database
- Real-time sanctions list checking
- Confidence scoring for matches

### Web Intelligence
- Google search via Serper API
- Perplexity AI search
- Risk indicator extraction
- Sentiment analysis

### Graph Database
- Neo4j for relationship analysis
- Entity connections tracking
- Risk propagation analysis
- Historical data storage

## Risk Assessment Process

1. **Data Collection**
   - Gather entity information
   - Check sanctions lists
   - Perform web searches
   - Analyze connections

2. **AI Analysis**
   - Process search results
   - Identify risk indicators
   - Generate risk summary
   - Calculate confidence scores

3. **Risk Calculation**
   - Combine multiple risk factors
   - Weight different indicators
   - Generate final risk score
   - Provide recommendations

## Performance Optimization

- **Caching**: Implemented for frequent queries
- **Fast Mode**: Optimized for quick assessments
- **Parallel Processing**: Multiple data source checks
- **Connection Pooling**: Efficient database access

## Security

- API key management
- Input validation
- Rate limiting
- Error handling
- Secure data storage

## Monitoring and Maintenance

- Logging system
- Performance metrics
- Error tracking
- Database maintenance
- Cache management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the development team. 