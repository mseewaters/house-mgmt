import base64

# Test decode the base64 string from your email
base64_content = """DQpfX19fX19fX19fX19fX19fX19fX19fX19fX19fX19fXw0KRnJvbTogSG9tZSBDaGVmIDxzdXBw
b3J0QGUuaG9tZWNoZWYuY29tPg0KU2VudDogTW9uZGF5LCBOb3ZlbWJlciAyNCwgMjAyNSAxMjoy
NCBQTQ0KVG86IHNlZV93YXRlcnNAY29tY2FzdC5uZXQgPHNlZV93YXRlcnNAY29tY2FzdC5uZXQ+
DQpTdWJqZWN0OiBUaGlzIHdlZWvigJlzIG1lbnUganVzdCB3ZW50IGxpdmUhIEhlcmUncyB3aGF0
J3MgY29taW5nIG5leHQgd2Vlaw0KDQpNYWtlIHVwZGF0ZXMgYnkgRnJpZGF5IGF0IDEyUE0gQ1Qg
4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDi
gIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKA
h8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCH
wq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfC
rc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8Kt
zY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3N
jyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2P
IOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g
4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDi
gIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKA
h8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCH
wq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfC
rc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8Kt
zY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3N
jyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2P
IOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g
4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDi
gIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKA
h8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCH
wq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfC
rc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8Kt
zY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3N
jyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2P
IOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g
4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDi
gIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKAh8KtzY8g4oCHwq3NjyDigIfCrc2PIOKA"""

try:
    # Clean and decode
    cleaned = base64_content.replace('\n', '').replace('\r', '')
    decoded_bytes = base64.b64decode(cleaned)
    decoded_text = decoded_bytes.decode('utf-8')
    
    print("Successfully decoded! Here's the content:")
    print("=" * 50)
    print(decoded_text)
    print("=" * 50)
    
    # Look for key phrases
    if "delivery will arrive on" in decoded_text.lower():
        print("✅ Found 'delivery will arrive on'")
    if "december" in decoded_text.lower():
        print("✅ Found 'december'")
    if "what" in decoded_text.lower() and "box" in decoded_text.lower():
        print("✅ Found 'what's in your box'")
        
except Exception as e:
    print(f"Error decoding: {e}")