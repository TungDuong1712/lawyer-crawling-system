#!/bin/bash

# Script setup cho hệ thống crawl dữ liệu luật sư

echo "🏛️ HỆ THỐNG CRAWL DỮ LIỆU LUẬT SƯ - SETUP"
echo "=========================================="

# Kiểm tra Python
echo "🐍 Kiểm tra Python..."
if command -v python3 &> /dev/null; then
    echo "   ✅ Python3 đã cài đặt: $(python3 --version)"
else
    echo "   ❌ Python3 chưa được cài đặt"
    echo "   💡 Hãy cài đặt Python3 trước"
    exit 1
fi

# Kiểm tra pip
echo "📦 Kiểm tra pip..."
if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3 đã cài đặt: $(pip3 --version)"
elif python3 -m pip --version &> /dev/null; then
    echo "   ✅ pip3 có sẵn qua python3 -m pip"
else
    echo "   ❌ pip3 chưa được cài đặt"
    echo "   💡 Hãy cài đặt pip3 trước"
    exit 1
fi

# Cài đặt dependencies
echo "📚 Cài đặt dependencies..."
if pip3 install -r requirements.txt; then
    echo "   ✅ Dependencies đã được cài đặt"
elif python3 -m pip install -r requirements.txt; then
    echo "   ✅ Dependencies đã được cài đặt"
else
    echo "   ❌ Lỗi khi cài đặt dependencies"
    echo "   💡 Hãy thử cài đặt thủ công:"
    echo "      pip3 install requests beautifulsoup4 pandas lxml fake-useragent python-dotenv"
    exit 1
fi

# Test hệ thống
echo "🧪 Test hệ thống..."
if python3 simple_test.py; then
    echo "   ✅ Test thành công"
else
    echo "   ❌ Test thất bại"
    echo "   💡 Hãy kiểm tra lại cấu hình"
    exit 1
fi

# Demo hệ thống
echo "🎬 Chạy demo..."
if python3 demo.py; then
    echo "   ✅ Demo thành công"
else
    echo "   ❌ Demo thất bại"
    exit 1
fi

echo ""
echo "🎉 SETUP HOÀN THÀNH!"
echo "==================="
echo ""
echo "💡 Cách sử dụng:"
echo "   • Test nhanh: python3 main.py --test"
echo "   • Crawl cơ bản: python3 main.py --limit 10"
echo "   • Xem hướng dẫn: python3 main.py --help"
echo "   • Demo: python3 demo.py"
echo ""
echo "📁 Files quan trọng:"
echo "   • main.py - Script chính"
echo "   • config.py - Cấu hình"
echo "   • README.md - Hướng dẫn chi tiết"
echo ""
echo "🚀 Hệ thống đã sẵn sàng để crawl dữ liệu luật sư!"
