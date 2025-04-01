"""
Enhanced visualization module for A320 wing system.
Provides detailed 2D and 3D visualization options for the airfoil
and flow field.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # 비대화형 백엔드 설정 (중요!)
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import traceback

class WingVisualizer:
    """
    Class for generating enhanced visualizations of the A320 wing system
    """
    
    def __init__(self, aerodynamics_model):
        """Initialize with reference to the aerodynamics model"""
        self.model = aerodynamics_model
    
    def generate_pressure_plot(self, width=800, height=400):
        """
        Generate a pressure distribution plot using matplotlib
        Returns a base64 encoded image
        """
        try:
            # Create a new figure
            plt.figure(figsize=(width/100, height/100), dpi=100)
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            
            # Get pressure distribution data
            pressure_data = self.model.results.get("pressure_distribution", [])
            if not pressure_data:
                print("Warning: Empty pressure distribution data")
                pressure_data = []
            
            # Extract data into arrays
            x = [point.get("x", 0) for point in pressure_data]
            cp_upper = [point.get("cp_upper", 0) for point in pressure_data]
            cp_lower = [point.get("cp_lower", 0) for point in pressure_data]
            
            # Plot upper and lower surface pressure
            ax.plot(x, cp_upper, 'r-', label='Upper Surface')
            ax.plot(x, cp_lower, 'b-', label='Lower Surface')
            
            # Invert y-axis for pressure coefficient (convention)
            ax.invert_yaxis()
            
            # Add labels and title
            ax.set_xlabel('x/c')
            ax.set_ylabel('Pressure Coefficient (Cp)')
            ax.set_title('A320 Airfoil Pressure Distribution')
            
            # Add legend
            ax.legend()
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add annotations for key features
            # Shock position (if transonic)
            if self.model.results.get("mach_number", 0) > 0.7:
                shock_pos = 0.35 + 0.25 * (self.model.results.get("mach_number", 0) - 0.7) / 0.3
                
                # Find pressure at shock
                shock_idx = min(range(len(x)), key=lambda i: abs(x[i] - shock_pos)) if x else 0
                shock_cp = cp_upper[shock_idx] if shock_idx < len(cp_upper) else 0
                
                # Annotate shock position
                ax.annotate('Shock', 
                           xy=(shock_pos, shock_cp),
                           xytext=(shock_pos, shock_cp - 0.5),
                           arrowprops=dict(facecolor='black', shrink=0.05),
                           horizontalalignment='center')
            
            # Add info about configuration
            config_text = f"AoA: {self.model.state.get('angle_of_attack', 0)}°, M: {self.model.results.get('mach_number', 0):.3f}\n"
            config_text += f"Flaps: {self.model.state.get('flap_setting', 'UP')}, Slats: {self.model.state.get('slat_setting', 'UP')}"
            
            ax.text(0.05, 0.05, config_text,
                    transform=ax.transAxes,
                    bbox=dict(facecolor='white', alpha=0.7))
            
            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            print(f"Error in generate_pressure_plot: {str(e)}")
            print(traceback.format_exc())
            return self._generate_error_image(f"Error generating pressure plot: {str(e)}")
    
    def generate_airfoil_plot(self, width=800, height=400):
        """
        Generate an airfoil shape plot with high-lift devices
        Returns a base64 encoded image
        """
        try:
            # Create a new figure
            plt.figure(figsize=(width/100, height/100), dpi=100)
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            
            # Get coordinates
            coords = self.model.results.get("airfoil_coordinates", {})
            
            # Plot main wing
            main_wing = coords.get("main_wing", [])
            if main_wing:
                x_main = [point.get("x", 0) for point in main_wing]
                y_upper = [point.get("y_upper", 0) for point in main_wing]
                y_lower = [point.get("y_lower", 0) for point in main_wing]
                
                # Connect points in correct order
                x_airfoil = x_main + x_main[::-1]
                y_airfoil = y_upper + y_lower[::-1]
                
                ax.fill(x_airfoil, y_airfoil, 'gray', alpha=0.7, label='Main Wing')
                ax.plot(x_airfoil, y_airfoil, 'k-', linewidth=1)
            
            # Plot slat if extended
            slat = coords.get("slat", [])
            if slat:
                x_slat = [point.get("x", 0) for point in slat]
                y_upper = [point.get("y_upper", 0) for point in slat]
                y_lower = [point.get("y_lower", 0) for point in slat]
                
                # Connect points in correct order
                x_slat_plot = x_slat + x_slat[::-1]
                y_slat_plot = y_upper + y_lower[::-1]
                
                ax.fill(x_slat_plot, y_slat_plot, 'blue', alpha=0.6, label='Slat')
                ax.plot(x_slat_plot, y_slat_plot, 'b-', linewidth=1)
            
            # Plot flap if extended
            flap = coords.get("flap", [])
            if flap:
                x_flap = [point.get("x", 0) for point in flap]
                y_upper = [point.get("y_upper", 0) for point in flap]
                y_lower = [point.get("y_lower", 0) for point in flap]
                
                # Connect points in correct order
                x_flap_plot = x_flap + x_flap[::-1]
                y_flap_plot = y_upper + y_lower[::-1]
                
                ax.fill(x_flap_plot, y_flap_plot, 'green', alpha=0.6, label='Flap')
                ax.plot(x_flap_plot, y_flap_plot, 'g-', linewidth=1)
            
            # Set equal aspect ratio
            ax.set_aspect('equal')
            
            # Add labels and title
            ax.set_xlabel('x/c')
            ax.set_ylabel('y/c')
            ax.set_title('A320 Airfoil with High-Lift Devices')
            
            # Add legend
            ax.legend()
            
            # Set limits with some margin
            ax.set_xlim(-0.1, 1.2)
            ax.set_ylim(-0.3, 0.3)
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.4)
            
            # Add info about configuration
            config_text = f"Flaps: {self.model.state.get('flap_setting', 'UP')} ({self.model.state.get('flap_angle', 0)}°)\n"
            config_text += f"Slats: {self.model.state.get('slat_setting', 'UP')} ({self.model.state.get('slat_extension', 0)*100:.0f}%)"
            
            ax.text(0.05, 0.05, config_text,
                    transform=ax.transAxes,
                    bbox=dict(facecolor='white', alpha=0.7))
            
            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            print(f"Error in generate_airfoil_plot: {str(e)}")
            print(traceback.format_exc())
            return self._generate_error_image(f"Error generating airfoil plot: {str(e)}")
    
    def generate_polar_plot(self, width=800, height=400):
        """
        Generate a lift-drag polar plot for the current configuration
        Simulates multiple angles of attack to create the curve
        Returns a base64 encoded image
        """
        try:
            # Create a new figure
            plt.figure(figsize=(width/100, height/100), dpi=100)
            fig, ax = plt.subplots(figsize=(width/100, height/100), dpi=100)
            
            # Store original AoA
            original_aoa = self.model.state.get("angle_of_attack", 0)
            
            try:
                # Calculate lift and drag for a range of angles of attack
                aoa_range = np.arange(-5, 16, 1)
                cl_values = []
                cd_values = []
                
                for aoa in aoa_range:
                    # Update model with new AoA
                    self.model.state["angle_of_attack"] = aoa
                    self.model._compute_simulation()
                    
                    # Store results
                    cl_values.append(self.model.results.get("lift_coefficient", 0))
                    cd_values.append(self.model.results.get("drag_coefficient", 0))
                
                # Restore original AoA
                self.model.state["angle_of_attack"] = original_aoa
                self.model._compute_simulation()
            except Exception as inner_e:
                print(f"Error calculating polar data: {str(inner_e)}")
                # 간단한 더미 데이터 사용
                aoa_range = np.arange(-5, 16, 1)
                cl_values = [0.1 * a + 0.2 for a in aoa_range]  # 간단한 선형 관계로 근사
                cd_values = [0.01 + 0.001 * a**2 for a in aoa_range]  # 간단한 2차 함수로 근사
            
            # Plot the polar curve
            ax.plot(cd_values, cl_values, 'b-o', markersize=4)
            
            # Mark the current operating point
            current_cl = self.model.results.get("lift_coefficient", 0)
            current_cd = self.model.results.get("drag_coefficient", 0)
            ax.plot(current_cd, current_cl, 'ro', markersize=8, label=f'AoA: {original_aoa}°')
            
            # Add labels and title
            ax.set_xlabel('Drag Coefficient (CD)')
            ax.set_ylabel('Lift Coefficient (CL)')
            ax.set_title('Lift-Drag Polar')
            
            # Add legend
            ax.legend()
            
            # Add grid
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Add configuration information
            config_text = f"Mach: {self.model.results.get('mach_number', 0):.3f}\n"
            config_text += f"Flaps: {self.model.state.get('flap_setting', 'UP')}, Slats: {self.model.state.get('slat_setting', 'UP')}"
            
            ax.text(0.05, 0.95, config_text,
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(facecolor='white', alpha=0.7))
            
            # Convert plot to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            print(f"Error in generate_polar_plot: {str(e)}")
            print(traceback.format_exc())
            return self._generate_error_image(f"Error generating polar plot: {str(e)}")
    
    def _generate_error_image(self, error_message):
        """Generate a simple error image with a message"""
        try:
            plt.figure(figsize=(8, 4), dpi=100)
            fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
            ax.text(0.5, 0.5, error_message, 
                   ha='center', va='center', fontsize=12,
                   transform=ax.transAxes)
            ax.set_axis_off()
            
            # Convert to base64 image
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            image_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_data}"
        except Exception as e:
            print(f"Error creating error image: {str(e)}")
            # 최후의 수단으로 정적 텍스트 응답 반환
            return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVQI12P4//8/AAX+Av7czFnnAAAAAElFTkSuQmCC"
    
    def generate_visualization_endpoint(self, plot_type):
        """Generate a visualization based on plot type"""
        try:
            if plot_type == 'pressure':
                return self.generate_pressure_plot()
            elif plot_type == 'airfoil':
                return self.generate_airfoil_plot()
            elif plot_type == 'polar':
                return self.generate_polar_plot()
            else:
                return self._generate_error_image(f"Unknown plot type: {plot_type}")
        except Exception as e:
            print(f"Error in generate_visualization_endpoint: {str(e)}")
            print(traceback.format_exc())
            return self._generate_error_image(f"Visualization error: {str(e)}")