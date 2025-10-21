#!/bin/bash

echo "🐳 Testing Minimal Docker Setup"
echo "================================"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true

# Build and start services
echo "🚀 Building and starting minimal services..."
docker-compose -f docker-compose.minimal.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 15

# Check if services are running
echo "🔍 Checking service status..."
docker-compose -f docker-compose.minimal.yml ps

# Test web service
echo "🌐 Testing web service..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Web service is running"
else
    echo "❌ Web service is not responding"
    echo "📋 Checking logs..."
    docker-compose -f docker-compose.minimal.yml logs web
fi

# Test database
echo "🗄️ Testing database..."
if docker-compose -f docker-compose.minimal.yml exec -T db pg_isready -U crawler > /dev/null 2>&1; then
    echo "✅ Database is running"
else
    echo "❌ Database is not responding"
fi

echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.minimal.yml ps

echo ""
echo "💡 Next steps:"
echo "   1. Access: http://localhost:8000"
echo "   2. Run migrations: docker-compose -f docker-compose.minimal.yml exec web python manage.py migrate"
echo "   3. Create superuser: docker-compose -f docker-compose.minimal.yml exec web python manage.py createsuperuser"
echo "   4. View logs: docker-compose -f docker-compose.minimal.yml logs web"
echo "   5. Stop services: docker-compose -f docker-compose.minimal.yml down"
