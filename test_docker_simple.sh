#!/bin/bash

echo "🐳 Testing Simple Docker Setup"
echo "=============================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "💡 Please install Docker Desktop first"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "💡 Please install Docker Compose first"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Test simple setup
echo "🚀 Testing simple Docker setup..."

# Build and start services
echo "📦 Building and starting services..."
docker-compose -f docker-compose.simple.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker-compose.simple.yml ps

# Test web service
echo "🌐 Testing web service..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Web service is running"
else
    echo "❌ Web service is not responding"
fi

# Test database
echo "🗄️ Testing database..."
if docker-compose -f docker-compose.simple.yml exec -T db pg_isready -U crawler > /dev/null 2>&1; then
    echo "✅ Database is running"
else
    echo "❌ Database is not responding"
fi

echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.simple.yml ps

echo ""
echo "💡 Next steps:"
echo "   1. Access: http://localhost:8000"
echo "   2. Run migrations: docker-compose -f docker-compose.simple.yml exec web python manage.py migrate"
echo "   3. Create superuser: docker-compose -f docker-compose.simple.yml exec web python manage.py createsuperuser"
echo "   4. View logs: docker-compose -f docker-compose.simple.yml logs web"
