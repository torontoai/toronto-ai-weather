"""
Utility functions for data visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
from datetime import datetime, timedelta

def generate_weather_chart(weather_data, is_historical=False):
    """
    Generate a chart for weather data.
    
    Args:
        weather_data: WeatherData object
        is_historical: Whether this is historical data
        
    Returns:
        str: Base64 encoded image
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set style for dark theme
    plt.style.use('dark_background')
    
    # Set colors
    main_color = '#00ff00'  # Green
    accent_color = '#ff7700'  # Orange
    
    # Plot temperature
    ax.plot([weather_data.timestamp], [weather_data.temperature], 
            marker='o', markersize=8, color=main_color, label='Temperature (°C)')
    
    # Plot feels like temperature
    ax.plot([weather_data.timestamp], [weather_data.feels_like], 
            marker='x', markersize=8, color=accent_color, label='Feels Like (°C)')
    
    # Set title and labels
    title = f"Historical Weather - {weather_data.timestamp.strftime('%Y-%m-%d')}" if is_historical else "Current Weather"
    ax.set_title(title, color='white', fontsize=16)
    ax.set_xlabel('Time', color='white', fontsize=12)
    ax.set_ylabel('Temperature (°C)', color='white', fontsize=12)
    
    # Set grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Add weather condition text
    condition_text = f"Condition: {weather_data.weather_condition}\n"
    condition_text += f"Humidity: {weather_data.humidity}%\n"
    condition_text += f"Wind: {weather_data.wind_speed} m/s\n"
    condition_text += f"Pressure: {weather_data.pressure} hPa"
    
    plt.figtext(0.02, 0.02, condition_text, color='white', fontsize=10)
    
    # Save to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#000000')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Close the figure to free memory
    plt.close(fig)
    
    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    return graphic

def generate_forecast_chart(forecast_data):
    """
    Generate a chart for forecast data.
    
    Args:
        forecast_data: List of Forecast objects
        
    Returns:
        str: Base64 encoded image
    """
    if not forecast_data:
        return None
    
    # Extract data
    timestamps = [f.forecast_timestamp for f in forecast_data]
    temperatures = [f.temperature for f in forecast_data]
    feels_like = [f.feels_like for f in forecast_data]
    precipitation_prob = [f.precipitation_probability * 100 if f.precipitation_probability else 0 for f in forecast_data]
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Set style for dark theme
    plt.style.use('dark_background')
    
    # Set colors
    temp_color = '#00ff00'  # Green
    feels_color = '#00aa00'  # Darker green
    precip_color = '#ff7700'  # Orange
    
    # Plot temperature
    ax1.plot(timestamps, temperatures, marker='o', markersize=4, color=temp_color, label='Temperature (°C)')
    ax1.plot(timestamps, feels_like, marker='x', markersize=4, color=feels_color, label='Feels Like (°C)')
    
    # Set primary y-axis
    ax1.set_xlabel('Time', color='white', fontsize=12)
    ax1.set_ylabel('Temperature (°C)', color=temp_color, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=temp_color)
    
    # Create secondary y-axis for precipitation
    ax2 = ax1.twinx()
    ax2.bar(timestamps, precipitation_prob, alpha=0.3, color=precip_color, label='Precipitation Probability (%)')
    ax2.set_ylabel('Precipitation Probability (%)', color=precip_color, fontsize=12)
    ax2.tick_params(axis='y', labelcolor=precip_color)
    ax2.set_ylim(0, 100)
    
    # Set title
    start_date = timestamps[0].strftime('%Y-%m-%d')
    end_date = timestamps[-1].strftime('%Y-%m-%d')
    if start_date == end_date:
        title = f"Weather Forecast - {start_date}"
    else:
        title = f"Weather Forecast - {start_date} to {end_date}"
    
    plt.title(title, color='white', fontsize=16)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    if len(timestamps) > 12:
        plt.xticks(rotation=45)
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=4))
    
    # Add grid
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # Add weather conditions as text
    conditions = []
    for i in range(0, len(forecast_data), 6):  # Show every 6 hours
        if i < len(forecast_data):
            f = forecast_data[i]
            time_str = f.forecast_timestamp.strftime('%H:%M')
            conditions.append(f"{time_str}: {f.weather_condition}")
    
    condition_text = "\n".join(conditions)
    plt.figtext(0.02, 0.02, condition_text, color='white', fontsize=10)
    
    # Save to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#000000')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Close the figure to free memory
    plt.close(fig)
    
    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    return graphic

