#!/usr/bin/env python3
"""
Shadoway 2025 - Shadow-Aware Pathfinding System
대구 빅데이터 분석대회 본선 진출작

Main demonstration script showing shade-priority route calculation
using building data and real-time solar position analysis.
"""

import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any

from solar_calculator import SolarCalculator, SolarPosition
from shadow_calculator import ShadowCalculator, Building, Point2D
from pathfinder import ShadeAwarePathfinder, PathNode, PathEdge, PathResult


class ShadowaySystem:
    """Main system class integrating all components"""
    
    def __init__(self, data_file: str):
        """Initialize system with building and path data"""
        self.data = self._load_data(data_file)
        self.location = self.data['location']
        self.buildings = self._parse_buildings()
        self.nodes = self._parse_nodes() 
        self.edges = self._parse_edges()
        
        # Initialize pathfinder
        self.pathfinder = ShadeAwarePathfinder(
            nodes=self.nodes,
            edges=self.edges,
            buildings=self.buildings,
            latitude=self.location['latitude'],
            longitude=self.location['longitude'],
            shade_preference=0.5  # 50% preference for shade
        )
        
        self.solar_calculator = SolarCalculator()
        self.shadow_calculator = ShadowCalculator(self.buildings)
    
    def _load_data(self, filename: str) -> Dict[str, Any]:
        """Load building and path data from JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _parse_buildings(self) -> List[Building]:
        """Convert JSON building data to Building objects"""
        buildings = []
        for b_data in self.data['buildings']:
            footprint = [Point2D(p['x'], p['y']) for p in b_data['footprint']]
            building = Building(
                id=b_data['id'],
                name=b_data['name'],
                footprint=footprint,
                height=b_data['height']
            )
            buildings.append(building)
        return buildings
    
    def _parse_nodes(self) -> List[PathNode]:
        """Convert JSON node data to PathNode objects"""
        nodes = []
        for n_data in self.data['path_nodes']:
            node = PathNode(
                id=n_data['id'],
                position=Point2D(n_data['x'], n_data['y'])
            )
            nodes.append(node)
        return nodes
    
    def _parse_edges(self) -> List[PathEdge]:
        """Convert JSON edge data to PathEdge objects"""
        edges = []
        for e_data in self.data['path_edges']:
            edge = PathEdge(
                from_node=e_data['from'],
                to_node=e_data['to'],
                base_weight=e_data['distance']
            )
            edges.append(edge)
        return edges
    
    def analyze_solar_position(self, dt: datetime) -> SolarPosition:
        """Get solar position for given time"""
        return self.solar_calculator.calculate_solar_position(
            self.location['latitude'],
            self.location['longitude'], 
            dt
        )
    
    def get_current_shadows(self, dt: datetime) -> List:
        """Calculate current shadow areas"""
        solar_pos = self.analyze_solar_position(dt)
        return self.shadow_calculator.calculate_all_shadows(solar_pos)
    
    def find_shade_route(
        self, 
        start_node: str, 
        end_node: str, 
        departure_time: datetime
    ) -> Dict[str, Any]:
        """
        Find optimal shade-priority route between two points.
        
        Returns comprehensive route analysis including:
        - Optimal path
        - Shadow coverage statistics
        - Comparison with shortest route
        - Time-based recommendations
        """
        # Get shade-optimal route
        shade_route = self.pathfinder.find_shade_optimal_path(
            start_node, end_node, departure_time
        )
        
        # Compare with standard shortest path
        route_comparison = self.pathfinder.compare_routes(
            start_node, end_node, departure_time
        )
        
        # Get solar position at departure time
        solar_pos = self.analyze_solar_position(departure_time)
        
        # Calculate current shadow coverage in area
        shadows = self.get_current_shadows(departure_time)
        
        # Get time-based recommendations for the day
        time_recommendations = self.pathfinder.get_time_based_recommendations(
            start_node, end_node, departure_time, time_range_hours=12
        )
        
        return {
            'departure_time': departure_time.isoformat(),
            'solar_position': {
                'azimuth': solar_pos.azimuth,
                'elevation': solar_pos.elevation,
                'zenith': solar_pos.zenith
            },
            'shade_route': self._route_to_dict(shade_route) if shade_route else None,
            'route_comparison': {
                key: self._route_to_dict(route) if route else None 
                for key, route in route_comparison.items()
            },
            'shadow_summary': {
                'total_shadows': len(shadows),
                'buildings_casting_shadows': [s.building_id for s in shadows if s.vertices]
            },
            'time_recommendations': [
                {
                    'time': rec[0].strftime('%H:%M'),
                    'shade_coverage': rec[1].shade_coverage,
                    'travel_time': rec[1].travel_time_minutes,
                    'path_length': len(rec[1].path)
                }
                for rec in time_recommendations[:6]  # Show top 6 recommendations
            ]
        }
    
    def _route_to_dict(self, route: PathResult) -> Dict[str, Any]:
        """Convert PathResult to dictionary for JSON serialization"""
        if not route:
            return None
            
        return {
            'path': route.path,
            'total_cost': round(route.total_cost, 2),
            'total_distance': round(route.total_distance, 1),
            'shade_coverage': round(route.shade_coverage, 3),
            'travel_time_minutes': round(route.travel_time_minutes, 1)
        }
    
    def generate_daily_analysis(self, date: datetime, start_node: str, end_node: str) -> Dict[str, Any]:
        """Generate analysis for different times throughout a day"""
        analysis_times = []
        
        # Analyze every 2 hours from 6 AM to 8 PM
        for hour in range(6, 21, 2):
            analysis_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            
            route_result = self.find_shade_route(start_node, end_node, analysis_time)
            
            analysis_times.append({
                'time': analysis_time.strftime('%H:%M'),
                'solar_elevation': route_result['solar_position']['elevation'],
                'solar_azimuth': route_result['solar_position']['azimuth'],
                'shade_route_coverage': route_result['shade_route']['shade_coverage'] if route_result['shade_route'] else 0,
                'shortest_route_coverage': route_result['route_comparison']['shortest']['shade_coverage'] if route_result['route_comparison']['shortest'] else 0,
                'improvement': (route_result['shade_route']['shade_coverage'] - route_result['route_comparison']['shortest']['shade_coverage']) if (route_result['shade_route'] and route_result['route_comparison']['shortest']) else 0
            })
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'route': f"{start_node} → {end_node}",
            'location': self.location['name'],
            'daily_analysis': analysis_times
        }


def main():
    """Main demonstration function"""
    print("=" * 60)
    print("SHADOWAY 2025 - Shadow-Aware Pathfinding System")
    print("대구 빅데이터 분석대회 본선 진출작")
    print("=" * 60)
    
    # Initialize system
    system = ShadowaySystem('sample_data.json')
    
    print(f"\n📍 Location: {system.location['name']}")
    print(f"   Coordinates: {system.location['latitude']:.4f}°N, {system.location['longitude']:.4f}°E")
    print(f"   Buildings loaded: {len(system.buildings)}")
    print(f"   Path nodes: {len(system.nodes)}")
    print(f"   Path edges: {len(system.edges)}")
    
    # Example route analysis
    start_node = "node_001"  # Main Station
    end_node = "node_009"    # University Gate
    
    # Test at different times
    test_times = [
        datetime(2025, 6, 21, 8, 0, 0),   # 8 AM - Summer solstice
        datetime(2025, 6, 21, 12, 0, 0),  # 12 PM - Noon
        datetime(2025, 6, 21, 16, 0, 0),  # 4 PM - Afternoon
        datetime(2025, 12, 21, 12, 0, 0), # 12 PM - Winter solstice
    ]
    
    print(f"\n🗺️  Route Analysis: Main Station → University Gate")
    print("-" * 60)
    
    for test_time in test_times:
        print(f"\n⏰ Time: {test_time.strftime('%Y-%m-%d %H:%M')} ({'Summer' if test_time.month == 6 else 'Winter'} solstice)")
        
        analysis = system.find_shade_route(start_node, end_node, test_time)
        
        # Solar position
        solar = analysis['solar_position']
        print(f"   ☀️ Solar Position: {solar['elevation']:.1f}° elevation, {solar['azimuth']:.1f}° azimuth")
        
        # Route comparison
        shade_route = analysis['shade_route']
        shortest_route = analysis['route_comparison']['shortest']
        
        if shade_route and shortest_route:
            print(f"   🌳 Shade Route: {shade_route['shade_coverage']:.1%} shade, {shade_route['total_distance']:.0f}m, {shade_route['travel_time_minutes']:.1f}min")
            print(f"   🏃 Shortest Route: {shortest_route['shade_coverage']:.1%} shade, {shortest_route['total_distance']:.0f}m, {shortest_route['travel_time_minutes']:.1f}min")
            
            shade_improvement = shade_route['shade_coverage'] - shortest_route['shade_coverage']
            distance_difference = shade_route['total_distance'] - shortest_route['total_distance']
            
            print(f"   📊 Improvement: +{shade_improvement:.1%} shade coverage, +{distance_difference:.0f}m distance")
        else:
            print("   ❌ No route found")
    
    # Daily analysis
    print(f"\n📅 Daily Analysis for Summer Solstice (2025-06-21)")
    print("-" * 60)
    
    daily_analysis = system.generate_daily_analysis(
        datetime(2025, 6, 21), start_node, end_node
    )
    
    for time_data in daily_analysis['daily_analysis']:
        improvement = time_data['improvement']
        symbol = "🌟" if improvement > 0.2 else "✅" if improvement > 0 else "⚠️"
        
        print(f"{symbol} {time_data['time']}: "
              f"Shade route {time_data['shade_route_coverage']:.1%} vs "
              f"shortest {time_data['shortest_route_coverage']:.1%} "
              f"(+{improvement:.1%} improvement)")
    
    # Best time recommendation
    best_time = max(daily_analysis['daily_analysis'], key=lambda x: x['improvement'])
    print(f"\n🏆 Best time for maximum shade: {best_time['time']} "
          f"(+{best_time['improvement']:.1%} shade improvement)")
    
    print(f"\n✅ Analysis complete! The system successfully:")
    print(f"   • Calculated real-time solar positions")
    print(f"   • Projected building shadows based on sun angle") 
    print(f"   • Applied Dijkstra's algorithm with shade-weighted edges")
    print(f"   • Recommended optimal departure times for maximum shade coverage")


if __name__ == "__main__":
    main()