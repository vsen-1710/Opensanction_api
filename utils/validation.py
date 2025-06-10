import re
import logging
from typing import Dict, Any, List, Optional
import phonenumbers
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

class InputValidator:
    """Enhanced input validator for flexible person/company data structures"""
    
    def __init__(self):
        logger.info("Input validator initialized for flexible data structures")
        self.name_pattern = re.compile(r'^[a-zA-Z\s\-\'\.]{2,100}$')
        self.company_pattern = re.compile(r'^[a-zA-Z0-9\s\-\'\.&,()]{2,200}$')
        self.address_pattern = re.compile(r'^[a-zA-Z0-9\s\-\'\.,#\/]{5,500}$')
    
    def validate_risk_assessment_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize risk assessment input with flexible structure"""
        if not data:
            raise ValueError("Request body cannot be empty")
        
        # Extract person and company data
        person_data = data.get('person', {})
        company_data = data.get('company', {})
        
        # Handle legacy flat structure (backward compatibility)
        if not person_data and not company_data:
            # Check if we have flat structure (old format)
            if data.get('name') or data.get('company'):
                # Build person data from flat structure
                if data.get('name'):
                    person_data = {
                        'name': data.get('name', ''),
                        'phone': data.get('phone', ''),
                        'email': data.get('email', ''),
                        'address': data.get('address', ''),
                        'date_of_birth': data.get('date_of_birth', ''),
                        'country': data.get('country', '')
                    }
                
                # Build company data from flat structure if company name exists
                if data.get('company'):
                    company_data = {
                        'name': data.get('company', ''),
                        'address': data.get('company_address', data.get('address', '')),
                        'phone': data.get('company_phone', data.get('phone', '')),
                        'country': data.get('country', ''),
                        'industry': data.get('industry', ''),
                        'registration_number': data.get('company_id', '')
                    }
                    # If we only have a company, don't create person data
                    if not data.get('name'):
                        person_data = {}
        
        # Validate that we have at least person OR company data
        if not person_data and not company_data:
            raise ValueError("Must provide either person details, company details, or both")
        
        validated_data = {
            'input_type': self._determine_input_type(person_data, company_data),
            'timestamp': data.get('timestamp'),
            'request_id': data.get('request_id')
        }
        
        # Validate and add person data if provided
        if person_data and any(person_data.values()):
            validated_data['person'] = self._validate_person_data(person_data)
        
        # Validate and add company data if provided
        if company_data and any(company_data.values()):
            validated_data['company'] = self._validate_company_data(company_data)
        
        return validated_data
    
    def _determine_input_type(self, person_data: Dict, company_data: Dict) -> str:
        """Determine the type of input for processing strategy"""
        has_person = person_data and any(person_data.values())
        has_company = company_data and any(company_data.values())
        
        if has_person and has_company:
            return 'person_and_company'
        elif has_person:
            return 'person_only'
        elif has_company:
            return 'company_only'
        else:
            return 'invalid'
    
    def _validate_person_data(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate person-specific data"""
        validated = {}
        
        # Name validation
        name = person_data.get('name', '').strip()
        if name:
            if len(name) < 2:
                raise ValueError("Person name must be at least 2 characters")
            if len(name) > 100:
                raise ValueError("Person name must be less than 100 characters")
            validated['name'] = name
        
        # Phone validation
        phone = person_data.get('phone', '').strip()
        if phone:
            validated['phone'] = self._validate_phone(phone)
        
        # Email validation
        email = person_data.get('email', '').strip()
        if email:
            validated['email'] = self._validate_email(email)
        
        # Address validation
        address = person_data.get('address', '').strip()
        if address:
            if len(address) > 500:
                raise ValueError("Address must be less than 500 characters")
            validated['address'] = address
        
        # Date of birth validation
        dob = person_data.get('date_of_birth', '').strip()
        if dob:
            validated['date_of_birth'] = self._validate_date(dob)
        
        # Country validation
        country = person_data.get('country', '').strip()
        if country:
            validated['country'] = self._validate_country(country)
        
        # Additional fields
        for field in ['nationality', 'occupation', 'passport_number']:
            value = person_data.get(field, '').strip()
            if value:
                validated[field] = value
        
        return validated
    
    def _validate_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate company-specific data"""
        validated = {}
        
        # Company name validation
        name = company_data.get('name', '').strip()
        if name:
            if len(name) < 2:
                raise ValueError("Company name must be at least 2 characters")
            if len(name) > 200:
                raise ValueError("Company name must be less than 200 characters")
            validated['name'] = name
        
        # Registration number validation
        reg_number = company_data.get('registration_number', '').strip()
        if reg_number:
            validated['registration_number'] = reg_number
        
        # Phone validation
        phone = company_data.get('phone', '').strip()
        if phone:
            validated['phone'] = self._validate_phone(phone)
        
        # Email validation
        email = company_data.get('email', '').strip()
        if email:
            validated['email'] = self._validate_email(email)
        
        # Address validation
        address = company_data.get('address', '').strip()
        if address:
            if len(address) > 500:
                raise ValueError("Company address must be less than 500 characters")
            validated['address'] = address
        
        # Country validation
        country = company_data.get('country', '').strip()
        if country:
            validated['country'] = self._validate_country(country)
        
        # Industry validation
        industry = company_data.get('industry', '').strip()
        if industry:
            validated['industry'] = industry
        
        # Additional company fields
        for field in ['website', 'tax_id', 'incorporation_date', 'legal_form']:
            value = company_data.get(field, '').strip()
            if value:
                validated[field] = value
        
        return validated
    
    def _validate_phone(self, phone: str) -> str:
        """Validate phone number format with more lenient validation"""
        try:
            # Remove common formatting characters
            cleaned_phone = re.sub(r'[\s\-\(\)\.]', '', phone)
            
            # Try parsing with phonenumbers library
            try:
                parsed = phonenumbers.parse(cleaned_phone, None)
                
                if phonenumbers.is_valid_number(parsed):
                    # Return in international format
                    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            except phonenumbers.NumberParseException:
                pass
            
            # Fallback: more lenient validation for various formats
            # Remove all non-digit characters except +
            digits_only = re.sub(r'[^\d+]', '', phone)
            
            # Basic length validation (7-15 digits is reasonable for most phone numbers)
            digit_count = len(re.sub(r'[^\d]', '', digits_only))
            if digit_count < 7 or digit_count > 15:
                raise ValueError(f"Invalid phone number length: {phone}")
            
            # Accept various common formats
            common_patterns = [
                r'^\+\d{1,3}\d{7,12}$',  # International format
                r'^\d{10}$',             # 10-digit US format
                r'^\d{11}$',             # 11-digit with country code
                r'^\+1\d{10}$',          # US international format
                r'^\+\d{1,3}-\d{3,4}-\d{3,4}-\d{3,4}$'  # Hyphenated international
            ]
            
            # If it matches any common pattern, accept it
            for pattern in common_patterns:
                if re.match(pattern, digits_only):
                    return phone  # Return original format
            
            # If none match, it's still possibly valid - be lenient
            if digit_count >= 7:
                return phone
            
            raise ValueError(f"Invalid phone number format: {phone}")
        
        except ValueError:
            raise
        except Exception as e:
            logger.warning(f"Phone validation error: {str(e)}")
            # Be very lenient - if there's any error, just accept it if it has digits
            if re.search(r'\d{7,}', phone):
                return phone
            raise ValueError(f"Invalid phone number format: {phone}")
    
    def _validate_email(self, email: str) -> str:
        """Validate email format"""
        try:
            valid = validate_email(email)
            return valid.email
        except EmailNotValidError:
            raise ValueError(f"Invalid email format: {email}")
    
    def _validate_date(self, date_str: str) -> str:
        """Validate date format (YYYY-MM-DD or similar)"""
        # Basic date format validation
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$'   # DD-MM-YYYY
        ]
        
        if not any(re.match(pattern, date_str) for pattern in date_patterns):
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD, MM/DD/YYYY, or DD-MM-YYYY")
        
        return date_str
    
    def _validate_country(self, country: str) -> str:
        """Validate country code or name"""
        # Accept both country codes (US, UK, etc.) and full names
        if len(country) == 2:
            return country.upper()
        elif 2 < len(country) <= 50:
            return country.title()
        else:
            raise ValueError(f"Invalid country format: {country}")
    
    def normalize_for_search(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize validated data for search operations"""
        search_data = {
            'input_type': validated_data.get('input_type'),
            'search_queries': []
        }
        
        # Generate search queries based on input type
        if validated_data.get('person'):
            person = validated_data['person']
            search_data['primary_entity'] = {
                'type': 'person',
                'name': person.get('name', ''),
                'identifiers': {
                    'phone': person.get('phone', ''),
                    'email': person.get('email', ''),
                    'address': person.get('address', ''),
                    'country': person.get('country', '')
                }
            }
        
        if validated_data.get('company'):
            company = validated_data['company']
            search_data['secondary_entity'] = {
                'type': 'company', 
                'name': company.get('name', ''),
                'identifiers': {
                    'registration_number': company.get('registration_number', ''),
                    'phone': company.get('phone', ''),
                    'address': company.get('address', ''),
                    'country': company.get('country', '')
                }
            }
        
        return search_data
    
    def validate_entity_data(self, data):
        """Validate entity data from request"""
        if not isinstance(data, dict):
            return {
                'valid': False,
                'message': 'Input must be a JSON object'
            }
        
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                return {
                    'valid': False,
                    'message': f'Missing required field: {field}'
                }
        
        return {
            'valid': True,
            'data': data
        }
    
    def _validate_name(self, name: Any) -> Dict[str, Any]:
        """Validate and clean person name"""
        if not name:
            return {'valid': False, 'error': 'Name is required'}
        
        if not isinstance(name, str):
            return {'valid': False, 'error': 'Name must be a string'}
        
        name = name.strip()
        
        if len(name) < 2:
            return {'valid': False, 'error': 'Name must be at least 2 characters long'}
        
        if len(name) > 100:
            return {'valid': False, 'error': 'Name must be less than 100 characters'}
        
        # Clean and normalize the name
        cleaned_name = self._clean_text(name)
        
        # Check for valid characters
        if not self.name_pattern.match(cleaned_name):
            return {'valid': False, 'error': 'Name contains invalid characters'}
        
        # Check for suspicious patterns
        if self._contains_suspicious_patterns(cleaned_name):
            return {'valid': False, 'error': 'Name contains suspicious patterns'}
        
        return {'valid': True, 'value': cleaned_name}
    
    def _validate_company(self, company: str) -> Dict[str, Any]:
        """Validate and clean company name"""
        if len(company) < 2:
            return {'valid': False, 'error': 'Company name must be at least 2 characters long'}
        
        if len(company) > 200:
            return {'valid': False, 'error': 'Company name must be less than 200 characters'}
        
        cleaned_company = self._clean_text(company)
        
        if not self.company_pattern.match(cleaned_company):
            return {'valid': False, 'error': 'Company name contains invalid characters'}
        
        if self._contains_suspicious_patterns(cleaned_company):
            return {'valid': False, 'error': 'Company name contains suspicious patterns'}
        
        return {'valid': True, 'value': cleaned_company}
    
    def _validate_address(self, address: str) -> Dict[str, Any]:
        """Validate and clean address"""
        if len(address) < 5:
            return {'valid': False, 'error': 'Address must be at least 5 characters long'}
        
        if len(address) > 500:
            return {'valid': False, 'error': 'Address must be less than 500 characters'}
        
        cleaned_address = self._clean_text(address)
        
        if not self.address_pattern.match(cleaned_address):
            return {'valid': False, 'error': 'Address contains invalid characters'}
        
        return {'valid': True, 'value': cleaned_address}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text input"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Normalize quotes and apostrophes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _contains_suspicious_patterns(self, text: str) -> bool:
        """Check for suspicious patterns in text"""
        suspicious_patterns = [
            r'<script[^>]*>',  # Script tags
            r'javascript:',     # JavaScript URLs
            r'on\w+\s*=',      # Event handlers
            r'eval\s*\(',      # Eval function
            r'alert\s*\(',     # Alert function
            r'document\.',     # Document object
            r'window\.',       # Window object
            r'\.\./',          # Directory traversal
            r'[<>]',           # HTML tags
            r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]'  # Control characters
        ]
        
        text_lower = text.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def validate_search_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search parameters"""
        validation_result = {
            'valid': True,
            'message': 'Validation successful',
            'params': {}
        }
        
        # Validate limit
        limit = params.get('limit', 10)
        try:
            limit = int(limit)
            if limit < 1 or limit > 100:
                validation_result['valid'] = False
                validation_result['message'] = 'Limit must be between 1 and 100'
                return validation_result
            validation_result['params']['limit'] = limit
        except (ValueError, TypeError):
            validation_result['valid'] = False
            validation_result['message'] = 'Limit must be a valid integer'
            return validation_result
        
        # Validate offset
        offset = params.get('offset', 0)
        try:
            offset = int(offset)
            if offset < 0:
                validation_result['valid'] = False
                validation_result['message'] = 'Offset must be non-negative'
                return validation_result
            validation_result['params']['offset'] = offset
        except (ValueError, TypeError):
            validation_result['valid'] = False
            validation_result['message'] = 'Offset must be a valid integer'
            return validation_result
        
        # Validate risk level filter
        risk_level = params.get('risk_level')
        if risk_level:
            if risk_level.upper() not in ['LOW', 'MEDIUM', 'HIGH']:
                validation_result['valid'] = False
                validation_result['message'] = 'Risk level must be LOW, MEDIUM, or HIGH'
                return validation_result
            validation_result['params']['risk_level'] = risk_level.upper()
        
        return validation_result 