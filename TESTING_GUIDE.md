# OpenSancton API Testing Guide

This guide provides comprehensive JSON input examples for testing all scenarios of the OpenSancton Risk Intelligence Platform.

## API Base URL
- Development: `http://localhost:5000`
- Production: `https://your-domain.com`

## Testing Scenarios

### 1. Person Only Risk Assessment

Test individual person risk assessment without company information.

```json
{
  "person": {
    "name": "John Smith",
    "phone": "+1-555-0123",
    "email": "john.smith@email.com",
    "address": "123 Main Street, New York, NY 10001",
    "date_of_birth": "1985-03-15",
    "country": "US"
  }
}
```

### 2. Company Only Risk Assessment

Test company risk assessment without person information.

```json
{
  "company": {
    "name": "Acme Corporation",
    "address": "456 Business Ave, San Francisco, CA 94105",
    "phone": "+1-555-0124",
    "country": "US",
    "industry": "Technology",
    "registration_number": "C1234567",
    "website": "https://acme-corp.com",
    "incorporation_date": "2020-01-15"
  }
}
```

### 3. Company with Single Director ID (Backward Compatibility)

Test company with a single director ID for legacy support.

```json
{
  "company": {
    "name": "Tech Innovations LLC",
    "address": "789 Innovation Drive, Austin, TX 78701",
    "phone": "+1-555-0125",
    "country": "US",
    "industry": "Software Development",
    "registration_number": "LLC9876543",
    "director_id": "DIR001234"
  }
}
```

### 4. Company with Multiple Directors (New Feature)

Test company with detailed director information including names, positions, and appointment dates.

```json
{
  "company": {
    "name": "Global Solutions Inc",
    "address": "100 Corporate Plaza, Chicago, IL 60601",
    "phone": "+1-555-0126",
    "country": "US",
    "industry": "Consulting",
    "registration_number": "INC5555555",
    "website": "https://globalsolutions.com",
    "directors": [
      {
        "director_id": "DIR001",
        "name": "Alice Johnson",
        "position": "Chief Executive Officer",
        "appointment_date": "2021-01-01",
        "status": "Active",
        "nationality": "US",
        "date_of_birth": "1975-06-20"
      },
      {
        "director_id": "DIR002",
        "name": "Robert Chen",
        "position": "Chief Financial Officer",
        "appointment_date": "2021-03-15",
        "status": "Active",
        "nationality": "US"
      },
      {
        "director_id": "DIR003",
        "name": "Maria Rodriguez",
        "position": "Chief Technology Officer",
        "appointment_date": "2021-06-01",
        "status": "Active",
        "nationality": "MX"
      }
    ]
  }
}
```

### 5. Person and Company Association

Test person associated with a company to verify relationship tracking.

```json
{
  "person": {
    "name": "Emily Davis",
    "phone": "+1-555-0127",
    "email": "emily.davis@startup.com",
    "address": "555 Startup St, Seattle, WA 98101",
    "country": "US"
  },
  "company": {
    "name": "Startup Ventures LLC",
    "address": "555 Startup St, Seattle, WA 98101",
    "phone": "+1-555-0128",
    "country": "US",
    "industry": "Venture Capital",
    "registration_number": "LLC2023001"
  }
}
```

### 6. Person Associated with Company Having Directors

Test complex relationship where a person is associated with a company that has multiple directors.

```json
{
  "person": {
    "name": "Michael Thompson",
    "phone": "+1-555-0129",
    "email": "m.thompson@bigcorp.com",
    "address": "777 Executive Blvd, Boston, MA 02101",
    "country": "US"
  },
  "company": {
    "name": "Big Corporation Ltd",
    "address": "777 Executive Blvd, Boston, MA 02101",
    "phone": "+1-555-0130",
    "country": "US",
    "industry": "Manufacturing",
    "registration_number": "LTD7777777",
    "website": "https://bigcorp.com",
    "directors": [
      {
        "director_id": "BIGDIR001",
        "name": "Sarah Wilson",
        "position": "Chairman",
        "appointment_date": "2020-01-01",
        "status": "Active"
      },
      {
        "director_id": "BIGDIR002",
        "name": "David Kim",
        "position": "Managing Director",
        "appointment_date": "2020-01-01",
        "status": "Active"
      }
    ]
  }
}
```

### 7. International Company with Directors

Test international company with directors from different countries.

```json
{
  "company": {
    "name": "International Holdings PLC",
    "address": "City of London, EC2V 8RF, United Kingdom",
    "phone": "+44-20-7123-4567",
    "country": "UK",
    "industry": "Financial Services",
    "registration_number": "PLC12345678",
    "website": "https://intlholdings.co.uk",
    "incorporation_date": "2015-03-20",
    "directors": [
      {
        "director_id": "INTL001",
        "name": "James Morrison",
        "position": "Executive Director",
        "appointment_date": "2015-03-20",
        "status": "Active",
        "nationality": "UK"
      },
      {
        "director_id": "INTL002",
        "name": "Hans Mueller",
        "position": "Non-Executive Director",
        "appointment_date": "2016-01-10",
        "status": "Active",
        "nationality": "DE"
      },
      {
        "director_id": "INTL003",
        "name": "Hiroshi Tanaka",
        "position": "Independent Director",
        "appointment_date": "2017-04-15",
        "status": "Active",
        "nationality": "JP"
      }
    ]
  }
}
```

