# brightmls

A Python package for interacting with the Bright MLS API.

## Features

- Connects to the Bright MLS API
- Fetches real estate data
- [Add more features as relevant]

## Installation

```bash
pip install brightmls
```

## Usage

```python
from brightmls import BrightMLS

# Example usage
client = BrightMLS(api_key="YOUR_API_KEY")
data = client.get_listings()
print(data)
```

## Integrating brightmls with n8n

n8n is a powerful workflow automation tool that allows you to connect APIs, databases, and more. To use brightmls in n8n, you can create a custom node or use the HTTP Request node to interact with the Bright MLS API via your package.

### Option 1: Using the HTTP Request Node

1. **Install n8n**  
   If you haven't already, install n8n:
   ```bash
   npm install n8n -g
   ```

2. **Start n8n**  
   ```bash
   n8n
   ```

3. **Create a new workflow**  
   - Open the n8n editor (usually at http://localhost:5678).
   - Add an "HTTP Request" node.
   - Configure the node to call your brightmls API endpoint (e.g., a FastAPI or Flask server you run that wraps your package).

4. **Set up authentication**  
   - Add your API key or credentials in the HTTP headers or query parameters as required by your API.

5. **Process the response**  
   - Use additional n8n nodes to process, store, or forward the data as needed.

### Option 2: Creating a Custom n8n Node

If you want a more integrated experience, you can create a custom n8n node:

1. **Clone the n8n repository**  
   ```bash
   git clone https://github.com/n8n-io/n8n.git
   cd n8n
   ```

2. **Create a new node**  
   - Follow the [n8n node creation guide](https://docs.n8n.io/integrations/creating-nodes/create-node/) to scaffold a new node.
   - Implement the logic to call your brightmls package (this may require running Python code from Node.js, e.g., via a REST API wrapper or using a tool like `python-shell`).

3. **Build and run n8n with your custom node**  
   - Build the project and start n8n.
   - Your custom node will now be available in the editor.

### Example: Exposing brightmls via FastAPI for n8n

If you want to use the HTTP Request node, you can expose your package via a simple API:

```python
# brightmls_api.py
from fastapi import FastAPI
from brightmls import BrightMLS

app = FastAPI()
client = BrightMLS(api_key="YOUR_API_KEY")

@app.get("/listings")
def get_listings():
    return client.get_listings()
```

Run your API:
```bash
uvicorn brightmls_api:app --reload
```

Then, in n8n, use the HTTP Request node to call `http://localhost:8000/listings`.

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Node Creation Guide](https://docs.n8n.io/integrations/creating-nodes/create-node/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

If you provide more details about your package’s endpoints or intended use, I can tailor the instructions and examples further. Would you like to add more specific usage examples or API details?