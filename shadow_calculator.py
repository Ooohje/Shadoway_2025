#!/usr/bin/env python3
"""
Building Model and Shadow Calculator

Defines building structures and calculates their shadows based on solar position.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Set, NamedTuple
from solar_calculator import SolarPosition


@dataclass
class Point2D:
    """2D point representation"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point2D') -> float:
        """Calculate Euclidean distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class Building:
    """Building representation with footprint and height"""
    id: str
    footprint: List[Point2D]  # Building outline vertices (clockwise)
    height: float  # Building height in meters
    name: str = ""
    
    def get_center(self) -> Point2D:
        """Calculate building center point"""
        sum_x = sum(p.x for p in self.footprint)
        sum_y = sum(p.y for p in self.footprint)
        n = len(self.footprint)
        return Point2D(sum_x / n, sum_y / n)


class ShadowPolygon(NamedTuple):
    """Shadow area represented as a polygon"""
    vertices: List[Point2D]
    building_id: str


class ShadowCalculator:
    """Calculates building shadows based on solar position"""
    
    def __init__(self, buildings: List[Building]):
        self.buildings = buildings
    
    def calculate_shadow(
        self, 
        building: Building, 
        solar_position: SolarPosition
    ) -> ShadowPolygon:
        """
        Calculate shadow polygon for a building given solar position.
        
        Args:
            building: Building object
            solar_position: Current solar position
            
        Returns:
            ShadowPolygon representing the building's shadow
        """
        if solar_position.elevation <= 0:
            # No shadow when sun is below horizon
            return ShadowPolygon([], building.id)
        
        # Calculate shadow length based on building height and sun elevation
        shadow_length = building.height / math.tan(math.radians(solar_position.elevation))
        
        # Shadow direction (opposite to sun)
        shadow_direction = math.radians((solar_position.azimuth + 180) % 360)
        
        # Calculate shadow offset
        shadow_dx = shadow_length * math.sin(shadow_direction)
        shadow_dy = shadow_length * math.cos(shadow_direction)
        
        # Project building footprint to create shadow polygon
        shadow_vertices = []
        
        # Add original building vertices
        for vertex in building.footprint:
            shadow_vertices.append(vertex)
        
        # Add projected shadow vertices (in reverse order for proper polygon)
        for vertex in reversed(building.footprint):
            shadow_point = Point2D(
                vertex.x + shadow_dx,
                vertex.y + shadow_dy
            )
            shadow_vertices.append(shadow_point)
        
        return ShadowPolygon(shadow_vertices, building.id)
    
    def calculate_all_shadows(self, solar_position: SolarPosition) -> List[ShadowPolygon]:
        """Calculate shadows for all buildings"""
        shadows = []
        for building in self.buildings:
            shadow = self.calculate_shadow(building, solar_position)
            if shadow.vertices:  # Only add non-empty shadows
                shadows.append(shadow)
        return shadows
    
    def is_point_in_shadow(
        self, 
        point: Point2D, 
        shadows: List[ShadowPolygon]
    ) -> bool:
        """
        Check if a point is within any shadow polygon using ray casting algorithm.
        
        Args:
            point: Point to check
            shadows: List of shadow polygons
            
        Returns:
            True if point is in shadow, False otherwise
        """
        for shadow in shadows:
            if self._point_in_polygon(point, shadow.vertices):
                return True
        return False
    
    def _point_in_polygon(self, point: Point2D, polygon: List[Point2D]) -> bool:
        """
        Ray casting algorithm to determine if point is inside polygon.
        
        Args:
            point: Point to test
            polygon: Polygon vertices
            
        Returns:
            True if point is inside polygon
        """
        if len(polygon) < 3:
            return False
        
        x, y = point.x, point.y
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0].x, polygon[0].y
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n].x, polygon[i % n].y
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def get_shadow_coverage_ratio(
        self, 
        area_bounds: Tuple[Point2D, Point2D], 
        shadows: List[ShadowPolygon],
        grid_resolution: int = 50
    ) -> float:
        """
        Calculate what percentage of an area is covered by shadows.
        
        Args:
            area_bounds: (min_point, max_point) defining rectangular area
            shadows: List of shadow polygons
            grid_resolution: Number of sample points per dimension
            
        Returns:
            Ratio of area in shadow (0.0 to 1.0)
        """
        min_point, max_point = area_bounds
        
        total_points = 0
        shadowed_points = 0
        
        x_step = (max_point.x - min_point.x) / grid_resolution
        y_step = (max_point.y - min_point.y) / grid_resolution
        
        for i in range(grid_resolution):
            for j in range(grid_resolution):
                test_point = Point2D(
                    min_point.x + i * x_step,
                    min_point.y + j * y_step
                )
                total_points += 1
                if self.is_point_in_shadow(test_point, shadows):
                    shadowed_points += 1
        
        return shadowed_points / total_points if total_points > 0 else 0.0


if __name__ == "__main__":
    # Example usage
    from datetime import datetime
    from solar_calculator import SolarCalculator
    
    # Create sample buildings
    building1 = Building(
        id="b1",
        name="Office Building",
        footprint=[
            Point2D(0, 0),
            Point2D(20, 0),
            Point2D(20, 30),
            Point2D(0, 30)
        ],
        height=50  # 50 meters tall
    )
    
    building2 = Building(
        id="b2", 
        name="Shopping Center",
        footprint=[
            Point2D(50, 10),
            Point2D(80, 10),
            Point2D(80, 40),
            Point2D(50, 40)
        ],
        height=20  # 20 meters tall
    )
    
    # Initialize shadow calculator
    shadow_calc = ShadowCalculator([building1, building2])
    
    # Calculate solar position for Seoul at noon
    solar_calc = SolarCalculator()
    seoul_lat, seoul_lon = 37.5665, 126.9780
    noon_time = datetime(2025, 6, 21, 12, 0, 0)
    
    solar_pos = solar_calc.calculate_solar_position(seoul_lat, seoul_lon, noon_time)
    print(f"Solar Position: Az={solar_pos.azimuth:.1f}°, El={solar_pos.elevation:.1f}°")
    
    # Calculate shadows
    shadows = shadow_calc.calculate_all_shadows(solar_pos)
    
    print(f"\nCalculated {len(shadows)} shadows:")
    for shadow in shadows:
        print(f"Building {shadow.building_id}: {len(shadow.vertices)} shadow vertices")
    
    # Test if specific points are in shadow
    test_points = [Point2D(10, 15), Point2D(60, 25), Point2D(100, 50)]
    
    print(f"\nShadow coverage test:")
    for i, point in enumerate(test_points):
        in_shadow = shadow_calc.is_point_in_shadow(point, shadows)
        print(f"Point {i+1} ({point.x}, {point.y}): {'In shadow' if in_shadow else 'In sunlight'}")