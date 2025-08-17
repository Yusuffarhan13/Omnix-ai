# Enhanced Complex Mode Setup Guide

The Enhanced Complex Mode transforms Omnix AI into a **fully maxed-out** AI system with cutting-edge reasoning capabilities, multi-agent analysis, and advanced code execution.

## 🚀 Features Overview

### Core Enhancements
- **Gemini 2.5 Pro Deep Think Mode** - Advanced reasoning with thinking budget controls
- **Multi-Agent System** - 8 specialized AI agents working in parallel for comprehensive analysis
- **Sequential Thinking MCP** - Multi-chain reasoning with structured thought processes
- **Sandboxed Code Execution** - Safe execution and preview of generated code
- **AI Notebook Planning** - Intelligent task decomposition and planning system
- **Enhanced Research Mode** - Multi-source research with fact-checking and analysis

### AI Capabilities Maxed Out
- **Dynamic Thinking Budget** - Adaptive reasoning token allocation
- **Parallel Thinking** - Multiple solution paths explored simultaneously  
- **Multi-Perspective Analysis** - Strategic, Technical, Analytical, Critical, Research, and Creative viewpoints
- **Real-time Code Execution** - Python, JavaScript, HTML, CSS, Bash support
- **Interactive Previews** - Live preview of web applications and visualizations
- **Research Synthesis** - Academic papers, news sources, and specialized databases

## 📋 Prerequisites

### Required API Keys
1. **Google API Key** (Primary)
   - Visit: https://aistudio.google.com/app/apikey
   - Required for: Gemini 2.5 Pro Deep Think, Multi-Agent System, Research
   
2. **Brave Search API Key** (Optional but Recommended)
   - Visit: https://api.search.brave.com/
   - Required for: Enhanced research capabilities

### System Requirements
- **Python 3.8+**
- **Docker** (Optional - for enhanced code execution sandboxing)
- **4GB+ RAM** (recommended for multi-agent processing)
- **Internet Connection** (for MCP servers and research)

## 🛠️ Installation Steps

### 1. Install Dependencies
```bash
# Install enhanced dependencies
pip install -r requirements.txt

# Install additional packages for full functionality
pip install docker beautifulsoup4 aiohttp Pillow
```

### 2. Configure Environment Variables
Update your `.env` file:
```env
# Required for Enhanced Complex Mode
GOOGLE_API_KEY=your_google_api_key_here

# Optional but recommended
BRAVE_API_KEY=your_brave_search_api_key_here

# Existing keys (keep as they were)
BROWSER_USE_CLOUD_API_KEY=your_browser_use_cloud_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Install MCP Sequential Thinking Server
```bash
# Install Node.js if not already installed
# Then install the sequential thinking server
npm install -g @modelcontextprotocol/server-sequential-thinking
```

### 4. Docker Setup (Optional)
For enhanced code execution with full sandboxing:
```bash
# Install Docker
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install docker.io
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

### 5. Verify Installation
```bash
# Test the enhanced system
python test_enhanced_complex_mode.py
```

## 🎯 Usage Guide

### Accessing Enhanced Complex Mode

1. **Start the Application**
   ```bash
   python main.py
   ```

2. **Access Enhanced UI**
   - Navigate to: `http://localhost:8003/enhanced`
   - Or use the complex mode button in the main interface

### Enhanced Options Configuration

#### 🧠 Deep Think Mode
- **Dynamic Thinking Budget** (Recommended): Automatically adjusts reasoning depth
- **Fixed Budget Options**: 512, 1024, 2048 tokens for controlled processing
- **Parallel Thinking**: Enables simultaneous exploration of multiple solution paths

#### 🤖 Multi-Agent System
Enable specialized agents for comprehensive analysis:
- **Strategic Agent**: Long-term planning and strategic thinking
- **Technical Agent**: Implementation details and coding solutions  
- **Analytical Agent**: Data analysis and quantitative evaluation
- **Critical Agent**: Risk assessment and quality validation
- **Research Agent**: Multi-source information gathering
- **Creative Agent**: Innovative approaches and alternatives

#### 🔧 Code Execution Features
- **Sandboxed Execution**: Safe code execution in isolated environments
- **Interactive Previews**: Real-time preview of web applications
- **Multi-Language Support**: Python, JavaScript, HTML, CSS, Bash
- **Output Visualization**: Rich display of execution results

#### 📝 AI Notebook Planning
- **Automatic Planning**: AI-generated comprehensive task breakdown
- **Section Organization**: Executive Summary, Problem Analysis, Solution Architecture
- **Interactive Notes**: Add insights and observations during task execution
- **Progress Tracking**: Real-time updates and milestone monitoring

## 🎛️ Advanced Configuration

### Thinking Budget Optimization
- **Light (512 tokens)**: Quick analysis for simple tasks
- **Moderate (1024 tokens)**: Standard processing for most tasks
- **Heavy (2048 tokens)**: Deep analysis for complex problems
- **Dynamic (-1)**: AI determines optimal budget automatically

### Multi-Agent Perspective Selection
Customize which perspectives to include:
```javascript
// In the UI, select perspectives based on task type:
- Code/Technical tasks: Technical + Analytical + Critical
- Business strategy: Strategic + Analytical + Research  
- Creative projects: Creative + Strategic + Critical
- Research tasks: Research + Analytical + Critical
```

