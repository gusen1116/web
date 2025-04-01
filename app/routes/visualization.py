"""
Extended Flask routes for A320 visualization
Adds endpoints for advanced matplotlib visualizations
"""

from flask import Blueprint, render_template, jsonify, request, Response, current_app, send_file
import os
import io
import base64
import traceback
from app.services.a320_aerodynamics import A320WingAerodynamics
from app.services.wing_visualizer import WingVisualizer
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 비대화형 백엔드 설정
import matplotlib.pyplot as plt

# Create global instances for visualization
try:
    simulation_instance = A320WingAerodynamics()
    visualizer = WingVisualizer(simulation_instance)
except Exception as e:
    print(f"Error initializing visualization components: {str(e)}")
    print(traceback.format_exc())
    # 에러 발생해도 초기화는 계속 진행
    simulation_instance = None
    visualizer = None

# Create blueprint
visualization_bp = Blueprint('visualization', __name__, url_prefix='/visualization')

@visualization_bp.route('/a320/<plot_type>')
def get_visualization(plot_type):
    """
    Generate and return a visualization as an image
    
    Args:
        plot_type: Type of plot to generate ('pressure', 'airfoil', 'polar')
    
    Returns:
        HTTP response with the image data
    """
    try:
        # 디버깅 로그 추가
        current_app.logger.debug(f"Visualization request: {plot_type}")
        
        if simulation_instance is None or visualizer is None:
            return create_error_image(f"Visualization components not initialized"), 200
        
        # 유효한 plot_type 확인
        if plot_type not in ["pressure", "airfoil", "polar"]:
            return create_error_image(f"Invalid plot type: {plot_type}"), 200
        
        # Optional parameters with default values
        aoa = request.args.get('aoa', type=float, default=2.0)
        mach = request.args.get('mach', type=float, default=0.78)
        flap_setting = request.args.get('flap', type=str, default="2")
        slat_setting = request.args.get('slat', type=str, default="2")
        
        # 모든 파라미터 로깅
        current_app.logger.debug(f"Parameters: aoa={aoa}, mach={mach}, flap={flap_setting}, slat={slat_setting}")
        
        # Update simulation parameters if provided
        simulation_instance.state["angle_of_attack"] = aoa
        
        # Convert Mach to airspeed
        simulation_instance.state["airspeed"] = mach * 340.3
        
        # Update flap and slat settings
        try:
            simulation_instance.update_settings({"flap_setting": flap_setting})
            simulation_instance.update_settings({"slat_setting": slat_setting})
        except Exception as e:
            current_app.logger.error(f"Error updating settings: {str(e)}")
            return create_error_image(f"Failed to update simulation settings: {str(e)}"), 200
        
        # Recompute simulation with updated parameters
        try:
            simulation_instance._compute_simulation()
        except Exception as e:
            current_app.logger.error(f"Simulation computation error: {str(e)}")
            return create_error_image(f"Simulation computation failed: {str(e)}"), 200
        
        # Generate the visualization
        try:
            image_data = visualizer.generate_visualization_endpoint(plot_type)
        except Exception as e:
            current_app.logger.error(f"Visualization generation error: {str(e)}")
            return create_error_image(f"Visualization generation failed: {str(e)}"), 200
        
        if image_data:
            try:
                # Parse the data URL
                header, encoded = image_data.split(",", 1)
                data = base64.b64decode(encoded)
                
                # Return as an image
                return Response(data, mimetype='image/png')
            except Exception as e:
                current_app.logger.error(f"Image encoding error: {str(e)}")
                return create_error_image(f"Image encoding failed: {str(e)}"), 200
        else:
            return create_error_image("Empty visualization data"), 200
            
    except Exception as e:
        # 모든 예외 잡기
        current_app.logger.error(f"Uncaught exception in visualization endpoint: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return create_error_image(f"Internal server error: {str(e)}"), 200

@visualization_bp.route('/a320/data')
def get_visualization_data():
    """
    Return JSON data with all visualization URLs for embedding
    """
    try:
        # 디버깅 로그 추가
        current_app.logger.debug("Data API request received")
        
        if simulation_instance is None:
            return jsonify(create_dummy_data()), 200
        
        # Optional parameters with default values
        aoa = request.args.get('aoa', type=float, default=2.0)
        mach = request.args.get('mach', type=float, default=0.78)
        flap_setting = request.args.get('flap', type=str, default="2")
        slat_setting = request.args.get('slat', type=str, default="2")
        
        # 디버깅 로그 추가 - 요청 파라미터 확인
        current_app.logger.debug(f"Data Parameters: aoa={aoa}, mach={mach}, flap={flap_setting}, slat={slat_setting}")
        
        # Update simulation parameters
        simulation_instance.state["angle_of_attack"] = aoa
        simulation_instance.state["airspeed"] = mach * 340.3
        
        try:
            simulation_instance.update_settings({"flap_setting": flap_setting})
            simulation_instance.update_settings({"slat_setting": slat_setting})
        except Exception as e:
            current_app.logger.error(f"Error updating settings: {str(e)}")
            return jsonify(create_dummy_data(aoa, mach, flap_setting, slat_setting)), 200
        
        # Recompute simulation with updated parameters
        try:
            simulation_instance._compute_simulation()
        except Exception as e:
            current_app.logger.error(f"Simulation computation error: {str(e)}")
            return jsonify(create_dummy_data(aoa, mach, flap_setting, slat_setting)), 200
        
        # Base URL for the current request
        base_url = request.url_root.rstrip('/')
        
        # Current simulation state
        aoa = simulation_instance.state["angle_of_attack"]
        mach = simulation_instance.results.get("mach_number", mach)
        flap = simulation_instance.state["flap_setting"]
        slat = simulation_instance.state["slat_setting"]
        
        # Generate URLs with current parameters
        pressure_url = f"{base_url}/visualization/a320/pressure?aoa={aoa}&mach={mach}&flap={flap}&slat={slat}"
        airfoil_url = f"{base_url}/visualization/a320/airfoil?aoa={aoa}&flap={flap}&slat={slat}"
        polar_url = f"{base_url}/visualization/a320/polar?mach={mach}&flap={flap}&slat={slat}"
        
        # Get simulation results safely with default values
        lift_coefficient = simulation_instance.results.get("lift_coefficient", 0.374)
        drag_coefficient = simulation_instance.results.get("drag_coefficient", 0.0136)
        
        # Return JSON with URLs
        return jsonify({
            "pressure_plot": pressure_url,
            "airfoil_plot": airfoil_url,
            "polar_plot": polar_url,
            "current_state": {
                "angle_of_attack": aoa,
                "mach_number": mach,
                "flap_setting": flap,
                "slat_setting": slat,
                "lift_coefficient": lift_coefficient,
                "drag_coefficient": drag_coefficient
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error in data endpoint: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify(create_dummy_data()), 200

@visualization_bp.route('/a320/dashboard')
def a320_dashboard():
    """Render a dashboard with all visualizations"""
    try:
        current_app.logger.debug("A320 Dashboard requested")
        return render_template('simulation/a320_dashboard.html',
                            title="A320 Wing System Analysis Dashboard",
                            description="Comprehensive analysis of A320 aerodynamics with high-lift devices")
    except Exception as e:
        current_app.logger.error(f"Error rendering dashboard: {str(e)}")
        return f"Error loading dashboard: {str(e)}", 500

@visualization_bp.route('/test')
def test_visualization():
    """
    Simple test endpoint to verify matplotlib is working correctly
    """
    try:
        # Create a simple plot
        fig, ax = plt.subplots(figsize=(6, 4))
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        ax.plot(x, y)
        ax.set_title('Test Sine Wave')
        ax.set_xlabel('X')
        ax.set_ylabel('sin(x)')
        ax.grid(True)
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Convert to base64
        image_data = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close(fig)
        
        # Return as response
        return Response(base64.b64decode(image_data), mimetype='image/png')
    except Exception as e:
        current_app.logger.error(f"Test visualization error: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return create_error_image(f"Test visualization failed: {str(e)}"), 200

def create_error_image(error_message="Visualization error"):
    """오류 이미지 생성 - 기본 이미지 대신 사용"""
    try:
        plt.figure(figsize=(8, 4), dpi=100)
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        
        # 배경 및 테두리
        ax.set_facecolor('#f2f2f2')
        for spine in ax.spines.values():
            spine.set_edgecolor('#cccccc')
            spine.set_linewidth(1)
        
        # 텍스트 추가
        ax.text(0.5, 0.5, error_message, 
            ha='center', va='center', fontsize=12,
            transform=ax.transAxes)
        ax.set_axis_off()
        
        # 이미지로 변환
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close(fig)
        
        return Response(buffer.getvalue(), mimetype='image/png')
    except Exception as e:
        print(f"Error creating error image: {str(e)}")
        # 완전히 실패한 경우 1x1 투명 이미지
        return Response(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+P+/HgAFhAJc4RZ1SQAAAABJRU5ErkJggg=="), mimetype='image/png')

def create_dummy_data(aoa=2.0, mach=0.78, flap_setting="2", slat_setting="2"):
    """유효한 더미 데이터 생성"""
    base_url = request.url_root.rstrip('/')
    
    return {
        "pressure_plot": f"{base_url}/visualization/a320/pressure?aoa={aoa}&mach={mach}&flap={flap_setting}&slat={slat_setting}",
        "airfoil_plot": f"{base_url}/visualization/a320/airfoil?aoa={aoa}&flap={flap_setting}&slat={slat_setting}",
        "polar_plot": f"{base_url}/visualization/a320/polar?mach={mach}&flap={flap_setting}&slat={slat_setting}",
        "current_state": {
            "angle_of_attack": aoa,
            "mach_number": mach,
            "flap_setting": flap_setting,
            "slat_setting": slat_setting,
            "lift_coefficient": 0.374,
            "drag_coefficient": 0.0136
        }
    }