def generate_accuracy_chart(accuracy_data):
    """
    Generate a chart for prediction accuracy.
    
    Args:
        accuracy_data: List of (date, accuracy) tuples
        
    Returns:
        str: Base64 encoded image
    """
    if not accuracy_data:
        return None
    
    # Extract data
    dates = [d[0] for d in accuracy_data]
    accuracies = [float(d[1]) * 100 for d in accuracy_data]  # Convert to percentage
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set style for dark theme
    plt.style.use('dark_background')
    
    # Set colors
    main_color = '#00ff00'  # Green
    
    # Plot accuracy
    ax.plot(dates, accuracies, marker='o', markersize=6, color=main_color, label='Prediction Accuracy (%)')
    
    # Fill area under the curve
    ax.fill_between(dates, accuracies, alpha=0.3, color=main_color)
    
    # Set title and labels
    ax.set_title('Prediction Accuracy Over Time', color='white', fontsize=16)
    ax.set_xlabel('Date', color='white', fontsize=12)
    ax.set_ylabel('Accuracy (%)', color='white', fontsize=12)
    
    # Set y-axis limits
    ax.set_ylim(0, 100)
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    # Add legend
    ax.legend(loc='lower right')
    
    # Add average accuracy text
    avg_accuracy = sum(accuracies) / len(accuracies)
    plt.figtext(0.02, 0.02, f"Average Accuracy: {avg_accuracy:.2f}%", color='white', fontsize=12)
    
    # Save to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#000000')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Close the figure to free memory
    plt.close(fig)
    
    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    return graphic

def generate_system_metrics_chart(metrics_data):
    """
    Generate a chart for system metrics.
    
    Args:
        metrics_data: List of SystemMetrics objects
        
    Returns:
        str: Base64 encoded image
    """
    if not metrics_data:
        return None
    
    # Extract data
    timestamps = [m.timestamp for m in metrics_data]
    active_devices = [m.active_devices for m in metrics_data]
    system_loads = [m.system_load * 100 for m in metrics_data]  # Convert to percentage
    prediction_accuracies = [m.average_prediction_accuracy * 100 for m in metrics_data]  # Convert to percentage
    
    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 7))
    
    # Set style for dark theme
    plt.style.use('dark_background')
    
    # Set colors
    devices_color = '#00ff00'  # Green
    load_color = '#ff7700'  # Orange
    accuracy_color = '#00aaff'  # Blue
    
    # Plot active devices
    ax1.plot(timestamps, active_devices, marker='o', markersize=4, color=devices_color, label='Active Devices')
    
    # Set primary y-axis
    ax1.set_xlabel('Time', color='white', fontsize=12)
    ax1.set_ylabel('Active Devices', color=devices_color, fontsize=12)
    ax1.tick_params(axis='y', labelcolor=devices_color)
    
    # Create secondary y-axis for system load
    ax2 = ax1.twinx()
    ax2.plot(timestamps, system_loads, marker='s', markersize=4, color=load_color, label='System Load (%)')
    ax2.plot(timestamps, prediction_accuracies, marker='^', markersize=4, color=accuracy_color, label='Prediction Accuracy (%)')
    ax2.set_ylabel('Percentage (%)', color='white', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='white')
    ax2.set_ylim(0, 100)
    
    # Set title
    plt.title('System Metrics Over Time', color='white', fontsize=16)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    # Add grid
    ax1.grid(True, linestyle='--', alpha=0.7)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    # Save to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', facecolor='#000000')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    # Close the figure to free memory
    plt.close(fig)
    
    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    return graphic
