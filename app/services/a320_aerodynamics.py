import numpy as np
from scipy import interpolate
import json
import math

class A320WingAerodynamics:
    
    def __init__(self):
        # Physical constants
        self.AIR_DENSITY_SEA_LEVEL = 1.225  # kg/m³
        self.SPEED_OF_SOUND = 340.3  # m/s at sea level
        
        # A320 wing specifications based on actual aircraft data
        self.WING_SPAN = 35.8  # meters (with winglets)
        self.WING_AREA = 122.6  # m²
        self.MEAN_CHORD = 4.29  # meters
        self.ASPECT_RATIO = 9.39  # Span²/Area
        self.TAPER_RATIO = 0.21  # Tip chord / Root chord
        self.SWEEP_ANGLE = 25.0  # degrees, at quarter-chord
        self.THICKNESS_RATIO = 0.115  # 11.5% thickness-to-chord ratio
        self.DIHEDRAL_ANGLE = 5.0  # degrees
        
        # A320 high-lift system specifications
        # Real A320 flap/slat positions and angles based on research
        self.flap_configs = {
            "UP": {"angle": 0, "extension": 0},
            "1": {"angle": 10, "extension": 0.02},  # 10° flap deflection with 2% chord extension
            "2": {"angle": 15, "extension": 0.035},  # 15° flap deflection with 3.5% chord extension
            "3": {"angle": 20, "extension": 0.05},   # 20° flap deflection with 5% chord extension
            "FULL": {"angle": 35, "extension": 0.08} # 35° flap deflection with 8% chord extension
        }
        
        self.slat_configs = {
            "UP": {"extension": 0, "angle": 0},
            "MID": {"extension": 18, "angle": 13},    # S position (18% extension)
            "1": {"extension": 22, "angle": 16},      # 22% extension of chord length
            "2": {"extension": 24, "angle": 18},      # 24% extension of chord length
            "3": {"extension": 27, "angle": 20}       # 27% extension of chord length
        }
        
        # Initialize simulation state
        self.state = {
            "angle_of_attack": 2.0,
            "airspeed": 250.0,
            "altitude": 0.0,
            "flap_setting": "UP",
            "flap_angle": 0.0,
            "flap_extension": 0.0,
            "slat_setting": "UP",
            "slat_extension": 0.0,
            "slat_angle": 0.0,
            "spoiler_deflection": 0.0
        }
        
        # Initialize results
        self.results = {
            "mach_number": 0.0,
            "reynolds_number": 0.0,
            "dynamic_pressure": 0.0,
            "lift_coefficient": 0.0,
            "drag_coefficient": 0.0,
            "moment_coefficient": 0.0,
            "lift": 0.0,
            "drag": 0.0,
            "pitching_moment": 0.0,
            "airfoil_coordinates": {
                "main_wing": [],
                "flap": [],
                "slat": []
            },
            "pressure_distribution": [],
            "stall_warning": False,
            "buffet_warning": False
        }
        
        # A320 supercritical airfoil coordinates
        # These are approximate based on publicly available data
        # Real coordinates would be proprietary to Airbus
        self._initialize_airfoil_data()
    
    def _initialize_airfoil_data(self):
        """Initialize the A320 supercritical airfoil coordinate data"""
        # Base coordinates for A320-like supercritical airfoil
        # Upper surface coordinates (x, y)
        self.upper_surface = np.array([
            [0.00000, 0.00000],
            [0.00500, 0.01159],
            [0.01250, 0.01796],
            [0.02500, 0.02485],
            [0.05000, 0.03488],
            [0.10000, 0.04856],
            [0.15000, 0.05687],
            [0.20000, 0.06271],
            [0.25000, 0.06654],
            [0.30000, 0.06859],
            [0.35000, 0.06903],
            [0.40000, 0.06800],
            [0.45000, 0.06562],
            [0.50000, 0.06210],
            [0.55000, 0.05762],
            [0.60000, 0.05220],
            [0.65000, 0.04600],
            [0.70000, 0.03900],
            [0.75000, 0.03155],
            [0.80000, 0.02380],
            [0.85000, 0.01620],
            [0.90000, 0.00920],
            [0.95000, 0.00350],
            [1.00000, 0.00000]
        ])
        
        # Lower surface coordinates (x, y)
        self.lower_surface = np.array([
            [0.00000, 0.00000],
            [0.00500, -0.00950],
            [0.01250, -0.01480],
            [0.02500, -0.02050],
            [0.05000, -0.02800],
            [0.10000, -0.03715],
            [0.15000, -0.04300],
            [0.20000, -0.04705],
            [0.25000, -0.04970],
            [0.30000, -0.05110],
            [0.35000, -0.05140],
            [0.40000, -0.05060],
            [0.45000, -0.04870],
            [0.50000, -0.04580],
            [0.55000, -0.04200],
            [0.60000, -0.03750],
            [0.65000, -0.03250],
            [0.70000, -0.02720],
            [0.75000, -0.02180],
            [0.80000, -0.01650],
            [0.85000, -0.01150],
            [0.90000, -0.00680],
            [0.95000, -0.00270],
            [1.00000, 0.00000]
        ])
        
        # Create interpolation functions for the airfoil surfaces
        self.upper_interp = interpolate.interp1d(
            self.upper_surface[:, 0], 
            self.upper_surface[:, 1], 
            kind='cubic',
            bounds_error=False,
            fill_value=(self.upper_surface[0, 1], self.upper_surface[-1, 1])
        )
        
        self.lower_interp = interpolate.interp1d(
            self.lower_surface[:, 0], 
            self.lower_surface[:, 1], 
            kind='cubic',
            bounds_error=False,
            fill_value=(self.lower_surface[0, 1], self.lower_surface[-1, 1])
        )
    
    def update_settings(self, settings):
        """Update simulation settings from client inputs"""
        for key, value in settings.items():
            if key in self.state:
                self.state[key] = value
        
        # Handle configuration settings
        if "flap_setting" in settings:
            flap_config = self.flap_configs.get(settings["flap_setting"], {"angle": 0, "extension": 0})
            self.state["flap_angle"] = flap_config["angle"]
            self.state["flap_extension"] = flap_config["extension"]
        
        if "slat_setting" in settings:
            slat_config = self.slat_configs.get(settings["slat_setting"], {"extension": 0, "angle": 0})
            self.state["slat_extension"] = slat_config["extension"] / 100.0  # Convert percentage to decimal
            self.state["slat_angle"] = slat_config["angle"]
        
        # Compute new aerodynamic results based on updated settings
        self._compute_simulation()
        
        return self.get_simulation_data()
    
    def _generate_airfoil_coordinates(self, num_points=100):
        """
        Generate airfoil coordinates for the current state.
        Includes main wing, flap, and slat positions.
        """
        # Clear previous coordinates
        self.results["airfoil_coordinates"]["main_wing"] = []
        self.results["airfoil_coordinates"]["flap"] = []
        self.results["airfoil_coordinates"]["slat"] = []
        
        # Generate x positions with higher density near leading and trailing edges
        beta = np.linspace(0, np.pi, num_points)
        x = (1 - np.cos(beta)) / 2
        
        # Main wing coordinates (excluding flap and slat regions)
        flap_start = 0.7  # Position where flap starts (assuming 70% of chord)
        slat_end = 0.15   # Position where slat ends (assuming 15% of chord)
        
        # Generate main wing section
        for i in range(num_points):
            if x[i] > slat_end and x[i] < flap_start:
                y_upper = float(self.upper_interp(x[i]))
                y_lower = float(self.lower_interp(x[i]))
                
                self.results["airfoil_coordinates"]["main_wing"].append({
                    "x": float(x[i]),
                    "y_upper": y_upper,
                    "y_lower": y_lower
                })
        
        # Generate slat coordinates if extended
        if self.state["slat_extension"] > 0:
            slat_angle_rad = np.radians(self.state["slat_angle"])
            slat_extension = self.state["slat_extension"]
            
            for i in range(num_points):
                if x[i] <= slat_end:
                    # Original coordinates
                    y_upper = float(self.upper_interp(x[i]))
                    y_lower = float(self.lower_interp(x[i]))
                    
                    # Apply slat extension and rotation
                    slat_x = x[i] - slat_extension * (1 - x[i]/slat_end)
                    slat_y_upper = y_upper - slat_extension * 0.05
                    slat_y_lower = y_lower - slat_extension * 0.05
                    
                    # Rotate around leading edge for slat angle
                    if x[i] > 0:  # Avoid singularity at x=0
                        dx = slat_x
                        dy_upper = slat_y_upper
                        dy_lower = slat_y_lower
                        
                        slat_x = dx * np.cos(slat_angle_rad) - dy_upper * np.sin(slat_angle_rad)
                        slat_y_upper = dx * np.sin(slat_angle_rad) + dy_upper * np.cos(slat_angle_rad)
                        slat_y_lower = dx * np.sin(slat_angle_rad) + dy_lower * np.cos(slat_angle_rad)
                    
                    self.results["airfoil_coordinates"]["slat"].append({
                        "x": float(slat_x),
                        "y_upper": float(slat_y_upper),
                        "y_lower": float(slat_y_lower)
                    })
        
        # Generate flap coordinates if extended
        if self.state["flap_angle"] > 0:
            flap_angle_rad = np.radians(self.state["flap_angle"])
            flap_extension = self.state["flap_extension"]
            
            for i in range(num_points):
                if x[i] >= flap_start:
                    # Original coordinates
                    y_upper = float(self.upper_interp(x[i]))
                    y_lower = float(self.lower_interp(x[i]))
                    
                    # Calculate position relative to flap hinge
                    rel_x = x[i] - flap_start
                    rel_y_upper = y_upper
                    rel_y_lower = y_lower
                    
                    # Apply translation for fowler motion
                    flap_x = flap_start + rel_x + flap_extension
                    flap_y_upper = rel_y_upper - flap_extension * 0.1
                    flap_y_lower = rel_y_lower - flap_extension * 0.1
                    
                    # Rotate around hinge point
                    dx = flap_x - flap_start
                    dy_upper = flap_y_upper - self.upper_interp(flap_start)
                    dy_lower = flap_y_lower - self.lower_interp(flap_start)
                    
                    rotated_x = flap_start + dx * np.cos(flap_angle_rad) + dy_upper * np.sin(flap_angle_rad)
                    rotated_y_upper = self.upper_interp(flap_start) - dx * np.sin(flap_angle_rad) + dy_upper * np.cos(flap_angle_rad)
                    rotated_y_lower = self.lower_interp(flap_start) - dx * np.sin(flap_angle_rad) + dy_lower * np.cos(flap_angle_rad)
                    
                    self.results["airfoil_coordinates"]["flap"].append({
                        "x": float(rotated_x),
                        "y_upper": float(rotated_y_upper),
                        "y_lower": float(rotated_y_lower)
                    })
    
    def _calculate_flow_conditions(self):
        """Calculate basic flow conditions for the current state"""
        # Atmospheric properties calculation
        altitude = self.state["altitude"]
        if altitude <= 11000:  # Troposphere
            temperature = 288.15 - 0.00649 * altitude
            pressure = 101325 * (temperature / 288.15) ** 5.255876
        else:  # Stratosphere
            temperature = 216.65
            pressure = 22632.1 * np.exp(-0.00015769 * (altitude - 11000))
        
        density = pressure / (287.05 * temperature)
        airspeed = self.state["airspeed"]
        
        # Calculate Mach number
        speed_of_sound = np.sqrt(1.4 * 287.05 * temperature)
        mach_number = airspeed / speed_of_sound
        
        # Calculate Reynolds number
        dynamic_viscosity = 1.458e-6 * temperature ** 1.5 / (temperature + 110.4)
        reynolds_number = density * airspeed * self.MEAN_CHORD / dynamic_viscosity
        
        # Calculate dynamic pressure (q)
        dynamic_pressure = 0.5 * density * airspeed ** 2
        
        # Save to results
        self.results["mach_number"] = mach_number
        self.results["reynolds_number"] = reynolds_number
        self.results["dynamic_pressure"] = dynamic_pressure
        
        return {
            "temperature": temperature,
            "pressure": pressure,
            "density": density,
            "speed_of_sound": speed_of_sound,
            "mach_number": mach_number,
            "reynolds_number": reynolds_number,
            "dynamic_pressure": dynamic_pressure
        }
    
    def _calculate_aerodynamic_coefficients(self, flow_conditions):
        """
        Calculate wing aerodynamic coefficients.
        Uses empirical and analytical methods to estimate lift, drag, and moment coefficients.
        """
        # Extract flow and state parameters
        aoa = self.state["angle_of_attack"]
        mach = flow_conditions["mach_number"]
        reynolds = flow_conditions["reynolds_number"]
        q = flow_conditions["dynamic_pressure"]
        
        # Basic airfoil lift characteristics
        # Base lift coefficient for supercritical airfoil
        cl_alpha_base = 6.2  # per radian (approximately 0.108 per degree)
        cl0 = 0.2  # Zero-AoA lift coefficient
        aoa_rad = np.radians(aoa)
        
        # Calculate base 2D airfoil lift coefficient
        cl_airfoil = cl0 + cl_alpha_base * aoa_rad
        
        # 3D wing effects - lift coefficient correction
        # Finite wing correction using aspect ratio
        e = 0.85  # Oswald efficiency factor
        ar = self.ASPECT_RATIO
        cl_alpha_3d = cl_alpha_base / (1 + cl_alpha_base/(np.pi * e * ar))
        
        # Calculate wing lift coefficient with 3D corrections
        cl_wing = cl0 + cl_alpha_3d * aoa_rad
        
        # Compressibility correction using Prandtl-Glauert rule
        if mach < 0.8:
            cl_wing = cl_wing / np.sqrt(1 - mach**2)
        
        # Angle of attack corrections for compressibility
        if mach > 0.7:
            beta = np.sqrt(1 - mach**2)
            cl_wing = cl_wing * beta
        
        # High-lift devices contribution
        
        # Slat effect - based on slat position
        if self.state["slat_setting"] != "UP":
            # Slat increases maximum lift coefficient
            slat_extension_percent = self.state["slat_extension"] * 100
            # Roughly 0.2 increase in cl per 10% slat extension
            slat_cl_increment = 0.02 * slat_extension_percent
            cl_wing += slat_cl_increment
            
            # Slat also increases stall angle, but we don't model that here
        
        # Flap effect - based on flap angle
        if self.state["flap_setting"] != "UP":
            # Simplified flap effectiveness
            flap_angle = self.state["flap_angle"]
            flap_chord_ratio = 0.3  # Assumes flap is 30% of chord
            
            # Flap effectiveness parameter
            flap_effectiveness = 0.6  # Typical for slotted flaps
            
            # Flap contribution to lift (delta_cl)
            # Formula: delta_cl = 2*pi*effectiveness*flap_chord_ratio*sin(flap_angle)
            delta_cl_flap = 2 * np.pi * flap_effectiveness * flap_chord_ratio * np.sin(np.radians(flap_angle))
            cl_wing += delta_cl_flap
        
        # Spoiler effect - reduces lift
        if self.state["spoiler_deflection"] > 0:
            spoiler_deflection = self.state["spoiler_deflection"]
            # Spoiler effectiveness depends on position and angle
            spoiler_effectiveness = 0.01  # per degree of deflection
            cl_wing -= spoiler_deflection * spoiler_effectiveness
        
        # Calculate Drag Coefficient
        
        # Profile drag coefficient - using quadratic fit based on AoA
        cd_profile = 0.008 + 0.006 * aoa_rad**2
        
        # Induced drag coefficient
        cd_induced = cl_wing**2 / (np.pi * ar * e)
        
        # Wave drag for transonic flow
        cd_wave = 0
        if mach > 0.7:
            # Simple model for wave drag
            mach_crit = 0.72  # Critical Mach number for supercritical airfoil
            if mach > mach_crit:
                cd_wave = 0.1 * (mach - mach_crit)**4
        
        # High-lift device drag
        cd_slat = 0
        if self.state["slat_setting"] != "UP":
            cd_slat = 0.005 * self.state["slat_extension"] * 100
        
        cd_flap = 0
        if self.state["flap_setting"] != "UP":
            cd_flap = 0.01 * self.state["flap_angle"] / 10
        
        cd_spoiler = 0
        if self.state["spoiler_deflection"] > 0:
            cd_spoiler = 0.01 * self.state["spoiler_deflection"] / 10
        
        # Total drag coefficient
        cd_total = cd_profile + cd_induced + cd_wave + cd_slat + cd_flap + cd_spoiler
        
        # Moment coefficient (simplified model)
        cm_airfoil = -0.1  # Typical value for supercritical airfoils
        cm_wing = cm_airfoil
        
        # Flap effect on moment
        if self.state["flap_setting"] != "UP":
            flap_angle = self.state["flap_angle"]
            # Flap increases nose-down pitching moment
            cm_wing -= 0.01 * flap_angle / 10
        
        # Stall detection
        aoa_stall = 12.0  # Base stall AoA in degrees
        if self.state["slat_setting"] != "UP":
            # Slats increase stall angle
            aoa_stall += 3.0
        if self.state["flap_setting"] != "UP":
            # Flaps slightly reduce stall angle
            aoa_stall -= 1.0
        
        self.results["stall_warning"] = (aoa > 0.85 * aoa_stall)
        
        # Buffet detection for transonic flow
        buffet_cl_limit = 0.8 - 0.4 * (mach - 0.4) if mach > 0.4 else 0.8
        self.results["buffet_warning"] = (cl_wing > buffet_cl_limit and mach > 0.7)
        
        # Calculate forces and moments
        self.results["lift_coefficient"] = cl_wing
        self.results["drag_coefficient"] = cd_total
        self.results["moment_coefficient"] = cm_wing
        
        # Calculate actual forces and moment
        self.results["lift"] = cl_wing * q * self.WING_AREA
        self.results["drag"] = cd_total * q * self.WING_AREA
        self.results["pitching_moment"] = cm_wing * q * self.WING_AREA * self.MEAN_CHORD
    
    def _generate_pressure_distribution(self):
        """
        Generate pressure coefficient distribution around the airfoil.
        This is a simplified model - real CFD would provide more accurate results.
        """
        # Extract parameters
        aoa_rad = np.radians(self.state["angle_of_attack"])
        cl = self.results["lift_coefficient"]
        mach = self.results["mach_number"]
        
        # Generate x positions
        num_points = 100
        x = np.linspace(0, 1, num_points)
        
        # Initialize pressure arrays
        cp_upper = np.zeros(num_points)
        cp_lower = np.zeros(num_points)
        
        # Simplified pressure model for A320 supercritical airfoil
        # This is based on typical pressure distributions of supercritical airfoils
        
        # Upper surface pressure distribution
        for i, xi in enumerate(x):
            # Leading edge suction peak
            if xi < 0.05:
                cp_upper[i] = -5.0 * (xi / 0.05) + 1.0
            # Flat pressure region characteristic of supercritical airfoils
            elif xi < 0.6:
                cp_upper[i] = -1.0 - 0.2 * xi - 0.8 * cl * (1 - xi/0.6)
            # Pressure recovery region
            else:
                cp_upper[i] = -1.2 + 1.2 * ((xi - 0.6) / 0.4)
        
        # Apply AoA effect to upper surface
        cp_upper -= 2.0 * aoa_rad * (1.0 - x)
        
        # Lower surface pressure distribution
        for i, xi in enumerate(x):
            if xi < 0.1:
                cp_lower[i] = 1.0 - 8.0 * xi
            else:
                cp_lower[i] = 0.5 - 0.5 * xi
        
        # Apply AoA effect to lower surface
        cp_lower += 1.0 * aoa_rad * (1.0 - x)
        
        # Transonic effects - shock formation
        if mach > 0.7:
            # Position shock wave on upper surface based on Mach number
            shock_pos = 0.35 + 0.25 * (mach - 0.7) / 0.3
            shock_width = 0.05
            
            for i, xi in enumerate(x):
                # Add shock effect to upper surface
                if xi > shock_pos - shock_width and xi < shock_pos + shock_width:
                    # Create pressure jump at shock location
                    shock_strength = 2.0 * (mach - 0.7) / 0.3
                    dist_to_shock = abs(xi - shock_pos)
                    if xi < shock_pos:
                        # Before shock - lower pressure
                        cp_upper[i] -= shock_strength * (1.0 - dist_to_shock/shock_width)
                    else:
                        # After shock - pressure rise
                        cp_upper[i] += shock_strength * (1.0 - dist_to_shock/shock_width)
        
        # Apply high-lift device effects
        
        # Slat effect
        if self.state["slat_setting"] != "UP":
            slat_extension = self.state["slat_extension"]
            for i, xi in enumerate(x):
                if xi < 0.15:  # Slat region
                    # Slats reduce suction peak and distribute pressure more evenly
                    cp_upper[i] *= 0.8
                    cp_upper[i] -= 0.5 * slat_extension * (1.0 - xi/0.15)
                    cp_lower[i] *= 0.9
        
        # Flap effect
        if self.state["flap_setting"] != "UP":
            flap_angle = self.state["flap_angle"]
            flap_effect = flap_angle / 40.0  # Normalize to range 0-1
            for i, xi in enumerate(x):
                if xi > 0.7:  # Flap region
                    # Flaps increase pressure differential on rear portion
                    cp_upper[i] -= 1.0 * flap_effect * ((xi - 0.7) / 0.3)
                    cp_lower[i] += 0.5 * flap_effect * ((xi - 0.7) / 0.3)
        
        # Store results
        self.results["pressure_distribution"] = []
        for i, xi in enumerate(x):
            self.results["pressure_distribution"].append({
                "x": float(xi),
                "cp_upper": float(cp_upper[i]),
                "cp_lower": float(cp_lower[i])
            })
    
    def _compute_simulation(self):
        """Run the full simulation"""
        # Generate airfoil and high-lift device shapes
        self._generate_airfoil_coordinates()
        
        # Calculate flow conditions
        flow_conditions = self._calculate_flow_conditions()
        
        # Calculate aerodynamic coefficients
        self._calculate_aerodynamic_coefficients(flow_conditions)
        
        # Generate pressure distribution
        self._generate_pressure_distribution()
    
    def get_simulation_data(self):
        """Return current simulation data for visualization"""
        return {
            "state": self.state,
            "results": self.results
        }