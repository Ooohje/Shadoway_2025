#!/usr/bin/env python3
"""
Solar Position Calculator

Calculates precise solar position (azimuth and elevation) for any given
date, time, and geographic location using astronomical algorithms.
"""

import math
from datetime import datetime
from typing import Tuple, NamedTuple


class SolarPosition(NamedTuple):
    """Solar position data structure"""
    azimuth: float  # degrees from north (0-360)
    elevation: float  # degrees above horizon (-90 to 90)
    zenith: float  # degrees from vertical (0-180)


class SolarCalculator:
    """
    Calculates solar position using simplified astronomical algorithms.
    Based on NOAA Solar Position Calculator algorithms.
    """
    
    @staticmethod
    def calculate_solar_position(
        latitude: float, 
        longitude: float, 
        dt: datetime
    ) -> SolarPosition:
        """
        Calculate solar position using simplified but accurate astronomical formulas.
        
        Args:
            latitude: Latitude in degrees (-90 to 90)
            longitude: Longitude in degrees (-180 to 180)
            dt: datetime object for the calculation
            
        Returns:
            SolarPosition with azimuth, elevation, and zenith angles
        """
        # Convert to radians
        lat_rad = math.radians(latitude)
        
        # Day of year
        day_of_year = dt.timetuple().tm_yday
        
        # Solar declination (varies from -23.45° to +23.45° throughout the year)
        # Summer solstice around day 172, winter solstice around day 355
        declination_rad = math.radians(23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365)))
        
        # Time calculation
        hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        
        # Equation of time (accounts for elliptical orbit and axial tilt)
        b = 2 * math.pi * (day_of_year - 81) / 365
        equation_of_time = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
        
        # Time zone correction (assume local time is used)
        # For Korea, standard time is UTC+9, so longitude correction
        time_zone_offset = 9  # Korea Standard Time
        longitude_correction = (longitude - (15 * time_zone_offset)) * 4 / 60  # Convert to hours
        
        # Solar time
        solar_time = hour + longitude_correction + equation_of_time / 60
        
        # Hour angle (solar noon = 0°, morning negative, afternoon positive)
        hour_angle_rad = math.radians(15 * (solar_time - 12))
        
        # Solar elevation angle
        sin_elevation = (math.sin(declination_rad) * math.sin(lat_rad) + 
                        math.cos(declination_rad) * math.cos(lat_rad) * math.cos(hour_angle_rad))
        
        elevation_rad = math.asin(max(-1, min(1, sin_elevation)))
        elevation = math.degrees(elevation_rad)
        
        # Solar azimuth angle
        if abs(math.cos(elevation_rad)) < 1e-10:  # Near zenith
            azimuth = 180 if hour_angle_rad > 0 else 0
        else:
            cos_azimuth = ((math.sin(declination_rad) * math.cos(lat_rad) - 
                           math.cos(declination_rad) * math.sin(lat_rad) * math.cos(hour_angle_rad)) / 
                          math.cos(elevation_rad))
            
            cos_azimuth = max(-1, min(1, cos_azimuth))
            azimuth_rad = math.acos(cos_azimuth)
            azimuth = math.degrees(azimuth_rad)
            
            # Adjust for afternoon (hour angle > 0)
            if hour_angle_rad > 0:
                azimuth = 360 - azimuth
        
        # Zenith angle
        zenith = 90 - elevation
        
        return SolarPosition(azimuth, elevation, zenith)
    
    @staticmethod
    def is_sun_up(elevation: float) -> bool:
        """Check if sun is above horizon"""
        return elevation > 0
    
    @staticmethod
    def get_shadow_direction(azimuth: float) -> float:
        """
        Get shadow direction (opposite to sun azimuth)
        
        Args:
            azimuth: Sun azimuth in degrees
            
        Returns:
            Shadow direction in degrees (0-360)
        """
        return (azimuth + 180) % 360


if __name__ == "__main__":
    # Example usage
    calculator = SolarCalculator()
    
    # Example: Seoul, South Korea coordinates
    seoul_lat = 37.5665
    seoul_lon = 126.9780
    
    # Current time example
    now = datetime(2025, 6, 21, 12, 0, 0)  # Summer solstice noon
    
    position = calculator.calculate_solar_position(seoul_lat, seoul_lon, now)
    print(f"Solar Position at {now}:")
    print(f"Azimuth: {position.azimuth:.2f}°")
    print(f"Elevation: {position.elevation:.2f}°")
    print(f"Zenith: {position.zenith:.2f}°")
    print(f"Sun is up: {calculator.is_sun_up(position.elevation)}")
    print(f"Shadow direction: {calculator.get_shadow_direction(position.azimuth):.2f}°")