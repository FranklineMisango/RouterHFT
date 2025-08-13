"""
Geographic visualization of network paths and latency data.
Integrates with FCC microwave tower data for comprehensive network mapping.
"""

import folium
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import geopandas as gpd
from typing import List, Dict, Tuple, Optional
import requests
import json
import logging
from dataclasses import dataclass

from ..latency_mapping.traceroute_analyzer import HopData


@dataclass
class GeographicLocation:
    """Geographic location with metadata."""
    latitude: float
    longitude: float
    city: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None


class GeoIPResolver:
    """
    Resolves IP addresses to geographic locations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._cache = {}
    
    def resolve_ip_location(self, ip_address: str) -> Optional[GeographicLocation]:
        """
        Resolve IP address to geographic location using multiple services.
        """
        if ip_address in self._cache:
            return self._cache[ip_address]
        
        try:
            # Try multiple geolocation services
            location = self._try_ip_api(ip_address)
            if not location:
                location = self._try_ipinfo(ip_address)
            
            if location:
                self._cache[ip_address] = location
            
            return location
            
        except Exception as e:
            self.logger.error(f"Failed to resolve location for {ip_address}: {e}")
            return None
    
    def _try_ip_api(self, ip_address: str) -> Optional[GeographicLocation]:
        """
        Try ip-api.com service.
        """
        try:
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return GeographicLocation(
                        latitude=data.get('lat'),
                        longitude=data.get('lon'),
                        city=data.get('city'),
                        country=data.get('country'),
                        provider=data.get('isp')
                    )
        except Exception as e:
            self.logger.debug(f"ip-api.com failed for {ip_address}: {e}")
        
        return None
    
    def _try_ipinfo(self, ip_address: str) -> Optional[GeographicLocation]:
        """
        Try ipinfo.io service.
        """
        try:
            response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'loc' in data:
                    lat, lon = map(float, data['loc'].split(','))
                    return GeographicLocation(
                        latitude=lat,
                        longitude=lon,
                        city=data.get('city'),
                        country=data.get('country'),
                        provider=data.get('org')
                    )
        except Exception as e:
            self.logger.debug(f"ipinfo.io failed for {ip_address}: {e}")
        
        return None


class FCCDataManager:
    """
    Manages FCC microwave tower data for network infrastructure visualization.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._tower_data = None
    
    def load_fcc_tower_data(self, data_file: Optional[str] = None) -> bool:
        """
        Load FCC microwave tower data.
        """
        try:
            if data_file:
                # Load from local file
                with open(data_file, 'r') as f:
                    self._tower_data = json.load(f)
            else:
                # Load from FCC API (simplified - would need actual API implementation)
                self._tower_data = self._fetch_fcc_data()
            
            self.logger.info(f"Loaded {len(self._tower_data) if self._tower_data else 0} tower records")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load FCC tower data: {e}")
            return False
    
    def _fetch_fcc_data(self) -> List[Dict]:
        """
        Fetch FCC tower data (placeholder implementation).
        """
        # In a real implementation, this would query the FCC database
        # For now, return empty list
        return []
    
    def find_nearby_towers(self, lat: float, lon: float, radius_km: float = 50) -> List[Dict]:
        """
        Find microwave towers within specified radius.
        """
        if not self._tower_data:
            return []
        
        nearby_towers = []
        for tower in self._tower_data:
            # Calculate distance (simplified)
            tower_lat = tower.get('latitude', 0)
            tower_lon = tower.get('longitude', 0)
            
            # Simple distance calculation (would use proper haversine in production)
            distance = ((lat - tower_lat) ** 2 + (lon - tower_lon) ** 2) ** 0.5 * 111  # Rough km conversion
            
            if distance <= radius_km:
                nearby_towers.append(tower)
        
        return nearby_towers


