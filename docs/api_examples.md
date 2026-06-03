# MCP API Examples

**Purpose:** Provide copy-paste curl examples for all MCP protocol endpoints

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Base URL

```bash
# Local development
BASE_URL="http://localhost:8000/mcp"

# Production (with auth)
BASE_URL="https://mcp.example.com/ltem/mcp"
AUTH="user:password"
```

---

## 1. Initialize Session

**Purpose:** Start MCP session and get capabilities

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {
        "name": "curl-client",
        "version": "1.0.0"
      }
    }
  }' | jq .
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {}
    },
    "serverInfo": {
      "name": "LTEM Database",
      "version": "1.2.0"
    }
  }
}
```

**Extract Session ID:**

```bash
# Session ID is in Mcp-Session header
SESSION_ID=$(curl -s -D - $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | grep -i "mcp-session" | cut -d: -f2 | tr -d ' \r')

echo "Session ID: $SESSION_ID"
```

---

## 2. List Tools

**Purpose:** Get all available MCP tools

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }' | jq '.result.tools[] | {name: .name, description: .description}'
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_regions",
        "description": "List all surveyed regions",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      },
      {
        "name": "get_biomass_summary",
        "description": "Get biomass summary statistics",
        "inputSchema": {
          "type": "object",
          "properties": {
            "region": {"type": "string"}
          }
        }
      }
    ]
  }
}
```

---

## 3. Call Tool (No Parameters)

**Purpose:** Call a tool that requires no parameters

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_regions",
      "arguments": {}
    }
  }' | jq .
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"regions\": [\"Cabo Pulmo\", \"La Paz\", \"Loreto\"]}"
      }
    ]
  }
}
```

---

## 4. Call Tool (With Parameters)

**Purpose:** Call a tool with optional parameters

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "get_biomass_summary",
      "arguments": {
        "region": "La Paz"
      }
    }
  }' | jq '.result.content[0].text | fromjson'
```

**Expected Response:**

```json
{
  "data": {
    "mean_biomass": 125.5,
    "std_biomass": 45.2,
    "n_observations": 1500
  },
  "meta": {
    "region": "La Paz"
  }
}
```

---

## 5. List Resources

**Purpose:** Get all available MCP resources

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "resources/list",
    "params": {}
  }' | jq '.result.resources[] | {uri: .uri, name: .name}'
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "resources": [
      {
        "uri": "ltem://schema/tables",
        "name": "Database Schema",
        "mimeType": "application/json"
      },
      {
        "uri": "ltem://data-dictionary",
        "name": "Data Dictionary",
        "mimeType": "text/markdown"
      },
      {
        "uri": "ltem://metadata/manifest",
        "name": "Metadata Manifest",
        "mimeType": "application/json"
      }
    ]
  }
}
```

---

## 6. Read Resource

**Purpose:** Get content of a specific resource

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 6,
    "method": "resources/read",
    "params": {
      "uri": "ltem://schema/tables"
    }
  }' | jq '.result.contents[0].text | fromjson'
```

**Expected Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": {
    "contents": [
      {
        "uri": "ltem://schema/tables",
        "mimeType": "application/json",
        "text": "{\"tables\": [\"ltem_historical_database\"]}"
      }
    ]
  }
}
```

---

## 7. Server-Sent Events (SSE)

**Purpose:** Use SSE for streaming responses

```bash
curl -N $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 7,
    "method": "tools/call",
    "params": {
      "name": "get_observations",
      "arguments": {"limit": 100}
    }
  }'
```

**Expected Response (SSE format):**

```
event: message
data: {"jsonrpc":"2.0","id":7,"result":{"content":[{"type":"text","text":"..."}]}}

```

---

## Complete Workflow Example

**Scenario:** Get regions, then get biomass summary for each region

```bash
#!/bin/bash
set -e

BASE_URL="http://localhost:8000/mcp"
AUTH="user:password"

# 1. Initialize session
echo "1. Initializing session..."
INIT_RESPONSE=$(curl -s -D - $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "workflow", "version": "1.0"}
    }
  }')

SESSION_ID=$(echo "$INIT_RESPONSE" | grep -i "mcp-session" | cut -d: -f2 | tr -d ' \r')
echo "Session ID: $SESSION_ID"

# 2. Get regions
echo -e "\n2. Getting regions..."
REGIONS=$(curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_regions",
      "arguments": {}
    }
  }' | jq -r '.result.content[0].text | fromjson | .regions[]')

echo "Regions: $REGIONS"

