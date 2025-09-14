#!/usr/bin/env python3
"""
Shade-Aware Pathfinding using Modified Dijkstra's Algorithm

Implements pathfinding that prioritizes shaded routes by incorporating
shadow information into edge weights.
"""

import heapq
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set, Optional, NamedTuple
from dataclasses import dataclass

from solar_calculator import SolarCalculator, SolarPosition
from shadow_calculator import ShadowCalculator, Point2D, Building, ShadowPolygon


class PathNode(NamedTuple):
    """Node in the path graph"""
    id: str
    position: Point2D
    
    
class PathEdge(NamedTuple):
    """Edge connecting two nodes"""
    from_node: str
    to_node: str
    base_weight: float  # Base distance/time weight
    

@dataclass
class PathResult:
    """Result of pathfinding operation"""
    path: List[str]  # Node IDs in order
    total_cost: float
    total_distance: float
    shade_coverage: float  # Percentage of path in shade (0.0-1.0)
    travel_time_minutes: float


class ShadeAwarePathfinder:
    """
    Pathfinder that prioritizes shaded routes using modified Dijkstra's algorithm.
    Edge weights are adjusted based on shadow coverage at different times.
    """
    
    def __init__(
        self,
        nodes: List[PathNode],
        edges: List[PathEdge], 
        buildings: List[Building],
        latitude: float,
        longitude: float,
        shade_preference: float = 0.3  # 0.0 = no preference, 1.0 = maximum shade preference
    ):
        self.nodes = {node.id: node for node in nodes}
        self.edges = self._build_adjacency_list(edges)
        self.shadow_calculator = ShadowCalculator(buildings)
        self.solar_calculator = SolarCalculator()
        self.latitude = latitude
        self.longitude = longitude
        self.shade_preference = max(0.0, min(1.0, shade_preference))
        
        # Cache for shadow calculations
        self._shadow_cache: Dict[datetime, List[ShadowPolygon]] = {}
    
    def _build_adjacency_list(self, edges: List[PathEdge]) -> Dict[str, List[Tuple[str, float]]]:
        """Build adjacency list from edges"""
        adj_list = {}
        
        for edge in edges:
            # Add forward edge
            if edge.from_node not in adj_list:
                adj_list[edge.from_node] = []
            adj_list[edge.from_node].append((edge.to_node, edge.base_weight))
            
            # Add reverse edge (assuming bidirectional paths)
            if edge.to_node not in adj_list:
                adj_list[edge.to_node] = []
            adj_list[edge.to_node].append((edge.from_node, edge.base_weight))
        
        return adj_list
    
    def _get_shadows_at_time(self, dt: datetime) -> List[ShadowPolygon]:
        """Get cached shadow polygons for a specific time"""
        if dt not in self._shadow_cache:
            solar_pos = self.solar_calculator.calculate_solar_position(
                self.latitude, self.longitude, dt
            )
            shadows = self.shadow_calculator.calculate_all_shadows(solar_pos)
            self._shadow_cache[dt] = shadows
        
        return self._shadow_cache[dt]
    
    def _calculate_edge_shadow_coverage(
        self, 
        from_node_id: str, 
        to_node_id: str, 
        dt: datetime,
        sample_points: int = 10
    ) -> float:
        """
        Calculate what percentage of an edge is covered by shadows.
        
        Args:
            from_node_id: Starting node ID
            to_node_id: Ending node ID  
            dt: Time for shadow calculation
            sample_points: Number of points to sample along the edge
            
        Returns:
            Ratio of edge length in shadow (0.0 to 1.0)
        """
        from_node = self.nodes[from_node_id]
        to_node = self.nodes[to_node_id]
        shadows = self._get_shadows_at_time(dt)
        
        if not shadows:
            return 0.0
        
        # Sample points along the edge
        shadowed_points = 0
        total_points = sample_points
        
        for i in range(sample_points):
            t = i / (sample_points - 1) if sample_points > 1 else 0
            sample_point = Point2D(
                from_node.position.x + t * (to_node.position.x - from_node.position.x),
                from_node.position.y + t * (to_node.position.y - from_node.position.y)
            )
            
            if self.shadow_calculator.is_point_in_shadow(sample_point, shadows):
                shadowed_points += 1
        
        return shadowed_points / total_points
    
    def _calculate_dynamic_edge_weight(
        self,
        from_node_id: str,
        to_node_id: str, 
        base_weight: float,
        start_time: datetime,
        travel_duration_minutes: float = 5.0
    ) -> Tuple[float, float]:
        """
        Calculate time-dependent edge weight considering shadows.
        
        Args:
            from_node_id: Starting node
            to_node_id: Ending node
            base_weight: Base distance weight
            start_time: Time when traversing this edge
            travel_duration_minutes: Estimated time to traverse edge
            
        Returns:
            (adjusted_weight, shade_coverage)
        """
        # Calculate average shadow coverage during edge traversal
        mid_time = start_time + timedelta(minutes=travel_duration_minutes / 2)
        shade_coverage = self._calculate_edge_shadow_coverage(
            from_node_id, to_node_id, mid_time
        )
        
        # Adjust weight based on shade preference
        # More shade = lower weight (preferred)
        shade_bonus = self.shade_preference * shade_coverage
        adjusted_weight = base_weight * (1.0 - shade_bonus)
        
        return adjusted_weight, shade_coverage
    
    def find_shade_optimal_path(
        self,
        start_node_id: str,
        end_node_id: str,
        start_time: datetime,
        walking_speed_kmh: float = 5.0
    ) -> Optional[PathResult]:
        """
        Find optimal path considering shade coverage using modified Dijkstra's algorithm.
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Destination node ID  
            start_time: Journey start time
            walking_speed_kmh: Walking speed in km/h
            
        Returns:
            PathResult with optimal route or None if no path exists
        """
        if start_node_id not in self.nodes or end_node_id not in self.nodes:
            return None
        
        # Priority queue: (total_cost, current_time, node_id, path, total_distance, total_shade_coverage)
        pq = [(0.0, start_time, start_node_id, [start_node_id], 0.0, 0.0)]
        visited = set()
        
        # Convert walking speed to m/min for calculations
        walking_speed_m_per_min = (walking_speed_kmh * 1000) / 60
        
        while pq:
            current_cost, current_time, current_node, path, total_distance, accumulated_shade = heapq.heappop(pq)
            
            if current_node in visited:
                continue
                
            visited.add(current_node)
            
            if current_node == end_node_id:
                # Found destination, calculate final metrics
                avg_shade_coverage = accumulated_shade / len(path) if len(path) > 1 else 0.0
                travel_time = total_distance / walking_speed_m_per_min
                
                return PathResult(
                    path=path,
                    total_cost=current_cost,
                    total_distance=total_distance,
                    shade_coverage=avg_shade_coverage,
                    travel_time_minutes=travel_time
                )
            
            # Explore neighbors
            if current_node in self.edges:
                for neighbor_id, base_weight in self.edges[current_node]:
                    if neighbor_id not in visited:
                        # Calculate travel time for this edge
                        edge_travel_time = base_weight / walking_speed_m_per_min
                        next_time = current_time + timedelta(minutes=edge_travel_time)
                        
                        # Calculate adjusted weight considering shadows
                        adjusted_weight, shade_coverage = self._calculate_dynamic_edge_weight(
                            current_node, neighbor_id, base_weight, current_time, edge_travel_time
                        )
                        
                        new_cost = current_cost + adjusted_weight
                        new_distance = total_distance + base_weight
                        new_shade_accumulation = accumulated_shade + shade_coverage
                        new_path = path + [neighbor_id]
                        
                        heapq.heappush(pq, (
                            new_cost, 
                            next_time,
                            neighbor_id, 
                            new_path, 
                            new_distance,
                            new_shade_accumulation
                        ))
        
        return None  # No path found
    
    def compare_routes(
        self,
        start_node_id: str,
        end_node_id: str, 
        start_time: datetime,
        walking_speed_kmh: float = 5.0
    ) -> Dict[str, Optional[PathResult]]:
        """
        Compare shade-optimized route vs standard shortest path.
        
        Returns:
            Dictionary with 'shade_optimal' and 'shortest' route results
        """
        # Get shade-optimal route
        original_preference = self.shade_preference
        
        # Shade-optimal route
        self.shade_preference = original_preference
        shade_route = self.find_shade_optimal_path(
            start_node_id, end_node_id, start_time, walking_speed_kmh
        )
        
        # Standard shortest path (no shade preference)
        self.shade_preference = 0.0
        shortest_route = self.find_shade_optimal_path(
            start_node_id, end_node_id, start_time, walking_speed_kmh
        )
        
        # Restore original preference
        self.shade_preference = original_preference
        
        return {
            'shade_optimal': shade_route,
            'shortest': shortest_route
        }
    
    def get_time_based_recommendations(
        self,
        start_node_id: str,
        end_node_id: str,
        date: datetime,
        time_range_hours: int = 12,
        interval_minutes: int = 60
    ) -> List[Tuple[datetime, PathResult]]:
        """
        Get route recommendations for different times of day.
        
        Args:
            start_node_id: Start location
            end_node_id: End location  
            date: Base date (time will be varied)
            time_range_hours: Range of hours to analyze
            interval_minutes: Time interval between analyses
            
        Returns:
            List of (time, route_result) tuples
        """
        recommendations = []
        
        start_hour = 6  # Start from 6 AM
        total_intervals = (time_range_hours * 60) // interval_minutes
        
        for i in range(total_intervals):
            current_time = date.replace(
                hour=start_hour,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(minutes=i * interval_minutes)
            
            route = self.find_shade_optimal_path(start_node_id, end_node_id, current_time)
            if route:
                recommendations.append((current_time, route))
        
        return recommendations


if __name__ == "__main__":
    # Example usage with sample data
    from datetime import datetime
    
    # Create sample nodes (representing intersections/waypoints)
    nodes = [
        PathNode("A", Point2D(0, 0)),
        PathNode("B", Point2D(50, 0)), 
        PathNode("C", Point2D(100, 0)),
        PathNode("D", Point2D(0, 50)),
        PathNode("E", Point2D(50, 50)),
        PathNode("F", Point2D(100, 50)),
        PathNode("G", Point2D(0, 100)),
        PathNode("H", Point2D(50, 100)),
        PathNode("I", Point2D(100, 100))
    ]
    
    # Create sample edges (distances in meters)
    edges = [
        PathEdge("A", "B", 50), PathEdge("B", "C", 50),
        PathEdge("A", "D", 50), PathEdge("B", "E", 50), PathEdge("C", "F", 50),
        PathEdge("D", "E", 50), PathEdge("E", "F", 50),
        PathEdge("D", "G", 50), PathEdge("E", "H", 50), PathEdge("F", "I", 50),
        PathEdge("G", "H", 50), PathEdge("H", "I", 50),
        # Diagonal connections
        PathEdge("A", "E", 70.7), PathEdge("E", "I", 70.7),
        PathEdge("C", "E", 70.7), PathEdge("E", "G", 70.7)
    ]
    
    # Create sample buildings
    buildings = [
        Building(
            id="tower1",
            name="Office Tower", 
            footprint=[Point2D(20, 20), Point2D(30, 20), Point2D(30, 30), Point2D(20, 30)],
            height=100
        ),
        Building(
            id="mall1",
            name="Shopping Mall",
            footprint=[Point2D(70, 70), Point2D(90, 70), Point2D(90, 90), Point2D(70, 90)], 
            height=25
        )
    ]
    
    # Initialize pathfinder for Seoul
    pathfinder = ShadeAwarePathfinder(
        nodes=nodes,
        edges=edges,
        buildings=buildings,
        latitude=37.5665,  # Seoul
        longitude=126.9780,
        shade_preference=0.4  # 40% preference for shade
    )
    
    # Find shade-optimal route
    start_time = datetime(2025, 6, 21, 14, 0, 0)  # 2 PM on summer solstice
    
    print("Finding shade-optimal route from A to I...")
    result = pathfinder.find_shade_optimal_path("A", "I", start_time)
    
    if result:
        print(f"Path: {' -> '.join(result.path)}")
        print(f"Total distance: {result.total_distance:.1f}m")
        print(f"Travel time: {result.travel_time_minutes:.1f} minutes")
        print(f"Shade coverage: {result.shade_coverage:.1%}")
        print(f"Total cost: {result.total_cost:.2f}")
    else:
        print("No path found!")
    
    # Compare routes
    print(f"\nComparing routes:")
    comparison = pathfinder.compare_routes("A", "I", start_time)
    
    for route_type, route_result in comparison.items():
        if route_result:
            print(f"\n{route_type.title()} route:")
            print(f"  Path: {' -> '.join(route_result.path)}")
            print(f"  Distance: {route_result.total_distance:.1f}m") 
            print(f"  Shade coverage: {route_result.shade_coverage:.1%}")
            print(f"  Travel time: {route_result.travel_time_minutes:.1f} min")