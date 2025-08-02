# CORS Configuration Examples

## Quick Decision Guide

### Use API Gateway CORS When:
- Same CORS policy for all endpoints
- Simple origin allowlist
- Want fastest OPTIONS responses
- Don't need dynamic CORS logic

### Use FastAPI CORS When:  
- Different CORS per endpoint
- Dynamic origin validation
- Complex credential handling
- Need fine-grained control

## Files Explained

### API Gateway CORS
- `sam-template-cors.yaml` - Add this to your template.yaml Globals section
- Remove ALL FastAPI CORS middleware when using this approach

### FastAPI CORS  
- `fastapi-cors-dev.py` - Development with localhost origins
- `fastapi-cors-prod.py` - Production with specific domain
- `fastapi-cors-open.py` - Public APIs without credentials
- Remove CORS section from template.yaml when using FastAPI approach

## Common CORS Errors & Solutions

### "Access-Control-Allow-Origin header contains multiple values"
**Cause**: CORS configured in both API Gateway AND FastAPI
**Solution**: Choose one approach, remove the other

### "CORS policy: Credentials include but origin is '*'"
**Cause**: Using `allow_origins=["*"]` with `allow_credentials=True`
**Solution**: Use specific origins or set `allow_credentials=False`

### "Response to preflight request doesn't pass access control check"
**Cause**: Missing required headers in CORS configuration
**Solution**: Add required headers like `Content-Type`, `Authorization`

### OPTIONS request returns 404
**Cause**: API Gateway CORS not configured, FastAPI not handling OPTIONS
**Solution**: Add CORS to template.yaml OR FastAPI middleware

## Testing CORS

```bash
# Test preflight request
curl -i -X OPTIONS \
     -H "Origin: https://yourdomain.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     https://your-api-url/endpoint

# Should return 200 OK with CORS headers
```

## Debugging Steps

1. **Check browser DevTools**:
   - Network tab → Look for OPTIONS request
   - Console → Check for CORS error messages
   - Response headers → Verify CORS headers present

2. **Check Lambda logs**:
   ```bash
   sam logs --tail --stack-name your-stack
   ```
   - If OPTIONS requests appear in logs → Using FastAPI CORS
   - If no OPTIONS in logs → Using API Gateway CORS

3. **Test with curl**:
   - Use curl to isolate browser vs server issues
   - Browsers enforce CORS, curl doesn't

4. **Verify deployment**:
   - Template changes require `sam deploy`
   - Code changes require `sam build && sam deploy`