# 3. Get biomass for each region
echo -e "\n3. Getting biomass summaries..."
for region in $REGIONS; do
  echo -e "\nRegion: $region"
  curl -s $BASE_URL \
    -u $AUTH \
    -H "Content-Type: application/json" \
    -H "Mcp-Session: $SESSION_ID" \
    -d "{
      \"jsonrpc\": \"2.0\",
      \"id\": 3,
      \"method\": \"tools/call\",
      \"params\": {
        \"name\": \"get_biomass_summary\",
        \"arguments\": {
          \"region\": \"$region\"
        }
      }
    }" | jq '.result.content[0].text | fromjson'
done

echo -e "\n✓ Workflow complete"
```

---

## Error Handling

### Invalid Method

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "invalid/method",
    "params": {}
  }' | jq .
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

### Invalid Parameters

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_biomass_summary",
      "arguments": {
        "invalid_param": "value"
      }
    }
  }' | jq .
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

### Tool Not Found

```bash
curl -s $BASE_URL \
  -u $AUTH \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: $SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "nonexistent_tool",
      "arguments": {}
    }
  }' | jq .
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32602,
    "message": "Tool not found: nonexistent_tool"
  }
}
```

---

## Testing Tools

### Quick Smoke Test

```bash
#!/bin/bash
# Test basic MCP functionality

BASE_URL="http://localhost:8000/mcp"

echo "Testing MCP server..."

# Initialize
echo -n "1. Initialize: "
curl -s $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  | jq -e '.result.serverInfo.name' > /dev/null && echo "✓" || echo "✗"

# List tools
echo -n "2. List tools: "
curl -s $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | jq -e '.result.tools | length > 0' > /dev/null && echo "✓" || echo "✗"

# List resources
echo -n "3. List resources: "
curl -s $BASE_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"resources/list","params":{}}' \
  | jq -e '.result.resources | length > 0' > /dev/null && echo "✓" || echo "✗"

echo "Done!"
```

---

## Python Client Example

```python
import requests
import json

class MCPClient:
    def __init__(self, base_url, auth=None):
        self.base_url = base_url
        self.auth = auth
        self.session_id = None
        self.request_id = 0
    
    def _request(self, method, params=None):
        self.request_id += 1
        headers = {"Content-Type": "application/json"}
        if self.session_id:
            headers["Mcp-Session"] = self.session_id
        
        payload = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers,
            auth=self.auth
        )
        
        # Extract session ID from first request
        if not self.session_id and "Mcp-Session" in response.headers:
            self.session_id = response.headers["Mcp-Session"]
        
        return response.json()
    
    def initialize(self):
        return self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "python-client", "version": "1.0"}
        })
    
    def list_tools(self):
        return self._request("tools/list")
    
    def call_tool(self, name, arguments=None):
        return self._request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
    
    def list_resources(self):
        return self._request("resources/list")
    
    def read_resource(self, uri):
        return self._request("resources/read", {"uri": uri})

# Usage
client = MCPClient("http://localhost:8000/mcp")
client.initialize()

# List tools
tools = client.list_tools()
print(f"Available tools: {len(tools['result']['tools'])}")

# Call tool
result = client.call_tool("get_regions")
data = json.loads(result['result']['content'][0]['text'])
print(f"Regions: {data['regions']}")
```

---

## JavaScript Client Example

```javascript
class MCPClient {
  constructor(baseUrl, auth = null) {
    this.baseUrl = baseUrl;
    this.auth = auth;
    this.sessionId = null;
    this.requestId = 0;
  }

  async request(method, params = {}) {
    this.requestId++;
    
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.sessionId) {
      headers['Mcp-Session'] = this.sessionId;
    }
    
    if (this.auth) {
      headers['Authorization'] = `Basic ${btoa(this.auth)}`;
    }
    
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        jsonrpc: '2.0',
        id: this.requestId,
        method,
        params
      })
    });
    
    // Extract session ID
    if (!this.sessionId && response.headers.has('Mcp-Session')) {
      this.sessionId = response.headers.get('Mcp-Session');
    }
    
    return response.json();
  }

  async initialize() {
    return this.request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'js-client', version: '1.0' }
    });
  }

  async listTools() {
    return this.request('tools/list');
  }

  async callTool(name, arguments = {}) {
    return this.request('tools/call', { name, arguments });
  }
}

// Usage
const client = new MCPClient('http://localhost:8000/mcp');
await client.initialize();

const tools = await client.listTools();
console.log(`Available tools: ${tools.result.tools.length}`);

const result = await client.callTool('get_regions');
const data = JSON.parse(result.result.content[0].text);
console.log(`Regions: ${data.regions}`);
```

---

## See Also

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [docs/troubleshooting.md](troubleshooting.md) - Common issues
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment guide

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
