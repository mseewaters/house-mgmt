"""
Email Parser Lambda Handler for Meal Data Extraction
Triggered by S3 events when new email files arrive
Parses email content and extracts meal information
"""
import json
import boto3
import base64
import email
import re
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from urllib.parse import unquote

from models.meal import MealCreate
from dal.meal_dal import MealDAL

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
meal_dal = MealDAL()


def lambda_handler(event, context):
    """
    Lambda handler for parsing email files from S3 and extracting meal data
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process each S3 record
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:s3':
                bucket_name = record['s3']['bucket']['name']
                object_key = unquote(record['s3']['object']['key'])
                
                logger.info(f"Processing email file: s3://{bucket_name}/{object_key}")
                
                # Download and parse email
                email_content = download_email_from_s3(bucket_name, object_key)
                logger.info(f"Downloaded email content, length: {len(email_content)} characters")
                
                meals = parse_email_for_meals(email_content)
                logger.info(f"Parsed {len(meals)} meals from email")
                
                # Log the meals found
                for i, meal_data in enumerate(meals):
                    logger.info(f"Meal {i+1}: {meal_data.get('meal_name', 'unknown')}")
                
                # Save meals to DynamoDB
                for meal_data in meals:
                    try:
                        logger.info(f"Attempting to save meal: {meal_data}")
                        meal = MealCreate(**meal_data)
                        result = meal_dal.create_meal(meal)
                        logger.info(f"Successfully saved meal: {meal.meal_name}, result: {result}")
                    except Exception as e:
                        logger.error(f"Failed to save meal {meal_data.get('meal_name', 'unknown')}: {str(e)}")
                        logger.error(f"Meal data was: {meal_data}")
                
                logger.info(f"Processed {len(meals)} meals from email")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Email processing completed successfully'})
        }
        
    except Exception as e:
        logger.error(f"Error processing email: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def download_email_from_s3(bucket_name: str, object_key: str) -> str:
    """Download email content from S3"""
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read()
        
        # Try to decode as UTF-8, fallback to latin-1
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            return content.decode('latin-1')
            
    except Exception as e:
        logger.error(f"Failed to download email from S3: {str(e)}")
        raise


def parse_email_for_meals(email_content: str) -> List[Dict]:
    """
    Parse email content and extract meal information
    Handles both plain text and HTML emails, including base64 encoding
    """
    meals = []
    
    try:
        # Parse email message
        msg = email.message_from_string(email_content)
        
        # Get email body (handle multipart and base64 encoding)
        email_body = get_email_body(msg)
        
        # Extract date from email body (same content as meals)
        date_shipped = extract_date_from_raw_content(email_body)
        
        # Extract meals from content
        meals = extract_meals_from_content(email_body, date_shipped)
        
    except Exception as e:
        logger.error(f"Failed to parse email: {str(e)}")
        # Fallback: try to extract from raw content
        date_shipped = extract_date_from_raw_content(email_content)
        meals = extract_meals_from_content(email_content, date_shipped)
    
    return meals


def get_email_body(msg) -> str:
    """Extract body content from email message - prefer plain text for easier parsing"""
    html_body = None
    plain_body = None
    
    if msg.is_multipart():
        # Find text/plain and text/html parts, prefer plain text
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ['text/plain', 'text/html']:
                # ALWAYS decode - email.get_payload(decode=True) handles all encodings
                payload = part.get_payload(decode=True)
                
                if payload:
                    try:
                        if isinstance(payload, bytes):
                            decoded = payload.decode('utf-8', errors='ignore')
                        else:
                            decoded = payload
                    except UnicodeDecodeError:
                        if isinstance(payload, bytes):
                            decoded = payload.decode('latin-1', errors='ignore')
                        else:
                            decoded = payload
                    
                    # Store both versions
                    if content_type == 'text/html':
                        html_body = decoded
                    elif content_type == 'text/plain':
                        plain_body = decoded
        
        # Return plain text if available, otherwise HTML
        return plain_body if plain_body else (html_body if html_body else "")
    else:
        # Single part message - ALWAYS decode
        payload = msg.get_payload(decode=True)
        
        if payload:
            try:
                if isinstance(payload, bytes):
                    return payload.decode('utf-8', errors='ignore')
                else:
                    return payload
            except UnicodeDecodeError:
                if isinstance(payload, bytes):
                    return payload.decode('latin-1', errors='ignore')
                else:
                    return payload
        return ""


def is_base64_encoded(content: str) -> bool:
    """Check if content appears to be base64 encoded"""
    if not content:
        return False
    
    # Basic heuristic: if content is mostly base64 characters
    base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    content_chars = set(content.replace('\n', '').replace('\r', ''))
    
    return len(content_chars.intersection(base64_chars)) / len(content_chars) > 0.8 if content_chars else False


def decode_base64_content(content: str) -> str:
    """Decode base64 content"""
    try:
        # Clean up content (remove whitespace)
        cleaned = re.sub(r'\s+', '', content)
        decoded = base64.b64decode(cleaned)
        return decoded.decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to decode base64 content: {str(e)}")
        return content


def extract_date_from_email(msg, email_content: str) -> str:
    """Extract shipped date from email headers or content"""
    logger.info("Starting date extraction from email")
    
    # Try email Date header first
    date_header = msg.get('Date')
    logger.info(f"Email Date header: {date_header}")
    if date_header:
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_header)
            header_date = parsed_date.strftime('%Y-%m-%d')
            logger.info(f"Parsed date from header: {header_date}")
            # Don't return header date, let's extract from content instead
        except Exception as e:
            logger.warning(f"Failed to parse date header: {e}")
    
    # Try to extract from subject or content
    content_date = extract_date_from_raw_content(email_content)
    logger.info(f"Final extracted date: {content_date}")
    return content_date


def extract_date_from_raw_content(content: str) -> str:
    """Extract date from email content using regex patterns"""
    logger.info("Extracting date from email content")
    
    # CRITICAL: Decode quoted-printable FIRST before pattern matching
    content = decode_quoted_printable(content)
    
    # Find the section before "What's In Your Box" - this is where the date should be
    whats_in_box_match = re.search(r"What.?s In Your Box", content, re.IGNORECASE)
    if whats_in_box_match:
        # Get everything before "What's In Your Box"
        pre_meals_section = content[:whats_in_box_match.start()]
        logger.info(f"=== SECTION BEFORE 'What's In Your Box' (for date extraction) ===")
        logger.info(f"Length: {len(pre_meals_section)} chars")
        logger.info(f"Last 1000 chars of pre-meals section:")
        logger.info(f"'{pre_meals_section[-1000:]}'")
        logger.info(f"=== END PRE-MEALS SECTION ===")
        
        # Use this section for date extraction
        search_content = pre_meals_section
    else:
        logger.warning("Could not find 'What's In Your Box' marker, using full content")
        search_content = content
        logger.info(f"Full content preview (first 2000 chars): {content[:2000]}")
    
    # Search for key phrases in the search content
    if "delivery" in search_content.lower():
        logger.info("Found 'delivery' in search content")
        delivery_context = re.search(r'.{0,100}delivery.{0,100}', search_content, re.IGNORECASE | re.DOTALL)
        if delivery_context:
            logger.info(f"Delivery context: '{delivery_context.group()}'")
    
    if "will arrive" in search_content.lower():
        logger.info("Found 'will arrive' in search content")
        arrive_context = re.search(r'.{0,100}will arrive.{0,100}', search_content, re.IGNORECASE | re.DOTALL)
        if arrive_context:
            logger.info(f"Will arrive context: '{arrive_context.group()}'")
    
    if "december" in search_content.lower():
        logger.info("Found 'december' in search content")
        december_context = re.search(r'.{0,50}december.{0,50}', search_content, re.IGNORECASE | re.DOTALL)
        if december_context:
            logger.info(f"December context: '{december_context.group()}'")
    
    if "next week" in search_content.lower():
        logger.info("Found 'next week' in search content")
        next_week_contexts = re.findall(r'.{0,100}next week.{0,100}', search_content, re.IGNORECASE | re.DOTALL)
        for i, context in enumerate(next_week_contexts[:3]):  # Show first 3 matches
            logger.info(f"Next week context {i+1}: '{context}'")
    
    # Look for delivery date pattern: focus on "will arrive on"
    delivery_patterns = [
        r"will arrive on \w+,\s+(\w+\s+\d+)",           # "will arrive on Friday, December 5"
        r"will arrive on (\w+,\s+\w+\s+\d+)",           # "will arrive on Friday, December 5" (capture all)
        r"delivery will arrive on \w+,\s+(\w+\s+\d+)",  # "delivery will arrive on Friday, December 5" 
        r"delivery will arrive on (\w+,\s+\w+\s+\d+)",  # "delivery will arrive on Friday, December 5" (capture all)
        r"arrive on \w+,\s+(\w+\s+\d+)",                # "arrive on Friday, December 5"
        r"arrive on (\w+,\s+\w+\s+\d+)",                # "arrive on Friday, December 5" (capture all)
    ]
    
    logger.info(f"Testing delivery patterns against search content...")
    for pattern in delivery_patterns:
        logger.info(f"Trying delivery pattern: {pattern}")
        delivery_match = re.search(pattern, search_content, re.IGNORECASE | re.DOTALL)
        if delivery_match:
            date_str = delivery_match.group(1)  # e.g., "December 5" or "Friday, December 5"
            logger.info(f"✅ FOUND delivery date match with pattern '{pattern}': '{date_str}'")
            
            # Clean up the date string - if it includes day of week, extract just the month/day
            if ',' in date_str:
                # "Friday, December 5" -> "December 5"
                date_parts = date_str.split(',')
                if len(date_parts) > 1:
                    date_str = date_parts[1].strip()
            
            logger.info(f"Cleaned date string: '{date_str}'")
            parsed_date = parse_month_day_to_date(date_str)
            logger.info(f"Parsed delivery date: {parsed_date}")
            return parsed_date
        else:
            logger.info(f"❌ No match for pattern: {pattern}")
    
    # Also try to find "Week of Friday, December 5" pattern
    week_of_pattern = r"Week of \w+,\s+(\w+\s+\d+)"
    logger.info(f"Trying week pattern: {week_of_pattern}")
    week_match = re.search(week_of_pattern, search_content, re.IGNORECASE)
    if week_match:
        date_str = week_match.group(1)  # e.g., "December 5"
        logger.info(f"✅ FOUND 'Week of' date: '{date_str}'")
        parsed_date = parse_month_day_to_date(date_str)
        logger.info(f"Parsed week date: {parsed_date}")
        return parsed_date
    else:
        logger.info(f"❌ No match for week pattern")
    
    logger.warning("❌ No delivery date patterns matched in the search content")
    
    # Look for other common patterns
    date_patterns = [
        r'Week of \w+,\s+(\w+\s+\d+)',  # "Week of Friday, December 5"
        r'(\w+\s+\d+,\s+\d{4})',        # "December 5, 2025"
        r'(\d{4}-\d{2}-\d{2})',         # "2025-12-05"
        r'(\d{1,2}/\d{1,2}/\d{4})'      # "12/5/2025"
    ]
    
    for pattern in date_patterns:
        logger.info(f"Trying fallback pattern: {pattern}")
        match = re.search(pattern, search_content, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            logger.info(f"✅ FOUND date match with fallback pattern {pattern}: '{date_str}'")
            try:
                if re.match(r'\w+\s+\d+', date_str):  # "December 5" format
                    parsed_date = parse_month_day_to_date(date_str)
                    logger.info(f"Parsed date: {parsed_date}")
                    return parsed_date
                elif re.match(r'\d{4}-\d{2}-\d{2}', date_str):  # ISO format
                    logger.info(f"Using ISO date: {date_str}")
                    return date_str
                elif re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):  # MM/DD/YYYY
                    parts = date_str.split('/')
                    formatted = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
                    logger.info(f"Converted MM/DD/YYYY to: {formatted}")
                    return formatted
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_str}': {e}")
        else:
            logger.info(f"❌ No match for fallback pattern: {pattern}")
    
    # Fallback to current date
    fallback_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    logger.warning(f"❌ No date patterns found in any section, using fallback: {fallback_date}")
    return fallback_date


def parse_month_day_to_date(date_str: str) -> str:
    """Parse month name and day to ISO date format"""
    try:
        # Month name mapping
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        # Clean up the date string - if it includes day of week, extract just the month/day
        if ',' in date_str:
            # "Friday, December 5" -> "December 5"
            date_parts = date_str.split(',')
            if len(date_parts) > 1:
                date_str = date_parts[1].strip()
        
        # Split and parse
        parts = date_str.lower().split()
        if len(parts) >= 2:
            month_name = parts[0]
            day = int(parts[1])
            
            if month_name in months:
                month = months[month_name]
                
                # Determine year - meal dates are typically within the next few weeks
                from datetime import datetime, timezone
                current_date = datetime.now(timezone.utc)
                year = current_date.year
                
                # Create the date for this year
                try_date = datetime(year, month, day, tzinfo=timezone.utc)
                
                # If the date is more than 30 days in the past, assume it's next year
                days_diff = (current_date - try_date).days
                if days_diff > 30:
                    year += 1
                
                return f"{year}-{month:02d}-{day:02d}"
    
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {str(e)}")
    
    # Fallback to current date
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime('%Y-%m-%d')


def extract_meals_from_content(content: str, date_shipped: str) -> List[Dict]:
    """Extract meal information from email content using plain text parsing"""
    meals = []
    
    logger.info(f"Starting meal extraction for date: {date_shipped}")
    logger.info(f"Content preview (first 2000 chars): {content[:2000]}")
    
    # First, decode quoted-printable encoding if present
    content = decode_quoted_printable(content)
    logger.info(f"After decoding, content preview (first 2000 chars): {content[:2000]}")
    
    # Find the meal section between "What's In Your Box" and "View Full Menu"
    start_pattern = r"What.?s In Your Box"
    end_pattern = r"View Full Menu"
    
    start_match = re.search(start_pattern, content, re.IGNORECASE)
    end_match = re.search(end_pattern, content, re.IGNORECASE)
    
    if start_match and end_match:
        meal_section = content[start_match.end():end_match.start()]
        logger.info(f"Found meal section between markers, length: {len(meal_section)}")
        logger.info(f"Meal section preview: {meal_section[:500]}")
    else:
        logger.warning("Could not find meal section markers, using full content")
        meal_section = content
    
    # Extract meals from the section
    # Look for patterns like:
    # > Sheet Pan Potato-Crusted Chicken
    # > with chive crema and cheesy potatoes
    
    # Split by lines and process
    lines = meal_section.split('\n')
    current_meal = None
    logger.info(f"Processing {len(lines)} lines from meal section")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines and URL lines
        if not line or 'https://' in line or line.startswith('>=20'):
            continue
        
        # Remove leading > characters
        original_line = line
        line = re.sub(r'^>\s*', '', line)
        
        # Skip if still empty
        if not line:
            continue
        
        logger.info(f"Line {i}: '{original_line}' -> '{line}'")
        
        # Check if this looks like a meal title (starts with capital, doesn't start with "with")
        if (line and line[0].isupper() and 
            not line.lower().startswith('with ') and 
            not line.lower().startswith('view ') and
            len(line) > 3):
            
            # Save previous meal if we have one
            if current_meal and current_meal['meal_name']:
                logger.info(f"Saving meal: {current_meal['meal_name']}")
                meals.append(current_meal)
            
            # Start new meal
            logger.info(f"Starting new meal: {line}")
            current_meal = {
                'meal_name': line.strip(),
                'description': '',
                'thumbnail_url': 'https://asset.homechef.com/uploads/meal/default-placeholder.jpg',  # Default placeholder
                'date_shipped': date_shipped,
                'status': 'available'
            }
            
        elif current_meal and line:
            # This is likely a description line
            logger.info(f"Adding description to {current_meal['meal_name']}: {line}")
            if line.lower().startswith('with '):
                current_meal['description'] = line
            elif not current_meal['description'] and not line.lower().startswith('view '):
                # If no description yet, use this line (but skip lines like "View Full Menu")
                if line.lower().startswith('with '):
                    current_meal['description'] = line
                else:
                    current_meal['description'] = f"with {line}"
            elif line.endswith('included'):
                # Handle special cases like "2 sandwiches included"
                current_meal['description'] += f" ({line})"
    
    # Don't forget the last meal
    if current_meal and current_meal['meal_name']:
        logger.info(f"Saving final meal: {current_meal['meal_name']}")
        meals.append(current_meal)
    
    # Extract thumbnail URLs from the content and assign to meals
    image_urls = extract_thumbnail_urls_from_content(content)
    logger.info(f"Found {len(image_urls)} thumbnail URLs for {len(meals)} meals")
    
    # Assign thumbnails to meals
    for i, meal in enumerate(meals):
        if i < len(image_urls):
            meal['thumbnail_url'] = image_urls[i]
            logger.info(f"Assigned thumbnail to {meal['meal_name']}: {image_urls[i]}")
        else:
            meal['thumbnail_url'] = 'https://asset.homechef.com/uploads/meal/default-placeholder.jpg'
            logger.info(f"Using placeholder thumbnail for {meal['meal_name']}")
    
    # Clean up meal names and descriptions
    for meal in meals:
        meal['meal_name'] = re.sub(r'[^\w\s&-]', '', meal['meal_name']).strip()
        # Don't remove 'with' if the description starts with it
        if not meal['description'].lower().startswith('with '):
            meal['description'] = meal['description'].strip()
        else:
            meal['description'] = meal['description'].strip()
    
    # Filter out invalid meals
    valid_meals = [
        meal for meal in meals 
        if (meal['meal_name'] and 
            len(meal['meal_name']) > 3 and 
            meal['meal_name'].lower() not in ['menu', 'order', 'view', 'explore', 'full'])
    ]
    
    logger.info(f"Extracted {len(valid_meals)} valid meals from email content")
    return valid_meals


def extract_thumbnail_urls_from_content(content: str) -> List[str]:
    """Extract thumbnail URLs from email content (plain text or HTML)"""
    image_urls = []
    
    logger.info("Starting thumbnail URL extraction from email content")
    
    # Look for Home Chef image URLs - these appear in both HTML and plain text
    url_patterns = [
        r'https://asset\.homechef\.com/uploads/meal/[^"\s\>\<\)]+\.jpg',
        r'https://asset\.homechef\.com/uploads/meal/[^"\s\>\<\)]+\.jpeg', 
        r'https://asset\.homechef\.com/uploads/meal/[^"\s\>\<\)]+\.png',
        r'https://image\.e\.homechef\.com/[^"\s\>\<\)]+\.jpg',
        r'https://image\.e\.homechef\.com/[^"\s\>\<\)]+\.jpeg',
        r'https://image\.e\.homechef\.com/[^"\s\>\<\)]+\.png',
    ]
    
    for pattern in url_patterns:
        found_urls = re.findall(pattern, content, re.IGNORECASE)
        for url in found_urls:
            # Clean up the URL - remove any trailing characters
            clean_url = re.sub(r'[^\w\-\./:]+$', '', url)
            if clean_url not in image_urls:  # Avoid duplicates
                image_urls.append(clean_url)
                logger.info(f"Found thumbnail URL: {clean_url}")
    
    # Also search for any homechef.com URLs and filter for likely meal images
    general_homechef_pattern = r'https://[^"\s\>\<\)]*homechef\.com[^"\s\>\<\)]*'
    all_homechef_urls = re.findall(general_homechef_pattern, content, re.IGNORECASE)
    
    logger.info(f"Found {len(all_homechef_urls)} total Home Chef URLs")
    
    for url in all_homechef_urls:
        # Filter for image-like URLs
        if (any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png']) and
            'meal' in url.lower() and
            url not in image_urls):
            clean_url = re.sub(r'[^\w\-\./:]+$', '', url)
            image_urls.append(clean_url)
            logger.info(f"Found additional meal image URL: {clean_url}")
    
    logger.info(f"Total thumbnail URLs extracted: {len(image_urls)}")
    return image_urls


def extract_meals_from_html(content: str, date_shipped: str) -> List[Dict]:
    """Extract meal information from HTML email content"""
    meals = []
    
    logger.info("Extracting meals from HTML content")
    
    # First, decode quoted-printable encoding if present
    content = decode_quoted_printable(content)
    
    # Remove HTML tags to get clean text, but preserve structure
    import re
    
    # Look for the meal section - Home Chef emails usually have the meals in specific sections
    # Common patterns:
    # - "What's In Your Box" section
    # - Meal titles often in <h1>, <h2>, <h3>, or <strong> tags
    # - Descriptions often follow in <p> or <div> tags
    
    # First, try to find the meal box section
    meal_section_patterns = [
        r'What.?s In Your Box.*?(?=View Full Menu|$)',
        r'Your meals this week.*?(?=View Full Menu|$)',
        r'This week.?s meals.*?(?=View Full Menu|$)',
        r'<table[^>]*>.*?</table>',  # Look for meal tables
    ]
    
    meal_section = content
    for pattern in meal_section_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            meal_section = match.group(0)
            logger.info(f"Found meal section with pattern '{pattern}': {len(meal_section)} chars")
            break
    
    logger.info(f"Meal section preview (first 1000 chars): {meal_section[:1000]}")
    
    # Extract meal names - look for common HTML patterns
    meal_patterns = [
        # Look for text in table cells or divs that looks like meal names
        r'<td[^>]*>([^<]{10,80})</td>',  # Table cells with meal-like text
        r'<div[^>]*>([^<]{10,80})</div>',  # Divs with meal-like text  
        r'<h[1-6][^>]*>([^<]{5,80})</h[1-6]>',  # Headers
        r'<strong[^>]*>([^<]{5,80})</strong>',  # Strong text
        r'<b[^>]*>([^<]{5,80})</b>',  # Bold text
        r'<span[^>]*style="[^"]*font-weight[^"]*">([^<]{5,80})</span>',  # Styled spans
    ]
    
    potential_meals = []
    for pattern in meal_patterns:
        matches = re.findall(pattern, meal_section, re.IGNORECASE | re.DOTALL)
        for match in matches:
            # Clean up the text
            clean_text = re.sub(r'\s+', ' ', match.strip())
            clean_text = decode_quoted_printable(clean_text)
            
            # Filter out non-meal text
            if (len(clean_text) > 5 and 
                not re.match(r'^\d+$', clean_text) and  # Not just numbers
                not clean_text.lower().startswith('view') and
                not clean_text.lower().startswith('order') and
                not clean_text.lower().startswith('menu') and
                not clean_text.lower().startswith('explore') and
                not clean_text.lower().startswith('http') and
                not clean_text.lower().startswith('www') and
                not clean_text.lower() in ['now', 'make updates', 'friday', 'ct', '12pm'] and
                'font-family' not in clean_text.lower() and
                'color:' not in clean_text.lower()):
                
                potential_meals.append(clean_text)
                logger.info(f"Found potential meal from pattern '{pattern}': {clean_text}")
    
    # Also try to extract from alt text of images
    img_alt_pattern = r'<img[^>]+alt=["\']([^"\']{5,80})["\'][^>]*>'
    img_matches = re.findall(img_alt_pattern, meal_section, re.IGNORECASE)
    for alt_text in img_matches:
        clean_alt = re.sub(r'\s+', ' ', alt_text.strip())
        if len(clean_alt) > 5:
            potential_meals.append(clean_alt)
            logger.info(f"Found potential meal from img alt: {clean_alt}")
    
    logger.info(f"Total potential meals found: {len(potential_meals)}")
    
    # Filter and clean potential meals to get real meal names
    seen_meals = set()
    for text in potential_meals:
        # Skip if too generic or clearly not a meal
        if (text.lower() in ['make updates by friday at 12pm ct', 'now', 'home chef'] or
            len(text) < 8 or
            text in seen_meals):
            continue
            
        # Look for actual meal-like patterns
        # Meals often have patterns like "Chicken with ..." or "Pan-Seared ..."
        if (any(keyword in text.lower() for keyword in [
                'chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'pasta',
                'pizza', 'burger', 'steak', 'soup', 'salad', 'rice', 'noodles',
                'pan', 'grilled', 'baked', 'roasted', 'seared', 'crispy',
                'sheet pan', 'skillet', 'bowl', 'wrap', 'sandwich'
            ]) or
            # Or if it has a food-like structure (adjective + noun patterns)
            re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+.*', text)):
            
            # Extract description if it's in the vicinity
            description = extract_description_near_meal(meal_section, text)
            
            meal = {
                'meal_name': text.strip(),
                'description': description,
                'thumbnail_url': '',
                'date_shipped': date_shipped,
                'status': 'available'
            }
            
            meals.append(meal)
            seen_meals.add(text)
            logger.info(f"Added meal: {text}")
    
    # Extract thumbnail URLs
    image_urls = extract_image_urls_from_html(content)
    
    # Assign thumbnails to meals
    for i, meal in enumerate(meals):
        if i < len(image_urls):
            meal['thumbnail_url'] = image_urls[i]
            logger.info(f"Assigned thumbnail to {meal['meal_name']}: {image_urls[i]}")
        else:
            meal['thumbnail_url'] = "https://asset.homechef.com/uploads/meal/default-placeholder.jpg"
    
    logger.info(f"Extracted {len(meals)} valid meals from HTML content")
    return meals


def extract_description_near_meal(content: str, meal_name: str) -> str:
    """Try to find a description near a meal name in HTML content"""
    # Look for the meal name and try to find associated description text
    
    # Create a pattern to find content around the meal name
    escaped_meal = re.escape(meal_name)
    
    # Look for content within 500 characters after the meal name
    pattern = f'{escaped_meal}.{{0,500}}'
    match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
    
    if match:
        context = match.group(0)
        
        # Look for "with" phrases which are common in descriptions
        with_pattern = r'with [^<>]{5,100}'
        with_match = re.search(with_pattern, context, re.IGNORECASE)
        
        if with_match:
            description = with_match.group(0).strip()
            # Clean up HTML entities and extra whitespace
            description = decode_quoted_printable(description)
            description = re.sub(r'\s+', ' ', description)
            return description
    
    return ''


def extract_image_urls_from_html(content: str) -> List[str]:
    """Extract thumbnail URLs from HTML content"""
    image_urls = []
    
    # Look for img src attributes
    img_patterns = [
        r'<img[^>]+src=["\']([^"\']+asset\.homechef\.com[^"\']+)["\'][^>]*>',
        r'<img[^>]+src=["\']([^"\']+homechef[^"\']*\.jpg[^"\']*)["\'][^>]*>',
        r'<img[^>]+src=["\']([^"\']+homechef[^"\']*\.jpeg[^"\']*)["\'][^>]*>',
        r'<img[^>]+src=["\']([^"\']+homechef[^"\']*\.png[^"\']*)["\'][^>]*>',
    ]
    
    for pattern in img_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for url in matches:
            # Clean up the URL
            clean_url = url.strip()
            if clean_url and 'homechef' in clean_url.lower():
                image_urls.append(clean_url)
                logger.info(f"Found image URL: {clean_url}")
    
    # Also look for background images in style attributes
    bg_pattern = r'background-image:\s*url\(["\']?([^"\']+homechef[^"\']*)["\']?\)'
    bg_matches = re.findall(bg_pattern, content, re.IGNORECASE)
    for url in bg_matches:
        clean_url = url.strip()
        if clean_url:
            image_urls.append(clean_url)
            logger.info(f"Found background image URL: {clean_url}")
    
    return image_urls


def extract_meals_from_text(content: str, date_shipped: str) -> List[Dict]:
    """Extract meal information from plain text email content (original logic)"""
    meals = []
    
    logger.info("Extracting meals from plain text content")
    
    # First, decode quoted-printable encoding if present
    content = decode_quoted_printable(content)
    logger.info(f"After decoding, content preview (first 2000 chars): {content[:2000]}")
    
    # Find the meal section between "What's In Your Box" and "View Full Menu"
    start_pattern = r"What.?s In Your Box"
    end_pattern = r"View Full Menu"
    
    start_match = re.search(start_pattern, content, re.IGNORECASE)
    end_match = re.search(end_pattern, content, re.IGNORECASE)
    
    if start_match and end_match:
        meal_section = content[start_match.end():end_match.start()]
        logger.info(f"Found meal section between markers, length: {len(meal_section)}")
        logger.info(f"Meal section preview: {meal_section[:300]}")
    else:
        logger.warning("Could not find meal section markers, using full content")
        meal_section = content
    
    # Extract meals from the section
    # Look for patterns like:
    # > Sheet Pan Potato-Crusted Chicken
    # > with chive crema and cheesy potatoes
    
    # Split by lines and process
    lines = meal_section.split('\n')
    current_meal = None
    logger.info(f"Processing {len(lines)} lines from meal section")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines and URL lines
        if not line or 'https://' in line or line.startswith('>=20'):
            continue
        
        # Remove leading > characters
        original_line = line
        line = re.sub(r'^>\s*', '', line)
        
        # Skip if still empty
        if not line:
            continue
        
        logger.info(f"Line {i}: '{original_line}' -> '{line}'")
        
        # Check if this looks like a meal title (starts with capital, doesn't start with "with")
        if (line and line[0].isupper() and 
            not line.lower().startswith('with ') and 
            not line.lower().startswith('view ') and
            len(line) > 3):
            
            # Save previous meal if we have one
            if current_meal and current_meal['meal_name']:
                logger.info(f"Saving meal: {current_meal['meal_name']}")
                meals.append(current_meal)
            
            # Start new meal
            logger.info(f"Starting new meal: {line}")
            current_meal = {
                'meal_name': line.strip(),
                'description': '',
                'thumbnail_url': 'https://asset.homechef.com/uploads/meal/default-placeholder.jpg',  # Default placeholder
                'date_shipped': date_shipped,
                'status': 'available'
            }
            
        elif current_meal and line:
            # This is likely a description line
            logger.info(f"Adding description to {current_meal['meal_name']}: {line}")
            if line.lower().startswith('with '):
                current_meal['description'] = line
            elif not current_meal['description'] and not line.lower().startswith('view '):
                # If no description yet, use this line (but skip lines like "View Full Menu")
                if line.lower().startswith('with '):
                    current_meal['description'] = line
                else:
                    current_meal['description'] = f"with {line}"
            elif line.endswith('included'):
                # Handle special cases like "2 sandwiches included"
                current_meal['description'] += f" ({line})"
    
    # Don't forget the last meal
    if current_meal and current_meal['meal_name']:
        logger.info(f"Saving final meal: {current_meal['meal_name']}")
        meals.append(current_meal)
    
    # Extract thumbnail URLs from the content
    image_urls = extract_image_urls_from_text(content)
    
    # Try to assign thumbnail URLs to meals
    for i, meal in enumerate(meals):
        if i < len(image_urls):
            meal['thumbnail_url'] = image_urls[i]
            logger.info(f"Assigned thumbnail to {meal['meal_name']}: {image_urls[i]}")
        else:
            # Use placeholder for allowed domain
            meal['thumbnail_url'] = "https://asset.homechef.com/uploads/meal/default-placeholder.jpg"
            logger.info(f"Using placeholder thumbnail for {meal['meal_name']}")
    
    # Clean up meal names and descriptions
    for meal in meals:
        meal['meal_name'] = re.sub(r'[^\w\s&-]', '', meal['meal_name']).strip()
        # Don't remove 'with' if the description starts with it
        if not meal['description'].lower().startswith('with '):
            meal['description'] = meal['description'].strip()
        else:
            meal['description'] = meal['description'].strip()
    
    # Filter out invalid meals
    valid_meals = [
        meal for meal in meals 
        if (meal['meal_name'] and 
            len(meal['meal_name']) > 3 and 
            meal['meal_name'].lower() not in ['menu', 'order', 'view', 'explore', 'full'])
    ]
    
    logger.info(f"Extracted {len(valid_meals)} valid meals from text content")
    return valid_meals


def extract_image_urls_from_text(content: str) -> List[str]:
    """Extract thumbnail URLs from plain text content"""
    # Look for actual image URLs (asset.homechef.com or image.e.homechef.com)
    actual_image_patterns = [
        r'https://asset\.homechef\.com/uploads/meal/[^"\s\>\<\)]+',
        r'https://image\.e\.homechef\.com/[^"\s\>\<\)]+',
        r'https://asset\.homechef\.com[^"\s\>\<\)]*\.jpg',
        r'https://asset\.homechef\.com[^"\s\>\<\)]*\.jpeg',
        r'https://asset\.homechef\.com[^"\s\>\<\)]*\.png',
    ]
    
    image_urls = []
    for pattern in actual_image_patterns:
        logger.info(f"Trying image pattern: {pattern}")
        found_urls = re.findall(pattern, content)
        logger.info(f"Found {len(found_urls)} URLs with pattern: {found_urls}")
        image_urls.extend(found_urls)
    
    # Also look for any URLs that might be in the content (for debugging)
    all_urls = re.findall(r'https://[^"\s\>\<\)]+', content)
    logger.info(f"All URLs found in content ({len(all_urls)}): {all_urls[:10]}")  # Show first 10
    
    # Filter for any homechef URLs
    homechef_urls = [url for url in all_urls if 'homechef' in url.lower()]
    logger.info(f"All Home Chef URLs found ({len(homechef_urls)}): {homechef_urls}")
    
    logger.info(f"Final valid image URLs found: {len(image_urls)}")
    for i, url in enumerate(image_urls):
        logger.info(f"Image URL {i+1}: {url}")
    
    return image_urls


def decode_quoted_printable(content: str) -> str:
    """Decode quoted-printable encoding (=20, =3D, etc.)"""
    try:
        import quopri
        # First try proper quoted-printable decoding
        try:
            decoded = quopri.decodestring(content.encode('ascii')).decode('utf-8')
            return decoded
        except:
            pass
        
        # Manual decoding for common patterns
        replacements = {
            '=20': ' ',
            '=3D': '=',
            '=0D=0A': '\n',
            '=0A': '\n',
            '=0D': '\r',
            '=E2=80=99': "'",  # Right single quotation mark
            '=E2=80=93': '–',  # En dash
            '=E2=80=94': '—',  # Em dash
        }
        
        for encoded, decoded in replacements.items():
            content = content.replace(encoded, decoded)
        
        return content
        
    except Exception as e:
        logger.warning(f"Failed to decode quoted-printable: {str(e)}")
        return content