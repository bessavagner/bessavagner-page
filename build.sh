#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
    echo "📂 .env file loaded!"
else
    echo ".env file not found!"
    exit 1
fi

echo $BUILD
if [[ "$BUILD" -eq 1 ]]; then
    if [[ "$INSTALL" = "1" ]]; then
        echo "🛠️ Building project: "
        echo "╰─ ⏬ Installing requirements"
        poetry export -f requirements.txt --output requirements.txt
        pip install -r requirements.txt
        echo "╰─ ⏬ Installing requirements: ended!"
    fi
    if [[ "$BUILD_TAILWINDCSS" = "1" ]]; then
        cd src/tailwindcss
        echo "╰─ ⏬ Installing tailwindcss"
        npm install
        echo "╰─ ⏬ Installing tailwindcss: finished!"
        echo "╰─ ⏬ Building tailwind style"
        npm run build
        echo "╰─ ⏬ Building tailwind style: finished"
        cd ../../
    fi
    if [[ "$PRODUCTION" = "1" ]]; then
        echo "🐋 Building Docker image..."
        docker build -t "$DOCKER_USERNAME"/"$DOCKER_IMAGENAME" .
        echo "🐋 Building Docker image: finished!"
    fi
else
    echo "Skipping build..."
fi