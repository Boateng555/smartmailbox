# IR Sensor Optimization for Mailbox Environment

Complete optimization guide for IR sensor mail detection in mailbox environment.

## Hardware Setup

### 1. IR Sensor Configuration
- **Pin**: GPIO 13 (IR sensor output)
- **Power Control**: GPIO 2 (optional MOSFET for power control)
- **Detection Range**: 10-15cm (optimized for mailbox size)
- **Lens**: Add small focusing lens to narrow detection zone

### 2. Light Sensor (Optional but Recommended)
- **Pin**: GPIO 14 (ADC input)
- **Purpose**: Distinguish day/night to prevent false positives
- **Type**: LDR (Light Dependent Resistor) or photodiode
- **Threshold**: Adjustable (default: 100 ADC units)

### 3. Power Control Circuit
```
IR Sensor VCC → MOSFET Gate (GPIO 2)
              → MOSFET Drain → 3.3V
              → MOSFET Source → IR Sensor VCC
```

**Benefits:**
- IR sensor only powered during sleep/wake cycles
- Significant power savings
- Extends battery life

## Software Logic

### Wake Sequence
1. **Wake on Interrupt**: GPIO 13 HIGH triggers wake from deep sleep
2. **First Trigger Detection**: Record timestamp
3. **Wait for Second Trigger**: Require 2 consecutive triggers within 5 seconds
4. **Validation**: If second trigger confirmed → valid mail detection
5. **Photo Capture**: Take 3 photos (1 second apart)
6. **Upload**: Send photos to server
7. **Sleep**: Return to deep sleep (max 30 seconds awake)

### False Positive Prevention

#### 1. Consecutive Trigger Requirement
- **Window**: 5 seconds for 2 triggers
- **Logic**: First trigger starts timer, second trigger confirms
- **Benefit**: Filters out brief interruptions (wind, vibration)

#### 2. Upload Protection
- **Flag**: `isUploading` prevents triggers during upload
- **Benefit**: Prevents false triggers from upload activity

#### 3. Day/Night Detection
- **Light Sensor**: Monitors ambient light
- **Usage**: Logs day/night status with photos
- **Future**: Can adjust sensitivity based on time of day

#### 4. Max Awake Time
- **Limit**: 30 seconds maximum awake time
- **Benefit**: Prevents device staying awake indefinitely
- **Safety**: Ensures return to deep sleep

## Power Saving Optimizations

### 1. IR Sensor Power Control
```cpp
// Power on before sleep
powerOnIRSensor();  // GPIO 2 HIGH

// Power off after processing (optional)
powerOffIRSensor();  // GPIO 2 LOW
```

### 2. Wake Sequence
```
1. Power IR sensor (GPIO 2 HIGH)
2. Enter deep sleep
3. Wake on IR trigger (GPIO 13 HIGH)
4. Check for second trigger
5. Take photos
6. Upload
7. Return to sleep
```

### 3. Camera Power Management
- Camera initialized only when needed
- Camera powered off during deep sleep
- Re-initialized on wake

### 4. WiFi Power Management
- WiFi disabled during deep sleep
- WiFi reconnected only when needed
- Cellular fallback if WiFi unavailable

## Configuration Parameters

### Detection Parameters
```cpp
#define IR_SENSOR_PIN          13    // IR sensor output
#define IR_SENSOR_POWER_PIN    2     // Power control (optional)
#define LIGHT_SENSOR_PIN       14    // Light sensor ADC

const unsigned long CONSECUTIVE_TRIGGER_WINDOW = 5000;  // 5 seconds
const unsigned long MAX_AWAKE_TIME = 30000;            // 30 seconds
const float LIGHT_THRESHOLD = 100.0;                    // ADC threshold
```

### Photo Capture
```cpp
const int PHOTOS_PER_TRIGGER = 3;        // 3 photos per detection
const unsigned long PHOTO_INTERVAL = 1000; // 1 second between photos
```

## Testing

### 1. False Positive Test
- Wave hand quickly past sensor → Should NOT trigger
- Place mail item → Should trigger (2 consecutive detections)

### 2. Power Consumption Test
- Measure current during sleep
- Measure current during wake
- Verify IR sensor power control working

### 3. Range Test
- Test detection at 10cm
- Test detection at 15cm
- Verify no detection beyond 20cm

### 4. Day/Night Test
- Test during daylight
- Test during night
- Verify light sensor readings

## Troubleshooting

### Issue: Too Many False Positives
**Solution:**
- Adjust `CONSECUTIVE_TRIGGER_WINDOW` (increase for stricter)
- Check IR sensor alignment
- Verify lens is properly focused
- Check for interference sources

### Issue: Missing Detections
**Solution:**
- Check IR sensor power
- Verify GPIO 13 connection
- Test sensor range (10-15cm)
- Check for obstructions

### Issue: High Power Consumption
**Solution:**
- Verify IR sensor power control working
- Check camera is powered off during sleep
- Verify WiFi is disabled during sleep
- Measure current draw with multimeter

### Issue: Device Stays Awake
**Solution:**
- Check `MAX_AWAKE_TIME` is enforced
- Verify deep sleep is being called
- Check for blocking operations

## Hardware Recommendations

### IR Sensor
- **Model**: HC-SR501 or similar PIR sensor
- **Range**: Adjustable (set to 10-15cm)
- **Lens**: Add focusing lens for narrow detection zone
- **Mounting**: Position to detect mail entry point

### Light Sensor
- **Model**: LDR (Light Dependent Resistor) or photodiode
- **Resistor**: 10kΩ pull-down resistor
- **Mounting**: Position to detect ambient light

### Power Control
- **MOSFET**: N-channel logic-level MOSFET (e.g., 2N7002)
- **Gate Resistor**: 10kΩ pull-down
- **Protection**: Optional diode for reverse current

## Performance Metrics

### Expected Behavior
- **Wake Time**: < 1 second from trigger to first photo
- **Total Awake Time**: < 30 seconds (3 photos + upload)
- **Sleep Current**: < 10mA (with IR sensor powered)
- **Detection Accuracy**: > 95% (with false positive prevention)

### Power Consumption
- **Deep Sleep**: ~5-10mA (IR sensor powered)
- **Active (Photos)**: ~200-300mA
- **Upload**: ~150-250mA
- **Daily Consumption**: ~50-100mAh (10 detections/day)

## Future Enhancements

1. **Adaptive Sensitivity**: Adjust based on time of day
2. **Machine Learning**: Learn from false positives
3. **Multi-Zone Detection**: Multiple IR sensors for better coverage
4. **Temperature Compensation**: Adjust for temperature changes
5. **Vibration Filtering**: Add accelerometer to filter vibrations

## Code Structure

### Key Functions
- `powerOnIRSensor()` - Power control
- `powerOffIRSensor()` - Power control
- `readLightSensor()` - Light level reading
- `checkDaytime()` - Day/night detection
- `enterDeepSleep()` - Optimized sleep with IR wake

### State Management
- `firstTriggerDetected` - First trigger flag
- `firstTriggerTime` - First trigger timestamp
- `isUploading` - Upload protection flag
- `wakeTime` - Wake timestamp for timeout

## Summary

The optimized IR sensor implementation provides:
- ✅ **False Positive Prevention**: 2 consecutive triggers required
- ✅ **Power Efficiency**: IR sensor power control
- ✅ **Fast Response**: < 1 second wake to photo
- ✅ **Battery Optimized**: 30 second max awake time
- ✅ **Reliable Detection**: 10-15cm range with lens
- ✅ **Day/Night Awareness**: Light sensor integration

This configuration is ideal for battery-powered mailbox installations with solar charging support.







