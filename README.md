# AI Red-Flag Detector - Tester Version

This is a modified version of the AI Red-Flag Detector that allows testers to use their own OpenAI API keys instead of requiring a shared `.env` file.

## Features

✅ **User API Key Input** - Testers can enter their own OpenAI API key in the UI  
✅ **No .env Required** - Works without any configuration files  
✅ **Session-based Storage** - API key is only stored in browser session (not saved)  
✅ **Model Selection** - Choose from different OpenAI models  
✅ **Secure** - API key is masked and never stored permanently  

## How to Run

### Option 1: Run from app-tester directory
```bash
cd app-tester
streamlit run main.py
```

### Option 2: Run from project root
```bash
streamlit run app-tester/main.py
```

## Usage

1. **Start the application** using the command above
2. **Enter your OpenAI API key** in the sidebar
   - Get your API key at: https://platform.openai.com/api-keys
   - The key is stored only in your browser session
3. **Select a model** (default: gpt-4o-mini - recommended)
4. **Enter text** to classify in the main area
5. **Click "Analyze"** to get results

## API Key Security

- ✅ API key is only stored in Streamlit session state (browser memory)
- ✅ Never saved to disk or files
- ✅ Never transmitted to any server except OpenAI's API
- ✅ Cleared when you close the browser tab
- ✅ Masked display (shows only first 7 and last 4 characters)

## Requirements

Same as the main application:
```bash
pip install streamlit langchain-openai python-dotenv
```

Or install from project root:
```bash
pip install -r requirements.txt
```

## Differences from Main Version

| Feature | Main Version | Tester Version |
|---------|-------------|----------------|
| API Key Source | `.env` file | UI input (sidebar) |
| Configuration | Requires setup | No setup needed |
| Model Selection | Environment variable | UI dropdown |
| Best For | Production/Development | Testing/Demos |

## Troubleshooting

### "API Key required" error
- Make sure you've entered your API key in the sidebar
- Check that the key starts with `sk-`
- Verify you have credits in your OpenAI account

### "Model call failed" error
- Verify your API key is correct
- Check your OpenAI account has available credits
- Try a different model (gpt-4o-mini is most cost-effective)

### Import errors
- Make sure you're running from the correct directory
- Install requirements: `pip install -r requirements.txt`

## Notes

- This version is ideal for sharing with testers who have their own OpenAI accounts
- No need to share your API key with testers
- Each tester uses their own quota/credits
- Perfect for demos and testing scenarios

