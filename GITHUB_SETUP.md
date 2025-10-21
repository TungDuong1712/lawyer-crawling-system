# 🐙 GitHub Setup Guide

Hướng dẫn đẩy project Lawyer Crawling System lên GitHub.

## 📋 Bước 1: Tạo Repository trên GitHub

1. **Đăng nhập GitHub**: Truy cập [github.com](https://github.com)
2. **Tạo repository mới**:
   - Click "New repository" hoặc "+" → "New repository"
   - Repository name: `lawyer-crawling-system` (hoặc tên khác)
   - Description: `Django-based lawyer data crawling system with Docker support`
   - Visibility: Public hoặc Private
   - **KHÔNG** check "Initialize with README" (vì đã có sẵn)
3. **Copy repository URL** (sẽ cần cho bước sau)

## 🔧 Bước 2: Cấu hình Git (nếu chưa có)

```bash
# Cấu hình Git user
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Kiểm tra cấu hình
git config --list
```

## 🚀 Bước 3: Đẩy Code lên GitHub

### Option A: Sử dụng Script (Khuyến nghị)
```bash
# Chạy script tự động
./push_to_github.sh
```

### Option B: Thực hiện thủ công
```bash
# Thêm remote origin
git remote add origin https://github.com/username/lawyer-crawling-system.git

# Đẩy code lên GitHub
git push -u origin master
```

## 🔐 Bước 4: Cấu hình Authentication

### Option A: Personal Access Token (Khuyến nghị)
1. **Tạo token**: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Cấu hình permissions**: 
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. **Copy token** và sử dụng thay password

### Option B: SSH Key
```bash
# Tạo SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Thêm key vào SSH agent
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Thêm key vào GitHub: Settings → SSH and GPG keys
```

## 📊 Bước 5: Cấu hình Repository

### Repository Settings
1. **Description**: `Django-based lawyer data crawling system with Docker support`
2. **Topics**: `django`, `web-scraping`, `docker`, `postgresql`, `celery`, `lawyer-data`
3. **Website**: `http://localhost:8000` (cho development)
4. **License**: MIT License

### Branch Protection
1. **Settings** → **Branches** → **Add rule**
2. **Branch name pattern**: `master`
3. **Protect matching branches**: ✅
4. **Require pull request reviews**: ✅
5. **Require status checks**: ✅

## 🔄 Bước 6: GitHub Actions (CI/CD)

Tạo file `.github/workflows/ci.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ master, develop ]
  pull_request:
    branches: [ master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python test_urls_fixed.py
    
    - name: Test Docker build
      run: |
        docker-compose -f docker-compose.minimal-only.yml build
```

## 📈 Bước 7: Monitoring & Analytics

### GitHub Insights
- **Traffic**: Xem số lượt clone, view
- **Contributors**: Theo dõi contributors
- **Community**: Health score của repository

### Repository Health
- **README**: Đầy đủ thông tin
- **LICENSE**: Có license file
- **CONTRIBUTING**: Hướng dẫn contribute
- **Issues**: Template cho bug reports
- **Pull Requests**: Template cho PR

## 🛠️ Bước 8: Development Workflow

### Branch Strategy
```bash
# Main branches
master          # Production ready
develop         # Development integration

# Feature branches
feature/crawler-improvements
feature/docker-optimization
feature/api-enhancements

# Hotfix branches
hotfix/security-patch
hotfix/critical-bug
```

### Commit Convention
```
feat: add new crawling feature
fix: resolve URL configuration error
docs: update README with Docker setup
style: format code with black
refactor: optimize Docker build process
test: add URL configuration tests
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Failed
```bash
# Sử dụng Personal Access Token
git remote set-url origin https://username:token@github.com/username/repo.git
```

#### 2. Repository Already Exists
```bash
# Remove existing remote
git remote remove origin

# Add new remote
git remote add origin https://github.com/username/new-repo.git
```

#### 3. Large Files
```bash
# Add to .gitignore
echo "*.log" >> .gitignore
echo "*.db" >> .gitignore
echo "media/" >> .gitignore

# Remove from tracking
git rm --cached large-file.log
git commit -m "Remove large files"
```

## 📞 Support

Nếu gặp vấn đề:
1. **Check GitHub Status**: [status.github.com](https://status.github.com)
2. **GitHub Documentation**: [docs.github.com](https://docs.github.com)
3. **Git Tutorial**: [git-scm.com/docs](https://git-scm.com/docs)

---

**Happy Coding! 🚀**