### Research Mode Configuration
Enhanced research supports:
- **Academic Sources**: arXiv, CrossRef, PubMed integration
- **News Sources**: Multiple news APIs and RSS feeds  
- **Fact-Checking**: Multi-source verification and credibility assessment
- **Comparative Analysis**: Side-by-side evaluation of multiple topics

## 🔍 API Endpoints

### Enhanced Complex Task Processing
```http
POST /complex_task
{
  "prompt": "Your complex task description",
  "options": {
    "enable_deep_think": true,
    "thinking_budget": -1,
    "enable_multi_agent": true,
    "perspectives": ["strategic", "technical", "analytical"],
    "enable_code_execution": true,
    "enable_notebook_planning": true,
    "create_preview": true
  },
  "session_id": "optional_session_id"
}
```

### Enhanced Research
```http
POST /enhanced_research
{
  "query": "Research query",
  "type": "comprehensive", // or "fact_check", "comparative"
  "topics": ["topic1", "topic2"] // for comparative analysis
}
```

### Code Execution
```http
POST /execute_code
{
  "code": "print('Hello, Enhanced AI!')",
  "language": "python",
  "timeout": 30
}
```

### Notebook Management
```http
GET /notebook/{notebook_id}
POST /notebook/{notebook_id}/note
{
  "note": "Important insight about the task",
  "type": "user_note"
}
GET /notebook/{notebook_id}/summary
```

## 🚀 Performance Optimization

### System Resources
- **Multi-Agent Processing**: Can use significant RAM during parallel analysis
- **Code Execution**: Docker containers may require additional CPU/memory
- **Research Mode**: Network-intensive during multi-source searches

### Optimization Tips
1. **Adjust Thinking Budget**: Use lighter budgets for simple tasks
2. **Selective Perspectives**: Enable only necessary agent perspectives
3. **Resource Monitoring**: Monitor system resources during heavy tasks
4. **Cache Management**: Research results are cached for 1 hour by default

## 🔧 Troubleshooting

### Common Issues

#### "Enhanced complex mode not available"
- **Cause**: Google API key not configured or invalid
- **Solution**: Verify `GOOGLE_API_KEY` in `.env` file

#### "Multi-agent analysis failed"
- **Cause**: MCP sequential thinking server not installed
- **Solution**: Install via `npm install -g @modelcontextprotocol/server-sequential-thinking`

#### "Code execution system not available"  
- **Cause**: Missing dependencies or Docker not running
- **Solution**: Install required packages, start Docker service

#### "Research manager not initialized"
- **Cause**: Missing research dependencies
- **Solution**: Install `beautifulsoup4`, `aiohttp`, and other research packages

### Performance Issues
- **Slow Processing**: Reduce thinking budget or disable some perspectives
- **Memory Usage**: Monitor RAM usage with multiple agents
- **Network Timeouts**: Check internet connection for research features

## 📊 Monitoring and Analytics

### Session Tracking
- All enhanced sessions are tracked with unique IDs
- Notebook progress is automatically saved
- Code execution history is maintained
- Research cache statistics available

### Usage Analytics  
Access usage information:
```http
GET /complex_sessions        # List all sessions
GET /complex_session/{id}    # Session details
```

## 🔐 Security Considerations

### Code Execution Security
- **Sandboxed Environment**: All code runs in isolated containers
- **Resource Limits**: CPU and memory limits enforced
- **Network Isolation**: Limited network access in execution environment
- **Timeout Protection**: Automatic termination of long-running code

### API Security
- **Rate Limiting**: Built-in protection against API abuse
- **Input Validation**: All inputs sanitized and validated
- **Error Handling**: Secure error messages without sensitive information

## 🆕 What's New in Enhanced Mode

### Compared to Standard Complex Mode
- **10x More Reasoning Power**: Deep Think mode with dynamic budgets
- **8 Specialized Agents**: Instead of single-agent processing
- **Real Code Execution**: Interactive code testing and preview
- **AI Planning Notebook**: Comprehensive task decomposition  
- **Multi-Source Research**: Academic and news source integration
- **Advanced UI**: Dedicated interface with real-time monitoring

### Performance Improvements
- **Parallel Processing**: Multi-agent analysis runs simultaneously
- **Intelligent Caching**: Research results and session state cached
- **Optimized API Calls**: Batch processing reduces latency
- **Resource Management**: Dynamic resource allocation based on task complexity

## 🎓 Best Practices

### Task Formulation
- **Be Specific**: Detailed prompts yield better results
- **Context Matters**: Provide relevant background information
- **Complexity Indication**: Mention if task requires multiple perspectives

### Option Selection
- **Match Task Complexity**: Use appropriate thinking budget
- **Relevant Perspectives**: Select perspectives that match your domain
- **Enable Features**: Turn on code execution for programming tasks

### Result Interpretation
- **Confidence Scores**: Pay attention to AI confidence indicators
- **Multiple Perspectives**: Compare different agent viewpoints
- **Notebook Planning**: Use planning sections for implementation guidance

## 📞 Support and Feedback

### Getting Help
- **Documentation**: Check this guide and inline help
- **Error Messages**: Enhanced error reporting with suggestions
- **Debug Mode**: Use browser developer tools for detailed logging

### Contributing
- **Feature Requests**: Suggest new capabilities or improvements
- **Bug Reports**: Report issues with detailed reproduction steps
- **Performance Feedback**: Share experience with different configurations

---

**Ready to experience the most advanced AI reasoning system available!**

Access Enhanced Complex Mode at: `http://localhost:8003/enhanced`