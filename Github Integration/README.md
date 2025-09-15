# 🔗 GitHub Integration Guide

## 📋 **Overview**
Dokumentasi lengkap untuk integrasi project dengan GitHub, termasuk setup authentication, multi-account management, dan best practices untuk Jetson Orin Nano.

## 🔐 **Authentication Methods**

### **1. Personal Access Token (Recommended)**
```bash
# Generate token di GitHub:
# Settings → Developer settings → Personal access tokens → Generate new token

# Scopes yang diperlukan:
✅ repo (Full control of private repositories)
✅ workflow (Update GitHub Action workflows)
✅ write:packages (Upload packages to GitHub Package Registry)
✅ delete:packages (Delete packages from GitHub Package Registry)
✅ admin:org (Full control of orgs and teams)
✅ admin:public_key (Full control of user public keys)
✅ admin:repo_hook (Full control of repository hooks)
✅ admin:org_hook (Full control of organization hooks)
✅ gist (Create gists)
✅ notifications (Access notifications)
✅ user (Update ALL user data)
✅ delete_repo (Delete repositories)
✅ admin:gpg_key (Full control of user gpg keys)
```

### **2. GitHub CLI (Easiest)**
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y

# Login dengan token
echo "YOUR_TOKEN" | gh auth login --with-token

# Check status
gh auth status
```

### **3. SSH Keys (Most Secure)**
```bash
# Generate SSH key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_vnot01 -C "vnot01@example.com"

# Add to SSH agent
ssh-add ~/.ssh/id_ed25519_vnot01

# Copy public key
cat ~/.ssh/id_ed25519_vnot01.pub

# Add to GitHub: Settings → SSH and GPG keys → New SSH key
```

## 🔄 **Multi-Account Management**

### **Method 1: Personal Access Token + Username**
```bash
# Clone dengan username dan token
git clone https://vnot01:TOKEN_VNOT01@github.com/vnot01/repo1.git
git clone https://myotheruser:TOKEN_MYOTHER@github.com/myotheruser/repo2.git

# Set remote dengan username dan token
git remote set-url origin https://vnot01:TOKEN_VNOT01@github.com/vnot01/repo1.git
```

### **Method 2: Git Config Per-Repository**
```bash
# Set config global (default)
git config --global user.name "vnot01"
git config --global user.email "vnot01@example.com"

# Override per repository
cd repo1
git config user.name "vnot01"
git config user.email "vnot01@example.com"

cd ../repo2
git config user.name "myotheruser"
git config user.email "myotheruser@example.com"
```

### **Method 3: SSH Key Multiple**
```bash
# Generate multiple SSH keys
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_vnot01 -C "vnot01@example.com"
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_myother -C "myotheruser@example.com"

# Setup SSH config
cat >> ~/.ssh/config << EOF
# Account vnot01
Host github-vnot01
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_vnot01

# Account myotheruser
Host github-myother
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_myother
EOF

# Clone dengan host alias
git clone git@github-vnot01:vnot01/repo1.git
git clone git@github-myother:myotheruser/repo2.git
```

### **Method 4: Environment Variables**
```bash
# Set environment variables per session
export GIT_AUTHOR_NAME="vnot01"
export GIT_AUTHOR_EMAIL="vnot01@example.com"
export GIT_COMMITTER_NAME="vnot01"
export GIT_COMMITTER_EMAIL="vnot01@example.com"

# Atau untuk akun lain
export GIT_AUTHOR_NAME="myotheruser"
export GIT_AUTHOR_EMAIL="myotheruser@example.com"
export GIT_COMMITTER_NAME="myotheruser"
export GIT_COMMITTER_EMAIL="myotheruser@example.com"
```

## 🚀 **Project Initialization Workflow**

### **Step 1: Create Repository on GitHub**
```bash
# Method 1: Using GitHub CLI (if token has create permission)
gh repo create project-name --public --description "Project description" --source=. --remote=origin --push

# Method 2: Manual (via GitHub web interface)
# 1. Go to github.com
# 2. Click "+" → "New repository"
# 3. Fill repository name, description, visibility
# 4. Don't add README, .gitignore, or license (we already have them)
# 5. Click "Create repository"
```

### **Step 2: Initialize Local Repository**
```bash
# Initialize git repository
git init
git branch -m main

# Set git config
git config user.name "vnot01"
git config user.email "vnot01@example.com"

# Add remote
git remote add origin https://vnot01:TOKEN@github.com/vnot01/project-name.git
```

### **Step 3: Create .gitignore**
```bash
# Create comprehensive .gitignore
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
```

### **Step 4: Add, Commit, and Push**
```bash
# Add files
git add .

