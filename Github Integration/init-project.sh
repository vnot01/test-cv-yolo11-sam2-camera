#!/bin/bash
# GitHub Project Initialization Script
# Usage: ./init-project.sh <project-name> <github-user> <token>

PROJECT_NAME=$1
GITHUB_USER=$2
TOKEN=$3

if [ -z "$PROJECT_NAME" ] || [ -z "$GITHUB_USER" ] || [ -z "$TOKEN" ]; then
    echo "Usage: $0 <project-name> <github-user> <token>"
    echo "Example: $0 my-new-project vnot01 github_pat_..."
    exit 1
fi

echo "🚀 Initializing GitHub project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Initialize git repository
git init
git branch -m main

# Set git config
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@example.com"

# Create .gitignore
cat > .gitignore << 'EOF'
# Models (auto-download, don't upload)
models/
*.pt
*.pth
*.onnx
*.engine

# Output results (don't upload)
storages/
output/
results/
inference_results/
detection_images/
segmentation_images/

# Camera captures (don't upload)
camera_captures/
captures/
temp_images/

# Virtual environment (don't upload)
myenv/
venv/
env/
.venv/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
temp/
tmp/

# Jupyter Notebook
.ipynb_checkpoints

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# GitHub token (security)
.github_token*
*.token
EOF

# Create basic README
cat > README.md << EOF
# $PROJECT_NAME

## Description
Project description here.

## Installation
\`\`\`bash
# Clone repository
git clone https://github.com/$GITHUB_USER/$PROJECT_NAME.git
cd $PROJECT_NAME

# Install dependencies
pip install -r requirements.txt
\`\`\`

## Usage
\`\`\`bash
# Run project
python main.py
\`\`\`

## License
MIT License
EOF

# Create requirements.txt
cat > requirements.txt << EOF
# Add your dependencies here
# Example:
# numpy>=1.21.0
# opencv-python>=4.5.0
# ultralytics>=8.0.0
EOF

# Add remote
git remote add origin https://$GITHUB_USER:$TOKEN@github.com/$GITHUB_USER/$PROJECT_NAME.git

echo "✅ Project initialized successfully!"
echo "📁 Project directory: $(pwd)"
echo "🔗 Repository URL: https://github.com/$GITHUB_USER/$PROJECT_NAME"
echo ""
echo "Next steps:"
echo "1. Add your files to the project"
echo "2. git add ."
echo "3. git commit -m 'Initial commit'"
echo "4. git push -u origin main"
