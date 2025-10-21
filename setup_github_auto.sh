#!/bin/bash

echo "🚀 Auto GitHub Setup for Lawyer Crawling System"
echo "=============================================="

# Check if git is configured
if ! git config --global user.name > /dev/null 2>&1; then
    echo "❌ Git not configured. Please set up Git first:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

echo "✅ Git is configured"
echo "👤 User: $(git config --global user.name)"
echo "📧 Email: $(git config --global user.email)"
echo ""

# Check current status
echo "📊 Current Repository Status:"
echo "   📁 Files: $(find . -type f | wc -l)"
echo "   💾 Size: $(du -sh . | cut -f1)"
echo "   📝 Commits: $(git rev-list --count HEAD)"
echo ""

# Check if remote exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "✅ Remote origin already exists:"
    git remote -v
    echo ""
    echo "🚀 Ready to push! Run:"
    echo "   git push -u origin master"
    exit 0
fi

echo "📝 No remote origin found."
echo ""
echo "🔧 Next Steps:"
echo "1. Create repository on GitHub:"
echo "   - Go to: https://github.com"
echo "   - Click 'New repository'"
echo "   - Name: lawyer-crawling-system"
echo "   - Description: Django-based lawyer data crawling system"
echo "   - DON'T initialize with README"
echo ""
echo "2. Add remote origin:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/lawyer-crawling-system.git"
echo ""
echo "3. Push to GitHub:"
echo "   git push -u origin master"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - SETUP_GITHUB_NOW.md (step-by-step guide)"
echo "   - QUICK_GITHUB.md (quick reference)"
echo "   - GITHUB_SETUP.md (comprehensive guide)"