# Check status
git status

# Commit
git commit -m "Initial commit: Project description

- Feature 1
- Feature 2
- Feature 3
- Ready for production use"

# Push
git push -u origin main
```

## 🛠️ **Setup Scripts**

### **Multi-Account Setup Script**
```bash
#!/bin/bash
# File: setup-git-account.sh

REPO_NAME=$1
GITHUB_USER=$2
TOKEN=$3

if [ -z "$REPO_NAME" ] || [ -z "$GITHUB_USER" ] || [ -z "$TOKEN" ]; then
    echo "Usage: $0 <repo-name> <github-user> <token>"
    echo "Example: $0 test-cv-yolo11-sam2-camera vnot01 github_pat_..."
    exit 1
fi

# Set git config
git config user.name "$GITHUB_USER"
git config user.email "$GITHUB_USER@example.com"

# Set remote
git remote set-url origin https://$GITHUB_USER:$TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git

echo "Git setup completed for $GITHUB_USER/$REPO_NAME"
```

### **Account Switch Script**
```bash
#!/bin/bash
# File: switch-account.sh

ACCOUNT=$1

case $ACCOUNT in
    "vnot01")
        git config --global user.name "vnot01"
        git config --global user.email "vnot01@example.com"
        echo "Switched to vnot01 account"
        ;;
    "myotheruser")
        git config --global user.name "myotheruser"
        git config --global user.email "myotheruser@example.com"
        echo "Switched to myotheruser account"
        ;;
    *)
        echo "Usage: $0 [vnot01|myotheruser]"
        ;;
esac
```

## 🔒 **Security Best Practices**

### **1. Token Management**
```bash
# Store token securely
echo "YOUR_TOKEN" > ~/.github_token_vnot01
chmod 600 ~/.github_token_vnot01

# Use environment variable
export GITHUB_TOKEN_VNOT01="YOUR_TOKEN"

# Don't hardcode in scripts
# Use: https://vnot01:$GITHUB_TOKEN_VNOT01@github.com/...
```

### **2. SSH Key Management**
```bash
# Generate strong keys
ssh-keygen -t ed25519 -b 4096 -f ~/.ssh/id_ed25519_vnot01 -C "vnot01@example.com"

# Use passphrase for extra security
# Add to SSH agent
ssh-add ~/.ssh/id_ed25519_vnot01

# Test connection
ssh -T git@github.com
```

### **3. Repository Security**
```bash
# Use .gitignore to exclude sensitive files
# Never commit:
- API keys
- Passwords
- Tokens
- Personal data
- Large model files
- Output results
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **1. Permission Denied (publickey)**
```bash
# Check SSH key
ssh-add -l

# Test SSH connection
ssh -T git@github.com

# Regenerate SSH key if needed
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_vnot01 -C "vnot01@example.com"
```

#### **2. Repository Not Found**
```bash
# Check remote URL
git remote -v

# Verify repository exists on GitHub
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/vnot01/repo-name

# Create repository if needed
gh repo create repo-name --public --description "Description"
```

#### **3. Authentication Failed**
```bash
# Check token validity
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# Regenerate token if expired
# GitHub → Settings → Developer settings → Personal access tokens
```

#### **4. Rate Limit Exceeded**
```bash
# Check rate limit
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit

# Use authenticated requests for higher limits
# Wait for rate limit reset
```

## 📊 **GitHub API Usage**

### **Check User Information**
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### **List Repositories**
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user/repos
```

### **Check Rate Limits**
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit
```

### **Create Repository via API**
```bash
curl -H "Authorization: token YOUR_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user/repos \
     -d '{"name":"repo-name","description":"Description","private":false}'
```

## 🎯 **Best Practices Summary**

1. **Use Personal Access Tokens** for simplicity
2. **Set up .gitignore** to exclude unnecessary files
3. **Use per-repository git config** for multi-account
4. **Store tokens securely** (environment variables, files with restricted permissions)
5. **Test authentication** before pushing
6. **Use descriptive commit messages**
7. **Keep repositories organized** with proper documentation
8. **Regular backup** of important repositories
9. **Monitor rate limits** for API usage
10. **Keep tokens updated** and rotate regularly

## 📚 **Additional Resources**

- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [SSH Key Generation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
- [Git Configuration](https://git-scm.com/book/en/v2/Customizing-Git-Git-Configuration)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

**Last Updated:** $(date)
**Version:** 1.0
**Author:** vnot01