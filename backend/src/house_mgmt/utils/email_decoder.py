"""
Email Decoder Utility
Helper function to decode and preview email files the same way the Lambda does
Run this locally to see exactly what the Lambda processes
"""
import email
import base64
import re
import quopri
from datetime import datetime
from typing import Dict


def decode_quoted_printable(content: str) -> str:
    """Decode quoted-printable encoding (=20, =3D, etc.) - same as Lambda"""
    try:
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
        print(f"Failed to decode quoted-printable: {str(e)}")
        return content


def get_email_body(msg) -> Dict[str, str]:
    """Extract both HTML and plain text body content from email message"""
    html_body = None
    plain_body = None
    
    if msg.is_multipart():
        # Find text/plain and text/html parts
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type in ['text/plain', 'text/html']:
                # Check for base64 encoding in headers
                encoding = part.get('Content-Transfer-Encoding', '').lower()
                payload = part.get_payload(decode=True if encoding == 'base64' else False)
                
                if payload:
                    try:
                        if isinstance(payload, bytes):
                            decoded = payload.decode('utf-8')
                        else:
                            decoded = payload
                    except UnicodeDecodeError:
                        if isinstance(payload, bytes):
                            decoded = payload.decode('latin-1')
                        else:
                            decoded = payload
                    
                    # Store both versions
                    if content_type == 'text/html':
                        html_body = decoded
                    elif content_type == 'text/plain':
                        plain_body = decoded
        
        return {
            'html': html_body or "",
            'plain': plain_body or ""
        }
    else:
        # Single part message
        content_type = msg.get_content_type()
        encoding = msg.get('Content-Transfer-Encoding', '').lower()
        payload = msg.get_payload(decode=True if encoding == 'base64' else False)
        
        if payload:
            try:
                if isinstance(payload, bytes):
                    content = payload.decode('utf-8')
                else:
                    content = payload
            except UnicodeDecodeError:
                if isinstance(payload, bytes):
                    content = payload.decode('latin-1')
                else:
                    content = payload
            
            if content_type == 'text/html':
                return {'html': content, 'plain': ""}
            else:
                return {'html': "", 'plain': content}
        
        return {'html': "", 'plain': ""}


def is_base64_encoded(content: str) -> bool:
    """Check if content appears to be base64 encoded - same as Lambda"""
    if not content:
        return False
    
    # Basic heuristic: if content is mostly base64 characters
    base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
    content_chars = set(content.replace('\n', '').replace('\r', ''))
    
    return len(content_chars.intersection(base64_chars)) / len(content_chars) > 0.8 if content_chars else False


def decode_base64_content(content: str) -> str:
    """Decode base64 content - same as Lambda"""
    try:
        # Clean up content (remove whitespace)
        cleaned = re.sub(r'\s+', '', content)
        decoded = base64.b64decode(cleaned)
        return decoded.decode('utf-8')
    except Exception as e:
        print(f"Failed to decode base64 content: {str(e)}")
        return content


