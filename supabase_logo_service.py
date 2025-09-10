#!/usr/bin/env python3
"""
Supabase Storage Logo Service for Anéxodos AI
Fetches logos from Supabase Storage bucket and serves them to the frontend
"""

import os
import base64
import logging
import json
from io import BytesIO
from flask import Flask, jsonify, send_file
import requests

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
BUCKET_NAME = "omnix-bucket"

# Logo file names
OMNIX_LOGO = "Omnix-logo.png"
ANEXODOS_LOGO = "ANEXODOX-logo.png"

class SupabaseLogoService:
    """Service to fetch and cache logos from Supabase Storage"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logo_cache = {}
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_ANON_KEY
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL or anon key not configured")
            
            self.base_url = f"{self.supabase_url}/storage/v1/object/public/{BUCKET_NAME}"
            self.logger.info("✅ Supabase Storage client initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self.supabase_url = None
    
    def get_logo_url(self, logo_name):
        """Get public URL for logo from Supabase Storage"""
        if not self.supabase_url:
            return None
        
        try:
            url = f"{self.base_url}/{logo_name}"
            return url
        except Exception as e:
            self.logger.error(f"❌ Failed to get URL for {logo_name}: {e}")
            return None
    
    def get_logo_base64(self, logo_name):
        """Get logo as base64 encoded string for embedding"""
        if not self.supabase_url:
            return None
        
        # Check cache first
        if logo_name in self.logo_cache:
            return self.logo_cache[logo_name]
        
        try:
            # Get logo from Supabase Storage
            url = f"{self.base_url}/{logo_name}"
            response = requests.get(url, timeout=5)  # Reduced timeout
            
            if response.status_code != 200:
                self.logger.warning(f"⚠️ Logo {logo_name} not found in Supabase Storage (status: {response.status_code})")
                return None
            
            # Convert to base64
            logo_data = response.content
            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            
            # Determine MIME type
            mime_type = "image/png" if logo_name.endswith('.png') else "image/jpeg"
            
            # Create data URL
            data_url = f"data:{mime_type};base64,{logo_base64}"
            
            # Cache the result
            self.logo_cache[logo_name] = data_url
            
            self.logger.info(f"✅ Successfully loaded {logo_name} from Supabase Storage")
            return data_url
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.DNSError) as e:
            self.logger.warning(f"⚠️ Network issue fetching {logo_name}: Supabase unavailable")
            return None
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch {logo_name}: {e}")
            return None
    
    def get_omnix_logo(self):
        """Get Omnix AI logo"""
        return self.get_logo_base64(OMNIX_LOGO)
    
    def get_anexodos_logo(self):
        """Get Anéxodos AI logo"""
        return self.get_logo_base64(ANEXODOS_LOGO)
    
    def get_logos_data(self):
        """Get both logos as JSON data"""
        return {
            "omnix_logo": self.get_omnix_logo(),
            "anexodos_logo": self.get_anexodos_logo(),
            "status": "success" if self.supabase_url else "error"
        }

# Initialize the service
logo_service = SupabaseLogoService()

def get_logos_for_frontend():
    """Function to be called from main Flask app"""
    return logo_service.get_logos_data()

# Flask routes (if running as standalone service)
if __name__ == "__main__":
    app = Flask(__name__)
    
    @app.route('/api/logos')
    def get_logos():
        """API endpoint to get logos"""
        return jsonify(logo_service.get_logos_data())
    
    @app.route('/api/logos/omnix')
    def get_omnix_logo():
        """API endpoint to get Omnix logo"""
        logo_data = logo_service.get_omnix_logo()
        if logo_data:
            return jsonify({"logo": logo_data, "status": "success"})
        return jsonify({"error": "Failed to load logo", "status": "error"}), 404
    
    @app.route('/api/logos/anexodos')
    def get_anexodos_logo():
        """API endpoint to get Anéxodos logo"""
        logo_data = logo_service.get_anexodos_logo()
        if logo_data:
            return jsonify({"logo": logo_data, "status": "success"})
        return jsonify({"error": "Failed to load logo", "status": "error"}), 404
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "supabase_connected": logo_service.supabase_url is not None
        })
    
    app.run(debug=True, port=5001)