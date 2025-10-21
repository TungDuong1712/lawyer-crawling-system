#!/bin/bash

echo "🔑 SSH Setup and Push to GitHub"
echo "==============================="
echo ""

echo "✅ SSH Key Generated:"
echo "   File: ~/.ssh/github_lawyer_crawling"
echo "   Public: ~/.ssh/github_lawyer_crawling.pub"
echo ""

echo "📋 Your SSH Public Key:"
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPJYLstJdo10iobwv/Il58eYwKFY0D7hW/1aWltvKkrO duongnt@bkplussoft.org"
echo ""

echo "🚀 Step 1 - Add SSH Key to GitHub:"
echo "1. Go to: https://github.com/settings/ssh"
echo "2. Click 'New SSH key'"
echo "3. Title: 'Lawyer Crawling System'"
echo "4. Key type: 'Authentication Key'"
echo "5. Paste the key above"
echo "6. Click 'Add SSH key'"
echo ""

echo "⏳ Waiting for you to add SSH key..."
echo "Press Enter when you've added the SSH key to GitHub:"
read -p ""

echo "🔄 Step 2 - Update Remote URL:"
git remote set-url origin git@github.com:TungDuong1712/lawyer-crawling-system.git

echo "✅ Remote URL updated to SSH"

echo "🚀 Step 3 - Push to GitHub:"
git push -u origin master

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Code pushed to GitHub!"
    echo "📊 Repository: https://github.com/TungDuong1712/lawyer-crawling-system"
    echo ""
    echo "📋 What was uploaded:"
    echo "• Complete Django lawyer crawling system"
    echo "• Docker Compose configurations"
    echo "• REST API endpoints"
    echo "• Background task processing"
    echo "• Comprehensive documentation"
    echo "• 200+ files, 4 commits"
else
    echo ""
    echo "❌ Push failed. Please check:"
    echo "• SSH key is added to GitHub"
    echo "• Repository permissions"
    echo "• Network connection"
fi
