#!/usr/bin/env python3
"""
Visualization utility for Shadoway system

Creates visual representations of:
- Building layouts and shadows
- Path networks  
- Route comparisons
- Shadow coverage over time
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

from solar_calculator import SolarCalculator
from shadow_calculator import ShadowCalculator, Building, Point2D
from pathfinder import ShadeAwarePathfinder, PathNode, PathEdge
from shadoway_main import ShadowaySystem


class ShadowayVisualizer:
    """Visualization tools for the Shadoway system"""
    
    def __init__(self, data_file: str):
        self.system = ShadowaySystem(data_file)
        
    def plot_buildings_and_shadows(self, dt: datetime, figsize=(12, 10)):
        """Plot buildings and their shadows at a specific time"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get solar position and shadows
        solar_pos = self.system.analyze_solar_position(dt)
        shadows = self.system.get_current_shadows(dt)
        
        # Plot buildings
        for building in self.system.buildings:
            # Building footprint
            building_x = [p.x for p in building.footprint] + [building.footprint[0].x]
            building_y = [p.y for p in building.footprint] + [building.footprint[0].y]
            ax.fill(building_x, building_y, color='gray', alpha=0.8, label='Buildings')
            
            # Building label
            center = building.get_center()
            ax.text(center.x, center.y, f"{building.name}\n{building.height}m", 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Plot shadows
        for shadow in shadows:
            if shadow.vertices:
                shadow_x = [p.x for p in shadow.vertices] + [shadow.vertices[0].x]
                shadow_y = [p.y for p in shadow.vertices] + [shadow.vertices[0].y]
                ax.fill(shadow_x, shadow_y, color='blue', alpha=0.3, label='Shadows')
        
        # Plot path nodes
        for node in self.system.nodes:
            ax.plot(node.position.x, node.position.y, 'ro', markersize=8)
            ax.text(node.position.x + 10, node.position.y + 10, node.id, fontsize=8)
        
        # Plot path edges
        node_dict = {node.id: node for node in self.system.nodes}
        for edge in self.system.edges:
            if edge.from_node in node_dict and edge.to_node in node_dict:
                from_pos = node_dict[edge.from_node].position
                to_pos = node_dict[edge.to_node].position
                ax.plot([from_pos.x, to_pos.x], [from_pos.y, to_pos.y], 
                       'k-', alpha=0.5, linewidth=1)
        
        # Add solar information
        sun_info = f"Time: {dt.strftime('%H:%M')}\nSun: {solar_pos.elevation:.1f}° elevation, {solar_pos.azimuth:.1f}° azimuth"
        ax.text(0.02, 0.98, sun_info, transform=ax.transAxes, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
        
        ax.set_xlabel('X coordinate (m)')
        ax.set_ylabel('Y coordinate (m)')
        ax.set_title(f'Shadoway Analysis - {dt.strftime("%Y-%m-%d %H:%M")}')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # Remove duplicate labels
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        
        plt.tight_layout()
        return fig
    
    def plot_route_comparison(self, start_node: str, end_node: str, dt: datetime, figsize=(12, 8)):
        """Plot comparison between shade-optimal and shortest routes"""
        fig, ax = plt.subplots(figsize=figsize)
        
        # Get routes
        analysis = self.system.find_shade_route(start_node, end_node, dt)
        shade_route = analysis['shade_route']
        shortest_route = analysis['route_comparison']['shortest']
        
        # Plot buildings (lighter)
        for building in self.system.buildings:
            building_x = [p.x for p in building.footprint] + [building.footprint[0].x]
            building_y = [p.y for p in building.footprint] + [building.footprint[0].y]
            ax.fill(building_x, building_y, color='lightgray', alpha=0.5)
        
        # Plot shadows
        shadows = self.system.get_current_shadows(dt)
        for shadow in shadows:
            if shadow.vertices:
                shadow_x = [p.x for p in shadow.vertices] + [shadow.vertices[0].x]
                shadow_y = [p.y for p in shadow.vertices] + [shadow.vertices[0].y]
                ax.fill(shadow_x, shadow_y, color='blue', alpha=0.2)
        
        # Plot nodes
        node_dict = {node.id: node for node in self.system.nodes}
        for node in self.system.nodes:
            ax.plot(node.position.x, node.position.y, 'ko', markersize=6, alpha=0.5)
        
        # Plot shortest route
        if shortest_route and shortest_route['path']:
            route_x = [node_dict[node_id].position.x for node_id in shortest_route['path']]
            route_y = [node_dict[node_id].position.y for node_id in shortest_route['path']]
            ax.plot(route_x, route_y, 'r-', linewidth=3, alpha=0.7, 
                   label=f"Shortest Route ({shortest_route['shade_coverage']:.1%} shade)")
        
        # Plot shade-optimal route
        if shade_route and shade_route['path']:
            route_x = [node_dict[node_id].position.x for node_id in shade_route['path']]
            route_y = [node_dict[node_id].position.y for node_id in shade_route['path']]
            ax.plot(route_x, route_y, 'g-', linewidth=3, alpha=0.9,
                   label=f"Shade Route ({shade_route['shade_coverage']:.1%} shade)")
        
        # Highlight start and end
        start_pos = node_dict[start_node].position
        end_pos = node_dict[end_node].position
        ax.plot(start_pos.x, start_pos.y, 'go', markersize=12, label='Start')
        ax.plot(end_pos.x, end_pos.y, 'ro', markersize=12, label='End')
        
        ax.set_xlabel('X coordinate (m)')
        ax.set_ylabel('Y coordinate (m)')
        ax.set_title(f'Route Comparison: {start_node} → {end_node}\n{dt.strftime("%Y-%m-%d %H:%M")}')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.set_aspect('equal')
        
        plt.tight_layout()
        return fig
    
    def plot_daily_analysis(self, start_node: str, end_node: str, date: datetime, figsize=(14, 8)):
        """Plot shade coverage analysis throughout the day"""
        daily_analysis = self.system.generate_daily_analysis(date, start_node, end_node)
        
        times = [item['time'] for item in daily_analysis['daily_analysis']]
        shade_route_coverage = [item['shade_route_coverage'] for item in daily_analysis['daily_analysis']]
        shortest_route_coverage = [item['shortest_route_coverage'] for item in daily_analysis['daily_analysis']]
        improvements = [item['improvement'] for item in daily_analysis['daily_analysis']]
        solar_elevations = [item['solar_elevation'] for item in daily_analysis['daily_analysis']]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
        
        # Plot 1: Shade coverage comparison
        ax1.plot(times, [x * 100 for x in shade_route_coverage], 'g-o', 
                linewidth=2, markersize=6, label='Shade-Optimal Route')
        ax1.plot(times, [x * 100 for x in shortest_route_coverage], 'r-s', 
                linewidth=2, markersize=6, label='Shortest Route')
        ax1.fill_between(times, [x * 100 for x in shade_route_coverage], 
                        [x * 100 for x in shortest_route_coverage], 
                        alpha=0.3, color='green', label='Improvement')
        
        ax1.set_ylabel('Shade Coverage (%)')
        ax1.set_title(f'Daily Shade Analysis: {start_node} → {end_node}\n{date.strftime("%Y-%m-%d")}')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot 2: Solar elevation and improvement
        ax2_twin = ax2.twinx()
        
        bars = ax2.bar(times, [x * 100 for x in improvements], alpha=0.6, color='orange',
                      label='Shade Improvement (%)')
        line = ax2_twin.plot(times, solar_elevations, 'b-', linewidth=2, 
                           marker='D', markersize=4, label='Solar Elevation (°)')
        
        ax2.set_xlabel('Time of Day')
        ax2.set_ylabel('Shade Improvement (%)', color='orange')
        ax2_twin.set_ylabel('Solar Elevation (°)', color='blue')
        ax2.grid(True, alpha=0.3)
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig


def main():
    """Generate visualization examples"""
    visualizer = ShadowayVisualizer('sample_data.json')
    
    # Example times
    summer_morning = datetime(2025, 6, 21, 8, 0, 0)
    summer_noon = datetime(2025, 6, 21, 12, 0, 0)
    summer_afternoon = datetime(2025, 6, 21, 16, 0, 0)
    
    # Generate visualizations
    print("Generating Shadoway visualizations...")
    
    # 1. Buildings and shadows at different times
    fig1 = visualizer.plot_buildings_and_shadows(summer_morning)
    fig1.savefig('shadoway_morning.png', dpi=150, bbox_inches='tight')
    
    fig2 = visualizer.plot_buildings_and_shadows(summer_noon)  
    fig2.savefig('shadoway_noon.png', dpi=150, bbox_inches='tight')
    
    fig3 = visualizer.plot_buildings_and_shadows(summer_afternoon)
    fig3.savefig('shadoway_afternoon.png', dpi=150, bbox_inches='tight')
    
    # 2. Route comparison
    fig4 = visualizer.plot_route_comparison('node_001', 'node_009', summer_morning)
    fig4.savefig('route_comparison.png', dpi=150, bbox_inches='tight')
    
    # 3. Daily analysis
    fig5 = visualizer.plot_daily_analysis('node_001', 'node_009', summer_morning)
    fig5.savefig('daily_analysis.png', dpi=150, bbox_inches='tight')
    
    print("✅ Visualizations saved:")
    print("   - shadoway_morning.png")
    print("   - shadoway_noon.png") 
    print("   - shadoway_afternoon.png")
    print("   - route_comparison.png")
    print("   - daily_analysis.png")
    
    plt.show()


if __name__ == "__main__":
    main()