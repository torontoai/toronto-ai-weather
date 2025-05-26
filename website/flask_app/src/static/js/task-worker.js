"""
Task worker script for distributed computation.

This script runs in a Web Worker to perform computation tasks
without blocking the main thread.
"""

// Listen for messages from the main thread
self.onmessage = function(e) {
    const task = e.data;
    
    console.log('Worker received task:', task);
    
    // Start timing
    const startTime = performance.now();
    
    // Process task based on type
    switch (task.task_type) {
        case 'weather_prediction':
            processWeatherPrediction(task);
            break;
        case 'data_processing':
            processDataProcessing(task);
            break;
        case 'model_training':
            processModelTraining(task);
            break;
        case 'anomaly_detection':
            processAnomalyDetection(task);
            break;
        default:
            // Unknown task type
            self.postMessage({
                status: 'failed',
                error: 'Unknown task type: ' + task.task_type,
                task_uuid: task.task_uuid
            });
    }
    
    function processWeatherPrediction(task) {
        try {
            // Simulate CPU-intensive weather prediction
            const result = simulateWeatherPrediction(task.data);
            
            // Calculate duration
            const duration = (performance.now() - startTime) / 1000;
            
            // Send result back to main thread
            self.postMessage({
                status: 'completed',
                task_uuid: task.task_uuid,
                result: result,
                cpu_usage: 0.8, // Simulated CPU usage (0-1)
                memory_usage: 256, // Simulated memory usage in MB
                duration: duration,
                result_quality: 0.95 // Simulated quality score (0-1)
            });
        } catch (error) {
            self.postMessage({
                status: 'failed',
                task_uuid: task.task_uuid,
                error: error.message
            });
        }
    }
    
    function processDataProcessing(task) {
        try {
            // Simulate CPU-intensive data processing
            const result = simulateDataProcessing(task.data);
            
            // Calculate duration
            const duration = (performance.now() - startTime) / 1000;
            
            // Send result back to main thread
            self.postMessage({
                status: 'completed',
                task_uuid: task.task_uuid,
                result: result,
                cpu_usage: 0.6, // Simulated CPU usage (0-1)
                memory_usage: 128, // Simulated memory usage in MB
                duration: duration,
                result_quality: 0.98 // Simulated quality score (0-1)
            });
        } catch (error) {
            self.postMessage({
                status: 'failed',
                task_uuid: task.task_uuid,
                error: error.message
            });
        }
    }
    
    function processModelTraining(task) {
        try {
            // Simulate CPU-intensive model training
            const result = simulateModelTraining(task.data);
            
            // Calculate duration
            const duration = (performance.now() - startTime) / 1000;
            
            // Send result back to main thread
            self.postMessage({
                status: 'completed',
                task_uuid: task.task_uuid,
                result: result,
                cpu_usage: 0.9, // Simulated CPU usage (0-1)
                memory_usage: 512, // Simulated memory usage in MB
                duration: duration,
                result_quality: 0.92 // Simulated quality score (0-1)
            });
        } catch (error) {
            self.postMessage({
                status: 'failed',
                task_uuid: task.task_uuid,
                error: error.message
            });
        }
    }
    
    function processAnomalyDetection(task) {
        try {
            // Simulate CPU-intensive anomaly detection
            const result = simulateAnomalyDetection(task.data);
            
            // Calculate duration
            const duration = (performance.now() - startTime) / 1000;
            
            // Send result back to main thread
            self.postMessage({
                status: 'completed',
                task_uuid: task.task_uuid,
                result: result,
                cpu_usage: 0.7, // Simulated CPU usage (0-1)
                memory_usage: 192, // Simulated memory usage in MB
                duration: duration,
                result_quality: 0.94 // Simulated quality score (0-1)
            });
        } catch (error) {
            self.postMessage({
                status: 'failed',
                task_uuid: task.task_uuid,
                error: error.message
            });
        }
    }
};

// Simulate weather prediction computation
function simulateWeatherPrediction(data) {
    // In a real implementation, this would run actual prediction algorithms
    // For now, just simulate computation
    
    // Simulate CPU-intensive work
    let result = 0;
    for (let i = 0; i < 10000000; i++) {
        result += Math.sin(i * 0.0001) * Math.cos(i * 0.0002);
    }
    
    // Generate simulated prediction result
    return {
        location: data.location,
        timestamp: new Date().toISOString(),
        predictions: {
            temperature: 22.5 + (Math.random() * 5 - 2.5),
            humidity: 65 + (Math.random() * 20 - 10),
            wind_speed: 10 + (Math.random() * 8 - 4),
            precipitation_probability: Math.random() * 0.5,
            weather_condition: 'Partly Cloudy'
        },
        confidence: 0.85 + (Math.random() * 0.1)
    };
}

// Simulate data processing computation
function simulateDataProcessing(data) {
    // In a real implementation, this would process actual weather data
    // For now, just simulate computation
    
    // Simulate CPU-intensive work
    let result = 0;
    for (let i = 0; i < 5000000; i++) {
        result += Math.sqrt(i) * Math.log(i + 1);
    }
    
    // Generate simulated processing result
    return {
        processed_records: Math.floor(Math.random() * 1000) + 500,
        valid_records: Math.floor(Math.random() * 900) + 400,
        invalid_records: Math.floor(Math.random() * 100),
        processing_time: (Math.random() * 2 + 0.5).toFixed(2),
        data_quality_score: 0.92 + (Math.random() * 0.08)
    };
}

// Simulate model training computation
function simulateModelTraining(data) {
    // In a real implementation, this would train actual ML models
    // For now, just simulate computation
    
    // Simulate CPU-intensive work
    let result = 0;
    for (let i = 0; i < 15000000; i++) {
        result += Math.tanh(i * 0.0001) * Math.atanh((i % 10000) / 10000);
    }
    
    // Generate simulated training result
    return {
        model_type: data.model_type || 'LSTM',
        epochs_completed: 50,
        training_accuracy: 0.89 + (Math.random() * 0.1),
        validation_accuracy: 0.85 + (Math.random() * 0.1),
        loss: 0.15 + (Math.random() * 0.1),
        training_time: (Math.random() * 5 + 2).toFixed(2),
        model_size_kb: Math.floor(Math.random() * 1000) + 500
    };
}

// Simulate anomaly detection computation
function simulateAnomalyDetection(data) {
    // In a real implementation, this would run actual anomaly detection
    // For now, just simulate computation
    
    // Simulate CPU-intensive work
    let result = 0;
    for (let i = 0; i < 8000000; i++) {
        result += Math.pow(Math.sin(i * 0.0002), 2) * Math.pow(Math.cos(i * 0.0003), 2);
    }
    
    // Determine if there's an anomaly (20% chance)
    const hasAnomaly = Math.random() < 0.2;
    
    // Generate simulated anomaly detection result
    return {
        data_points_analyzed: Math.floor(Math.random() * 10000) + 5000,
        anomalies_detected: hasAnomaly ? Math.floor(Math.random() * 5) + 1 : 0,
        confidence_score: 0.9 + (Math.random() * 0.1),
        detection_threshold: 0.75,
        processing_time: (Math.random() * 3 + 1).toFixed(2),
        anomalies: hasAnomaly ? [
            {
                type: 'temperature_spike',
                severity: Math.random() * 0.5 + 0.5,
                timestamp: new Date(Date.now() - Math.floor(Math.random() * 86400000)).toISOString()
            }
        ] : []
    };
}
