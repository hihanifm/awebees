# AI Server Interaction Logging

## Overview
Enhanced logging for all AI server interactions to capture debugging information that isn't visible in the browser.

## What's Logged

### Test Connection (`test_connection()`)

**Success Path:**
```
INFO: AI Service: Testing connection to http://server:port/v1/chat/completions
DEBUG: AI Service: Test using model=gpt-4o-mini
INFO: AI Service: Test connection received status 200
INFO: AI Service: Test connection successful - model=gpt-4o-mini
```

**Error Paths:**
```
WARNING: AI Service: Test connection failed - service not configured
ERROR: AI Service: Test connection failed (404) - {error details}
ERROR: AI Service: Test connection failed (500) - {error details}
ERROR: AI Service: Test connection HTTP status error - 404: {response text}
ERROR: AI Service: Test connection request error - ConnectTimeout: {details}
ERROR: AI Service: Test connection unexpected error - ValueError: {details}
```

### AI Analysis (`analyze_stream()`)

**Request Logging:**
```
INFO: AI Service: Starting streaming analysis (model: gpt-4o-mini, prompt_type: explain)
INFO: AI Service: Sending request to http://server:port/v1/chat/completions
DEBUG: AI Service: Model=gpt-4o-mini, max_tokens=1000, temperature=0.5
DEBUG: AI Service: System prompt length: 245 chars
DEBUG: AI Service: User prompt length: 5432 chars
```

**Response Logging:**
```
INFO: AI Service: Received response with status 200
DEBUG: AI Service: Stream completed - received 45 chunks, 1234 characters
INFO: AI Service: Streaming analysis complete - 45 chunks, 1234 characters
```

**Error Logging:**
```
ERROR: AI Service: HTTP error 404: Endpoint not found
ERROR: AI Service: API returned error in stream: Context length exceeded
ERROR: AI Service: Full error data: {...}
WARNING: AI Service: Failed to parse SSE chunk: Invalid JSON
DEBUG: AI Service: Problematic data: {truncated data}
ERROR: AI Service: HTTP error - HTTP 404. Hint: Try adding '/v1'...
ERROR: AI Service: Request URL was: http://server:port/chat/completions
ERROR: AI Service: Request error - ConnectTimeout: Connection timeout
ERROR: AI Service: Unexpected error during streaming - Exception: {details}
```

## Log Levels

### DEBUG (Development Default)
- Request details (model, tokens, temperature)
- Prompt lengths
- Streaming metrics (chunk counts, character counts)
- Problematic data snippets

### INFO (Production Default)
- Connection attempts
- Response status codes
- Success/completion messages

### WARNING
- JSON parsing errors
- Non-critical issues

### ERROR
- HTTP errors (404, 500, etc.)
- API errors from LM Studio/OpenAI
- Connection failures
- Unexpected exceptions

## Helpful Hints in Errors

The logging system automatically detects common misconfigurations:

1. **Missing /v1 suffix:**
   ```
   ERROR: Connection failed (404). Hint: Try adding '/v1' to your base URL: http://server:34005/v1
   ```

2. **Endpoint errors:**
   ```
   ERROR: Unexpected endpoint. Hint: Your base URL might be missing '/v1'
   ```

3. **Context length errors:**
   ```
   ERROR: The number of tokens to keep from the initial prompt is greater than the context length
   ```

## Debugging Workflow

1. **Check backend logs:**
   ```bash
   tail -f logs/backend.log | grep "AI Service"
   ```

2. **Filter by log level:**
   ```bash
   # Errors only
   grep ERROR logs/backend.log | grep "AI Service"
   
   # Full trace
   grep "AI Service" logs/backend.log
   ```

3. **Check request details:**
   ```bash
   # See what was sent
   grep "Sending request" logs/backend.log
   grep "System prompt length" logs/backend.log
   ```

4. **Monitor streaming:**
   ```bash
   # Watch chunks being received
   grep "chunks" logs/backend.log
   ```

## Benefits

✅ **Complete visibility** into AI server interactions  
✅ **Troubleshoot errors** not visible in browser  
✅ **Track performance** (chunk counts, character counts)  
✅ **Detect misconfigurations** with helpful hints  
✅ **Debug timeouts** and connection issues  
✅ **Audit API calls** in production  

## Files Modified

- `backend/app/services/ai_service.py` - Comprehensive logging for test_connection() and analyze_stream()