def preview_email_file(file_path: str, output_file: str = None) -> Dict[str, str]:
    """
    Preview an email file the same way the Lambda processes it
    
    Args:
        file_path: Path to the email file or S3 URL
        output_file: Optional path to save the decoded content
    
    Returns:
        Dictionary with decoded content and analysis
    """
    try:
        # Check if it's an S3 URL
        if file_path.startswith('http') and 's3' in file_path.lower():
            print(f"📧 Downloading from S3 URL: {file_path}")
            import urllib.request
            with urllib.request.urlopen(file_path) as response:
                email_content = response.read().decode('utf-8')
        else:
            # Read the email file locally
            print(f"📧 Processing email file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                email_content = f.read()
        
        print(f"📏 Raw file size: {len(email_content)} characters")
        
        # Parse email message (same as Lambda)
        msg = email.message_from_string(email_content)
        
        # Get both HTML and plain text versions
        email_bodies = get_email_body(msg)
        
        # Test both versions
        for content_type in ['plain', 'html']:
            if email_bodies[content_type]:
                print(f"\n🔍 Testing {content_type.upper()} version:")
                print(f"📏 {content_type} body size: {len(email_bodies[content_type])} characters")
                
                # Test date extraction
                test_date_extraction(email_bodies[content_type])
                
                # Test meal extraction
                test_meal_extraction(email_bodies[content_type])
        
        # Use plain text for main analysis (same as Lambda)
        email_body = email_bodies['plain'] if email_bodies['plain'] else email_bodies['html']
        
        # Decode quoted-printable if needed
        decoded_content = decode_quoted_printable(email_body)
        
        print(f"📏 Final decoded content size: {len(decoded_content)} characters")
        
        # Analysis
        analysis = {
            'raw_content': email_content,
            'email_body': email_body,
            'decoded_content': decoded_content,
            'has_delivery': 'delivery will arrive on' in decoded_content.lower(),
            'has_will_arrive': 'will arrive on' in decoded_content.lower(),
            'has_december': 'december' in decoded_content.lower(),
            'has_whats_in_box': 'what' in decoded_content.lower() and 'in your box' in decoded_content.lower(),
            'has_view_full_menu': 'view full menu' in decoded_content.lower(),
            'has_week_of': 'week of' in decoded_content.lower(),
        }
        
        # Find key sections
        print("\n🔍 Content Analysis:")
        print(f"   ✅ Contains 'delivery will arrive on': {analysis['has_delivery']}")
        print(f"   ✅ Contains 'will arrive on': {analysis['has_will_arrive']}")
        print(f"   ✅ Contains 'week of': {analysis['has_week_of']}")
        print(f"   ✅ Contains 'december': {analysis['has_december']}")
        print(f"   ✅ Contains 'what's in your box': {analysis['has_whats_in_box']}")
        print(f"   ✅ Contains 'view full menu': {analysis['has_view_full_menu']}")
        
        # Show delivery context if found
        if analysis['has_will_arrive']:
            delivery_matches = re.findall(r'.{0,100}will arrive on.{0,100}', decoded_content, re.IGNORECASE)
            print(f"\n📅 'Will arrive on' contexts found ({len(delivery_matches)}):")
            for i, match in enumerate(delivery_matches):
                print(f"   {i+1}: {match}")
        
        # Show week of context if found
        if analysis['has_week_of']:
            week_matches = re.findall(r'.{0,50}week of.{0,50}', decoded_content, re.IGNORECASE)
            print(f"\n📅 'Week of' contexts found ({len(week_matches)}):")
            for i, match in enumerate(week_matches):
                print(f"   {i+1}: {match}")
        
        # Show meal section preview
        start_match = re.search(r"What.?s In Your Box", decoded_content, re.IGNORECASE)
        end_match = re.search(r"View Full Menu", decoded_content, re.IGNORECASE)
        
        if start_match and end_match:
            meal_section = decoded_content[start_match.end():end_match.start()]
            print(f"\n🍽️  Meal section preview (first 800 chars):")
            print("=" * 80)
            print(meal_section[:800])
            print("=" * 80)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== RAW EMAIL CONTENT ===\n\n")
                f.write(email_content)
                f.write(f"\n\n=== PLAIN TEXT BODY ===\n\n")
                f.write(email_bodies['plain'])
                f.write(f"\n\n=== HTML BODY ===\n\n")
                f.write(email_bodies['html'])
                f.write("\n\n=== DECODED CONTENT ===\n\n")
                f.write(decoded_content)
                f.write("\n\n=== MEAL SECTION ===\n\n")
                if start_match and end_match:
                    f.write(meal_section)
                else:
                    f.write("Meal section markers not found")
            
            print(f"\n💾 Saved full decoded content to: {output_file}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error processing email: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}


def test_date_extraction(content: str):
    """Test date extraction patterns on content"""
    print("\n🧪 Testing Date Extraction Patterns:")
    
    # Decode quoted-printable first
    content = decode_quoted_printable(content)
    
    # Test patterns from Lambda
    delivery_patterns = [
        r"will arrive on \w+,\s+(\w+\s+\d+)",           
        r"will arrive on (\w+,\s+\w+\s+\d+)",           
        r"delivery will arrive on \w+,\s+(\w+\s+\d+)",  
        r"delivery will arrive on (\w+,\s+\w+\s+\d+)",  
        r"arrive on \w+,\s+(\w+\s+\d+)",                
        r"arrive on (\w+,\s+\w+\s+\d+)",                
    ]
    
    for pattern in delivery_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            date_str = match.group(1)
            print(f"   ✅ Pattern '{pattern}' matched: '{date_str}'")
            
            # Test date parsing
            try:
                parsed_date = parse_month_day_to_date(date_str)
                print(f"      → Parsed to: {parsed_date}")
            except Exception as e:
                print(f"      ❌ Failed to parse: {e}")
        else:
            print(f"   ❌ Pattern '{pattern}' - no match")
    
    # Test Week of pattern
    week_pattern = r"Week of \w+,\s+(\w+\s+\d+)"
    week_match = re.search(week_pattern, content, re.IGNORECASE)
    if week_match:
        date_str = week_match.group(1)
        print(f"   ✅ Week pattern matched: '{date_str}'")
        try:
            parsed_date = parse_month_day_to_date(date_str)
            print(f"      → Parsed to: {parsed_date}")
        except Exception as e:
            print(f"      ❌ Failed to parse: {e}")
    else:
        print(f"   ❌ Week pattern - no match")


def test_meal_extraction(content: str):
    """Test meal extraction on content"""
    print("\n🧪 Testing Meal Extraction:")
    
    # Find meal section
    start_match = re.search(r"What.?s In Your Box", content, re.IGNORECASE)
    end_match = re.search(r"View Full Menu", content, re.IGNORECASE)
    
    if start_match and end_match:
        meal_section = content[start_match.end():end_match.start()]
        print(f"   ✅ Found meal section: {len(meal_section)} chars")
        
        # Look for potential meal lines
        lines = meal_section.split('\n')
        meal_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove leading > characters
            line = re.sub(r'^>\s*', '', line)
            if not line:
                continue
                
            # Check if looks like a meal title
            if (line and line[0].isupper() and 
                not line.lower().startswith('with ') and 
                not line.lower().startswith('view ') and
                len(line) > 3):
                meal_lines.append(line)
        
        print(f"   ✅ Found {len(meal_lines)} potential meals:")
        for i, meal in enumerate(meal_lines):
            print(f"      {i+1}. {meal}")
    else:
        print("   ❌ Could not find meal section markers")


def parse_month_day_to_date(date_str: str) -> str:
    """Parse month name and day to ISO date format - same as Lambda"""
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
                
                # Determine year - if month is before current month, it's next year
                current_date = datetime.now()
                year = current_date.year
                
                # If the month is before current month, assume next year
                if month < current_date.month:
                    year += 1
                # If same month but day is before current day, assume next year
                elif month == current_date.month and day < current_date.day:
                    year += 1
                
                return f"{year}-{month:02d}-{day:02d}"
    
    except Exception as e:
        print(f"Failed to parse date '{date_str}': {str(e)}")
    
    # Fallback to current date
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d')


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python email_decoder.py <email_file_path> [output_file_path]")
        print("\nExample:")
        print("  python email_decoder.py raw_email.txt decoded_email.txt")
    else:
        file_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        preview_email_file(file_path, output_file)