class NetworkPathVisualizer:
    """
    Creates interactive visualizations of network paths and latency data.
    """
    
    def __init__(self):
        self.geo_resolver = GeoIPResolver()
        self.fcc_manager = FCCDataManager()
        self.logger = logging.getLogger(__name__)
    
    def create_interactive_map(self, hops: List[HopData], title: str = "Network Path Visualization") -> folium.Map:
        """
        Create interactive Folium map showing network path.
        """
        if not hops:
            return folium.Map()
        
        # Resolve geographic locations for all hops
        geo_hops = []
        for hop in hops:
            location = self.geo_resolver.resolve_ip_location(hop.ip_address)
            if location:
                geo_hops.append((hop, location))
        
        if not geo_hops:
            self.logger.warning("No geographic locations resolved")
            return folium.Map()
        
        # Calculate map center
        center_lat = sum(loc.latitude for _, loc in geo_hops) / len(geo_hops)
        center_lon = sum(loc.longitude for _, loc in geo_hops) / len(geo_hops)
        
        # Create map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
        
        # Add hop markers
        for i, (hop, location) in enumerate(geo_hops):
            # Color based on latency
            latency_us = hop.rtt_ns / 1000.0
            color = self._get_latency_color(latency_us)
            
            folium.CircleMarker(
                location=[location.latitude, location.longitude],
                radius=8,
                popup=f"""
                Hop {hop.hop_number}: {hop.ip_address}<br>
                Hostname: {hop.hostname or 'Unknown'}<br>
                Latency: {latency_us:.2f} μs<br>
                Location: {location.city}, {location.country}<br>
                Provider: {location.provider or 'Unknown'}
                """,
                color='black',
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
            
            # Add path lines
            if i > 0:
                prev_location = geo_hops[i-1][1]
                folium.PolyLine(
                    locations=[[prev_location.latitude, prev_location.longitude],
                              [location.latitude, location.longitude]],
                    color=color,
                    weight=3,
                    opacity=0.8
                ).add_to(m)
        
        return m
    
    def create_latency_dashboard(self, hops: List[HopData]) -> go.Figure:
        """
        Create comprehensive latency dashboard using Plotly.
        """
        if not hops:
            return go.Figure()
        
        # Prepare data
        hop_numbers = [hop.hop_number for hop in hops]
        latencies_us = [hop.rtt_ns / 1000.0 for hop in hops]
        ip_addresses = [hop.ip_address for hop in hops]
        hostnames = [hop.hostname or 'Unknown' for hop in hops]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Latency by Hop', 'Cumulative Latency', 'Latency Distribution', 'Top Latency Hops'),
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "histogram"}, {"type": "bar"}]]
        )
        
        # Latency by hop
        fig.add_trace(
            go.Scatter(
                x=hop_numbers,
                y=latencies_us,
                mode='lines+markers',
                name='Latency',
                hovertemplate='Hop %{x}<br>Latency: %{y:.2f} μs<br>IP: %{customdata[0]}<br>Host: %{customdata[1]}',
                customdata=list(zip(ip_addresses, hostnames))
            ),
            row=1, col=1
        )
        
        # Cumulative latency
        cumulative_latency = [sum(latencies_us[:i+1]) for i in range(len(latencies_us))]
        fig.add_trace(
            go.Scatter(
                x=hop_numbers,
                y=cumulative_latency,
                mode='lines+markers',
                name='Cumulative',
                line=dict(color='red')
            ),
            row=1, col=2
        )
        
        # Latency distribution
        fig.add_trace(
            go.Histogram(
                x=latencies_us,
                nbinsx=20,
                name='Distribution'
            ),
            row=2, col=1
        )
        
        # Top latency hops
        sorted_hops = sorted(zip(hop_numbers, latencies_us, ip_addresses), key=lambda x: x[1], reverse=True)[:5]
        top_hop_numbers, top_latencies, top_ips = zip(*sorted_hops)
        
        fig.add_trace(
            go.Bar(
                x=top_hop_numbers,
                y=top_latencies,
                name='Top Latency',
                text=top_ips,
                textposition='auto'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title='Network Latency Analysis Dashboard',
            height=800,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Hop Number", row=1, col=1)
        fig.update_yaxes(title_text="Latency (μs)", row=1, col=1)
        fig.update_xaxes(title_text="Hop Number", row=1, col=2)
        fig.update_yaxes(title_text="Cumulative Latency (μs)", row=1, col=2)
        fig.update_xaxes(title_text="Latency (μs)", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_xaxes(title_text="Hop Number", row=2, col=2)
        fig.update_yaxes(title_text="Latency (μs)", row=2, col=2)
        
        return fig
    
    def _get_latency_color(self, latency_us: float) -> str:
        """
        Get color based on latency value.
        """
        if latency_us < 1000:  # < 1ms
            return 'green'
        elif latency_us < 10000:  # < 10ms
            return 'yellow'
        elif latency_us < 50000:  # < 50ms
            return 'orange'
        else:
            return 'red'
    
    def export_visualizations(self, hops: List[HopData], output_dir: str) -> None:
        """
        Export all visualizations to files.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export interactive map
        map_viz = self.create_interactive_map(hops)
        map_viz.save(os.path.join(output_dir, 'network_path_map.html'))
        
        # Export dashboard
        dashboard = self.create_latency_dashboard(hops)
        dashboard.write_html(os.path.join(output_dir, 'latency_dashboard.html'))
        
        self.logger.info(f"Visualizations exported to {output_dir}")
