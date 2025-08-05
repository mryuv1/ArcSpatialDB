#!/usr/bin/env python3
"""
Production server for ArcSpatialDB with automatic reconnection
This server will automatically restart if it fails or crashes
"""

import time
import sys
import os
import signal
import logging
from datetime import datetime
from waitress import serve
from app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutoReconnectServer:
    def __init__(self, max_retries=5, retry_delay=10):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_count = 0
        self.running = True
        
        # Get configuration
        try:
            from config import FLASK_HOST, FLASK_PORT
            self.host = FLASK_HOST
            self.port = FLASK_PORT
        except ImportError:
            # Fallback configuration
            self.host = "0.0.0.0"
            self.port = 5000
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False
        sys.exit(0)
    
    def start_server(self):
        """Start the server with automatic reconnection"""
        logger.info("🚀 Starting ArcSpatialDB Production Server with Auto-Reconnect")
        logger.info(f"📍 Host: {self.host}")
        logger.info(f"🔌 Port: {self.port}")
        logger.info(f"🌐 URL: http://{self.host}:{self.port}")
        logger.info("=" * 50)
        
        while self.running and self.retry_count < self.max_retries:
            try:
                logger.info(f"🔄 Attempt {self.retry_count + 1}/{self.max_retries}")
                logger.info("✅ Starting server...")
                
                # Start the production server
                serve(app, host=self.host, port=self.port, threads=4)
                
            except KeyboardInterrupt:
                logger.info("🛑 Server stopped by user")
                self.running = False
                break
                
            except Exception as e:
                self.retry_count += 1
                logger.error(f"❌ Server failed: {e}")
                
                if self.retry_count < self.max_retries:
                    logger.info(f"⏳ Waiting {self.retry_delay} seconds before retry...")
                    time.sleep(self.retry_delay)
                    
                    # Increase delay for next retry (exponential backoff)
                    self.retry_delay = min(self.retry_delay * 2, 300)  # Max 5 minutes
                else:
                    logger.error(f"❌ Maximum retries ({self.max_retries}) reached. Server will not restart.")
                    break
        
        if not self.running:
            logger.info("✅ Server shutdown completed")
        else:
            logger.error("❌ Server failed permanently")

def main():
    """Main function to start the auto-reconnect server"""
    server = AutoReconnectServer(max_retries=5, retry_delay=10)
    server.start_server()

if __name__ == '__main__':
    main() 