### 8. Legacy Format (Backward Compatibility)

Test the old flat structure format to ensure backward compatibility.

```json
{
  "name": "Legacy User",
  "phone": "+1-555-0131",
  "email": "legacy@example.com",
  "address": "Old Format Address",
  "company": "Legacy Company Inc",
  "company_address": "Legacy Company Address",
  "country": "US"
}
```

## API Endpoints for Testing

### 1. Main Risk Assessment
```http
POST /api/check_risk
Content-Type: application/json

[Use any of the JSON examples above]
```

### 2. Entity Relationships
```http
GET /api/entity/{entity_id}/relationships
```

### 3. Director Company Associations
```http
GET /api/director/{director_id}/companies
```

### 4. Entity Graph Data
```http
GET /api/entity/{entity_id}/graph
```

### 5. Performance Settings
```http
POST /api/performance/fast-mode
Content-Type: application/json

{
  "enabled": true
}
```

### 6. Health Check
```http
GET /health
```

## Expected Response Structure

### Risk Assessment Response
```json
{
  "entities": {
    "person": { /* person data */ },
    "company": { /* company data */ }
  },
  "input_type": "person_and_company",
  "risk_score": 45,
  "risk_level": "MEDIUM",
  "assessment_timestamp": 1640995200,
  "processing_time_ms": 1250,
  "sanctions_check": { /* sanctions results */ },
  "web_intelligence": { /* web search results */ },
  "ai_summary": { /* AI analysis */ },
  "graph_analysis": { /* graph connections */ },
  "entity_relationships": {
    "relationships_created": [],
    "director_relationships": [],
    "entity_associations": {}
  },
  "director_analysis": {
    "total_directors": 2,
    "director_risk_analysis": [],
    "suggestions": []
  }
}
```

### Entity Relationships Response
```json
{
  "entity_id": "company_12345678",
  "relationships": {
    "entity_found": true,
    "entity_type": ["Company", "Entity"],
    "entity_name": "Global Solutions Inc",
    "relationships": {
      "associated_persons": [],
      "directors": [
        {
          "director_id": "director_87654321",
          "director_name": "Alice Johnson",
          "external_director_id": "DIR001",
          "position": "Chief Executive Officer",
          "status": "Active",
          "appointment_date": "2021-01-01"
        }
      ]
    }
  }
}
```

### Director Companies Response
```json
{
  "director_id": "DIR001",
  "director_info": {
    "director_id": "DIR001",
    "director_name": "Alice Johnson",
    "internal_id": "director_87654321"
  },
  "associated_companies": [
    {
      "company_id": "company_12345678",
      "company_name": "Global Solutions Inc",
      "position": "Chief Executive Officer",
      "appointment_date": "2021-01-01",
      "status": "Active",
      "company_details": {
        "industry": "Consulting",
        "country": "US",
        "registration_number": "INC5555555",
        "risk_level": "LOW"
      }
    }
  ],
  "total_companies": 1,
  "suggestion": "Consider individual risk assessment for director Alice Johnson"
}
```

## Testing Workflow

1. **Start with Person Only** - Test basic individual assessment
2. **Test Company Only** - Verify company assessment works
3. **Add Director ID** - Test single director relationship
4. **Test Multiple Directors** - Verify complex director structure
5. **Test Person + Company** - Check entity associations
6. **Verify Relationships** - Use relationship endpoints to confirm connections
7. **Test Director Lookups** - Use director endpoint to find associated companies
8. **Performance Testing** - Enable fast mode and compare response times

## Error Testing

### Invalid Input
```json
{
  "invalid_field": "test"
}
```
Expected: 400 Bad Request with validation error

### Missing Required Fields
```json
{
  "person": {
    "phone": "+1-555-0123"
  }
}
```
Expected: 400 Bad Request - missing name

### Invalid Phone Format
```json
{
  "person": {
    "name": "Test User",
    "phone": "invalid-phone"
  }
}
```
Expected: 400 Bad Request - invalid phone format

## Performance Testing

1. **Fast Mode Enabled**: Response time should be 2-8 seconds
2. **Normal Mode**: Response time should be 4-15 seconds  
3. **Cached Requests**: Response time should be < 100ms
4. **Large Director Lists**: Test companies with 10+ directors

## Security Testing

1. **SQL Injection**: Test with malicious input in name fields
2. **XSS**: Test with script tags in text fields
3. **Large Payloads**: Test with oversized input data
4. **Rate Limiting**: Test rapid successive requests

This testing guide covers all scenarios for the enhanced OpenSancton platform with director relationships and entity associations. 