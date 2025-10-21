#!/bin/bash

echo "🚀 Pushing Lawyer Crawling System to GitHub"
echo "=========================================="

# Check if git is configured
if ! git config --global user.name > /dev/null 2>&1; then
    echo "❌ Git not configured. Please set up Git first:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
    exit 1
fi

# Check if remote origin exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "📝 No remote origin found. Please add GitHub repository:"
    echo "   git remote add origin https://github.com/username/lawyer-crawling-system.git"
    echo ""
    echo "Or create a new repository on GitHub and run:"
    echo "   git remote add origin <your-repo-url>"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  Uncommitted changes detected. Please commit or stash them first."
    git status --short
    exit 1
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
if git push -u origin $CURRENT_BRANCH; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🌐 Repository URL:"
    git remote get-url origin
    echo ""
    echo "📋 Next steps:"
    echo "   1. Visit your GitHub repository"
    echo "   2. Add collaborators if needed"
    echo "   3. Set up GitHub Actions for CI/CD"
    echo "   4. Configure branch protection rules"
    echo "   5. Add repository description and topics"
else
    echo "❌ Failed to push to GitHub"
    echo "💡 Common solutions:"
    echo "   - Check your GitHub credentials"
    echo "   - Verify repository permissions"
    echo "   - Try: git push --set-upstream origin $CURRENT_BRANCH"
    exit 1
fi
