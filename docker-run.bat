@echo off
echo Building and running ArcSpatialDB Docker container...
echo.

REM Build the Docker image
echo Building Docker image...
docker build -t arcspecialdb .

REM Run the container
echo.
echo Starting container...
docker run -d --name arcspecialdb-app -p 5002:5002 -v %cd%\elements.db:/app/elements.db arcspecialdb

echo.
echo Container started! Access the application at: http://localhost:5002
echo.
echo To stop the container: docker stop arcspecialdb-app
echo To remove the container: docker rm arcspecialdb-app
echo To view logs: docker logs arcspecialdb-app 