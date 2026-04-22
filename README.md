# Quiz Solver Agent 🚀

An AI-powered automation tool that automatically logs into Microsoft Forms, Google Forms, Kahoot!, and other quiz platforms to solve and submit quizzes.

## Features

- 🤖 **Automatic Login** - Handles Microsoft, Google authentication
- 📝 **Auto-fill Forms** - Fills name, class, roll number automatically  
- ✅ **Multiple Platforms** - Microsoft Forms, Google Forms, Kahoot!
- 🌐 **Web Interface** - Easy-to-use web interface

## Quick Start

### Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the web server
python api.py
```

Then open http://localhost:8000 in your browser.

### Using Docker

```bash
# Build the image
docker build -t quiz-solver .

# Run the container
docker run -p 8000:8000 quiz-solver
```

Then open http://localhost:8000

## API Usage

### Web Interface
Open http://localhost:8000 in your browser.

### Python Client

```python
import requests

data = {
    "url": "https://forms.cloud.microsoft/...",
    "email": "your@email.com",
    "password": "yourpassword",
    "name": "Your Name",
    "class_section": "CSE-25",
    "roll_no": "1234567890"
}

response = requests.post("http://localhost:8000/solve", json=data)
print(response.json())
```

### cURL

```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://forms.cloud.microsoft/...",
    "email": "your@email.com",
    "password": "yourpassword",
    "name": "Your Name"
  }'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 8000 |
| HEADLESS | Run browser headless | true |

## Supported Platforms

- ✅ Microsoft Forms (forms.office.com, forms.cloud.microsoft)
- ✅ Google Forms (docs.google.com/forms)
- ✅ Kahoot! (kahoot.it, kahoot.com)

## Deployment

### Render.com
1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `python api.py`
4. Add environment variable: `PORT=8000`

### Railway
```bash
railway init
railway up
```

### Heroku
```bash
heroku create quiz-solver
heroku stack:set container
heroku push heroku main
```

## Security Notes

⚠️ **Important:**
- Never commit passwords to git
- Use environment variables for sensitive data
- The browser runs on the server - no local setup needed for end users

## License

MIT