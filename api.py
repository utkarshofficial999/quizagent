from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import yaml
import uvicorn

from src.browser import BrowserManager
from src.quiz_solver import QuizSolver

app = FastAPI(title="Quiz Solver Agent")

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quiz Solver Agent</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }
            .container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; width: 100%; max-width: 500px; }
            h1 { color: #333; margin-bottom: 10px; text-align: center; }
            .subtitle { color: #666; text-align: center; margin-bottom: 30px; font-size: 14px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
            input, textarea { width: 100%; padding: 12px 15px; border: 2px solid #ddd; border-radius: 10px; font-size: 14px; transition: border-color 0.3s; }
            input:focus, textarea:focus { outline: none; border-color: #667eea; }
            textarea { resize: vertical; min-height: 100px; }
            button { width: 100%; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
            button:hover { transform: translateY(-2px); box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4); }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .result { margin-top: 20px; padding: 15px; border-radius: 10px; display: none; }
            .result.success { background: #d4edda; color: #155724; display: block; }
            .result.error { background: #f8d7da; color: #721c24; display: block; }
            .status { text-align: center; margin-top: 20px; color: #666; }
            .spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 10px; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Quiz Solver Agent</h1>
            <p class="subtitle">Automatically solve Microsoft Forms, Google Forms & more</p>
            
            <form id="quizForm">
                <div class="form-group">
                    <label>Quiz URL *</label>
                    <input type="url" name="url" required placeholder="https://forms.cloud.microsoft/...">
                </div>
                
                <div class="form-group">
                    <label>Email (optional, for login)</label>
                    <input type="email" name="email" placeholder="your@email.com">
                </div>
                
                <div class="form-group">
                    <label>Password (optional, for login)</label>
                    <input type="password" name="password" placeholder="Your password">
                </div>
                
                <div class="form-group">
                    <label>Name (optional)</label>
                    <input type="text" name="name" placeholder="Your name">
                </div>
                
                <div class="form-group">
                    <label>Class/Section (optional)</label>
                    <input type="text" name="class_section" placeholder="e.g., CSE-25">
                </div>
                
                <div class="form-group">
                    <label>Roll Number (optional)</label>
                    <input type="text" name="roll_no" placeholder="Your roll number">
                </div>
                
                <button type="submit" id="submitBtn">Solve Quiz</button>
            </form>
            
            <div class="status" id="status" style="display:none;">
                <span class="spinner"></span>
                <span id="statusText">Solving quiz...</span>
            </div>
            
            <div class="result" id="result"></div>
        </div>
        
        <script>
            document.getElementById('quizForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const data = {
                    url: formData.get('url'),
                    email: formData.get('email'),
                    password: formData.get('password'),
                    name: formData.get('name'),
                    class_section: formData.get('class_section'),
                    roll_no: formData.get('roll_no')
                };
                
                document.getElementById('submitBtn').disabled = true;
                document.getElementById('status').style.display = 'block';
                document.getElementById('result').style.display = 'none';
                
                try {
                    const response = await fetch('/solve', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        document.getElementById('result').className = 'result success';
                        document.getElementById('result').textContent = result.message;
                    } else {
                        document.getElementById('result').className = 'result error';
                        document.getElementById('result').textContent = result.message;
                    }
                } catch (err) {
                    document.getElementById('result').className = 'result error';
                    document.getElementById('result').textContent = 'Error: ' + err.message;
                }
                
                document.getElementById('submitBtn').disabled = false;
            });
        </script>
    </body>
    </html>
    """


@app.post("/solve")
async def solve_quiz(data: dict):
    url = data.get("url", "")
    email = data.get("email", "")
    password = data.get("password", "")
    name = data.get("name", "")
    class_section = data.get("class_section", "")
    roll_no = data.get("roll_no", "")
    
    if not url:
        return {"status": "error", "message": "URL is required"}
    
    credentials = {}
    if email and password:
        credentials["microsoft"] = {"email": email, "password": password}
    
    browser = None
    try:
        browser = BrowserManager(config)
        await browser.start()
        
        solver = QuizSolver(browser, config)
        
        is_microsoft = "forms.office.com" in url.lower() or "forms.microsoft.com" in url.lower() or "forms.cloud.microsoft" in url.lower()
        
        if is_microsoft and credentials:
            await browser.navigate("https://login.microsoft.com/")
            await asyncio.sleep(3)
            login_success = await solver.login_microsoft(credentials["microsoft"])
            if login_success:
                await browser.navigate(url)
                await asyncio.sleep(8)
        
        result = await solver.solve(url)
        
        await browser.close()
        
        if result.get("errors"):
            return {"status": "error", "message": f"Completed with errors: {result['errors']}"}
        
        return {"status": "success", "message": "Quiz completed successfully!"}
        
    except Exception as e:
        if browser:
            await browser.close()
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)