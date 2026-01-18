"""
Human Behavior Simulation
Realistic timing, mouse movements, and interaction patterns
"""

import asyncio
import random
import math
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class Point:
    """2D point for mouse movements"""
    x: float
    y: float


class Humanizer:
    """
    Simulates human-like behavior for browser automation
    All methods include realistic timing variations
    """
    
    # Timing distributions (milliseconds)
    CLICK_DELAY_MIN = 50
    CLICK_DELAY_MAX = 150
    TYPING_DELAY_MIN = 50
    TYPING_DELAY_MAX = 200
    SCROLL_DELAY_MIN = 100
    SCROLL_DELAY_MAX = 300
    ACTION_DELAY_MIN = 500
    ACTION_DELAY_MAX = 2000
    READ_DELAY_MIN = 1000
    READ_DELAY_MAX = 3000
    
    @staticmethod
    async def random_delay(min_ms: int = 100, max_ms: int = 500) -> None:
        """Wait for a random duration within range"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def human_delay(base_ms: int = 1000, variance: float = 0.3) -> None:
        """
        Human-like delay with natural variance
        Uses log-normal distribution for more realistic timing
        """
        # Log-normal gives right-skewed distribution (more short pauses, occasional long ones)
        mean = math.log(base_ms)
        sigma = variance
        delay_ms = random.lognormvariate(mean, sigma)
        delay_ms = max(100, min(delay_ms, base_ms * 3))  # Clamp to reasonable range
        await asyncio.sleep(delay_ms / 1000)
    
    @staticmethod
    def generate_bezier_path(
        start: Point, 
        end: Point, 
        num_points: int = 20,
        deviation: float = 0.3
    ) -> List[Point]:
        """
        Generate a bezier curve path between two points
        Simulates natural mouse movement with slight curves
        """
        # Calculate control points with random deviation
        dx = end.x - start.x
        dy = end.y - start.y
        
        # Two control points for cubic bezier
        ctrl1 = Point(
            start.x + dx * 0.25 + random.uniform(-deviation, deviation) * abs(dx),
            start.y + dy * 0.25 + random.uniform(-deviation, deviation) * abs(dy)
        )
        ctrl2 = Point(
            start.x + dx * 0.75 + random.uniform(-deviation, deviation) * abs(dx),
            start.y + dy * 0.75 + random.uniform(-deviation, deviation) * abs(dy)
        )
        
        path = []
        for i in range(num_points + 1):
            t = i / num_points
            
            # Cubic bezier calculation
            x = (1-t)**3 * start.x + \
                3 * (1-t)**2 * t * ctrl1.x + \
                3 * (1-t) * t**2 * ctrl2.x + \
                t**3 * end.x
            
            y = (1-t)**3 * start.y + \
                3 * (1-t)**2 * t * ctrl1.y + \
                3 * (1-t) * t**2 * ctrl2.y + \
                t**3 * end.y
            
            # Add micro-jitter for realism
            x += random.uniform(-0.5, 0.5)
            y += random.uniform(-0.5, 0.5)
            
            path.append(Point(x, y))
        
        return path
    
    @staticmethod
    def calculate_movement_duration(distance: float) -> int:
        """
        Calculate realistic mouse movement duration based on Fitts's law
        Returns duration in milliseconds
        """
        # Base duration + distance factor with random variance
        base_duration = 100
        distance_factor = 0.8  # ms per pixel
        duration = base_duration + distance * distance_factor
        
        # Add variance
        variance = random.uniform(0.8, 1.2)
        return int(duration * variance)
    
    @classmethod
    async def move_mouse(
        cls, 
        page, 
        target_x: float, 
        target_y: float,
        current_x: Optional[float] = None,
        current_y: Optional[float] = None
    ) -> None:
        """
        Move mouse along a natural bezier curve path
        """
        if current_x is None:
            current_x = random.randint(100, 500)
        if current_y is None:
            current_y = random.randint(100, 500)
        
        start = Point(current_x, current_y)
        end = Point(target_x, target_y)
        
        # Calculate distance and duration
        distance = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
        total_duration = cls.calculate_movement_duration(distance)
        
        # Generate path
        path = cls.generate_bezier_path(start, end)
        
        # Move along path
        step_duration = total_duration / len(path)
        for point in path:
            await page.mouse.move(point.x, point.y)
            await asyncio.sleep(step_duration / 1000)
    
    @classmethod
    async def human_click(
        cls, 
        page, 
        selector: str,
        move_to_element: bool = True
    ) -> None:
        """
        Perform a human-like click with natural mouse movement
        """
        # Find element
        element = await page.wait_for_selector(selector, timeout=10000)
        if not element:
            raise Exception(f"Element not found: {selector}")
        
        # Get element bounding box
        box = await element.bounding_box()
        if not box:
            raise Exception(f"Could not get bounding box for: {selector}")
        
        # Calculate click position with offset (not exactly center)
        offset_x = random.uniform(-box['width'] * 0.2, box['width'] * 0.2)
        offset_y = random.uniform(-box['height'] * 0.2, box['height'] * 0.2)
        target_x = box['x'] + box['width'] / 2 + offset_x
        target_y = box['y'] + box['height'] / 2 + offset_y
        
        if move_to_element:
            await cls.move_mouse(page, target_x, target_y)
        
        # Pre-click delay
        await cls.random_delay(cls.CLICK_DELAY_MIN, cls.CLICK_DELAY_MAX)
        
        # Click with variable button press duration
        await page.mouse.down()
        await cls.random_delay(50, 100)  # Hold button
        await page.mouse.up()
        
        # Post-click delay
        await cls.random_delay(cls.ACTION_DELAY_MIN, cls.ACTION_DELAY_MAX)
    
    @classmethod
    async def human_type(
        cls, 
        page, 
        selector: str, 
        text: str,
        typo_probability: float = 0.02
    ) -> None:
        """
        Type text with human-like timing and occasional typos
        """
        await page.click(selector)
        await cls.random_delay(200, 400)
        
        for char in text:
            # Occasional typo
            if random.random() < typo_probability:
                wrong_char = chr(ord(char) + random.choice([-1, 1]))
                await page.keyboard.type(wrong_char)
                await cls.random_delay(100, 200)
                await page.keyboard.press('Backspace')
                await cls.random_delay(50, 150)
            
            await page.keyboard.type(char)
            
            # Variable typing speed
            if char == ' ':
                await cls.random_delay(100, 200)  # Pause after words
            else:
                await cls.random_delay(cls.TYPING_DELAY_MIN, cls.TYPING_DELAY_MAX)
    
    @classmethod
    async def human_scroll(
        cls, 
        page, 
        direction: str = 'down',
        distance: int = 300,
        smooth: bool = True
    ) -> None:
        """
        Perform human-like scrolling with momentum
        """
        scroll_distance = distance * (1 if direction == 'down' else -1)
        
        if smooth:
            # Smooth scroll in chunks
            chunks = random.randint(3, 6)
            chunk_size = scroll_distance / chunks
            
            for _ in range(chunks):
                await page.mouse.wheel(0, chunk_size)
                await cls.random_delay(cls.SCROLL_DELAY_MIN, cls.SCROLL_DELAY_MAX)
        else:
            await page.mouse.wheel(0, scroll_distance)
        
        # Reading pause after scroll
        await cls.random_delay(cls.READ_DELAY_MIN, cls.READ_DELAY_MAX)
    
    @classmethod
    async def wait_for_page_load(cls, page, extra_wait: bool = True) -> None:
        """Wait for page load with human-like patience"""
        await page.wait_for_load_state('networkidle', timeout=30000)
        
        if extra_wait:
            # Humans don't act instantly when page loads
            await cls.human_delay(1500, 0.4)
    
    @classmethod
    async def simulate_reading(cls, duration_ms: int = 3000) -> None:
        """Simulate time spent reading content"""
        variance = random.uniform(0.7, 1.3)
        actual_duration = duration_ms * variance
        await asyncio.sleep(actual_duration / 1000)
    
    @classmethod
    async def random_mouse_movement(cls, page) -> None:
        """Perform random idle mouse movements (simulates reading/thinking)"""
        num_movements = random.randint(1, 3)
        
        for _ in range(num_movements):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y, steps=random.randint(5, 15))
            await cls.random_delay(200, 500)
