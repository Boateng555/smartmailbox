# ESP32-CAM Smart Mailbox Camera - Hardware Wiring Guide

## Overview
This guide provides complete wiring instructions for the ESP32-CAM Smart Mailbox Camera system with cellular connectivity, mail detection, and battery power.

## Components Required

### Main Components
1. **ESP32-CAM (AI-Thinker)** - Main microcontroller with camera
2. **A7670 4G/LTE Module** - Cellular connectivity module
3. **IR Sensor Module** (e.g., HC-SR501 or similar) - Mail detection
4. **Reed Switch** - Door state detection
5. **Light Sensor (LDR/Photodiode)** - Day/night detection (optional)
6. **Battery Pack** - 3.7V LiPo or 18650 battery (with protection circuit)
7. **Solar Panel** (optional) - For charging battery
8. **Voltage Divider Circuit** - For battery voltage monitoring
9. **MOSFET (N-channel)** - For IR sensor power control (optional)
10. **Resistors** - For voltage divider and pull-up/pull-down
11. **LED** - Status indicator (built-in on ESP32-CAM)

## Complete Pin Assignment Table

| Component | GPIO Pin | Function | Notes |
|-----------|----------|----------|-------|
| **Camera Module** | | | Built-in on ESP32-CAM |
| Camera PWDN | GPIO 32 | Power down | |
| Camera XCLK | GPIO 0 | Clock | |
| Camera SIOD | GPIO 26 | I2C Data | |
| Camera SIOC | GPIO 27 | I2C Clock | |
| Camera Y2-Y9 | GPIO 5,18,19,21,36,39,34,35 | Data lines | |
| Camera VSYNC | GPIO 25 | Vertical sync | |
| Camera HREF | GPIO 23 | Horizontal ref | |
| Camera PCLK | GPIO 22 | Pixel clock | |
| **A7670 4G Module** | | | |
| A7670 Power | GPIO 33 | Power control | HIGH for 1s to boot |
| A7670 TX | GPIO 17 | UART TX (ESP32 RX) | Connect to A7670 RX |
| A7670 RX | GPIO 16 | UART RX (ESP32 TX) | Connect to A7670 TX |
| A7670 GND | GND | Ground | |
| A7670 VCC | 5V | Power (via regulator) | Requires 5V, 2A peak |
| **IR Sensor** | | | |
| IR Sensor OUT | GPIO 13 | Detection signal | INPUT_PULLDOWN |
| IR Sensor VCC | 3.3V or MOSFET | Power | Via GPIO 2 if using MOSFET |
| IR Sensor GND | GND | Ground | |
| IR Power Control | GPIO 2 | MOSFET gate | Optional power control |
| **Reed Switch** | | | |
| Reed Switch | GPIO 12 | Door state | INPUT_PULLUP |
| **Light Sensor** | | | |
| Light Sensor | GPIO 14 | ADC input | LDR or photodiode |
| **Battery Monitoring** | | | |
| Battery Voltage | GPIO 14 | ADC input | Shared with light sensor |
| **Solar Charging** | | | |
| Solar Status | GPIO 15 | Charging status | Optional |
| **Status LED** | | | |
| LED Status | GPIO 4 | Built-in flash LED | On ESP32-CAM board |

## Detailed Wiring Instructions

### 1. ESP32-CAM Base Connections

```
ESP32-CAM
├── 5V Power Input (for programming/debugging)
├── GND (common ground)
└── USB-to-Serial (for programming)
    ├── TX → ESP32 GPIO 1
    └── RX → ESP32 GPIO 3
```

**Note:** GPIO 0 must be LOW during boot for normal operation. Keep it HIGH only when flashing firmware.

### 2. A7670 4G Module Wiring

```
A7670 Module Connections:
├── VCC → 5V (via voltage regulator from battery)
├── GND → Common GND
├── TX → ESP32 GPIO 16 (UART2 RX)
├── RX → ESP32 GPIO 17 (UART2 TX)
└── PWR_KEY → ESP32 GPIO 33 (Power control)

Power Requirements:
- Operating Voltage: 3.4V - 4.4V (typical 3.8V)
- Peak Current: Up to 2A during transmission
- Use a 5V regulator with 2A+ capacity
- Add 1000µF capacitor near module for power stability
```

**Power Control Circuit:**
```
ESP32 GPIO 33 → A7670 PWR_KEY pin
- Pull LOW to turn off
- Pull HIGH for 1 second to turn on
- Module boots in ~5 seconds after power on
```

**UART Connection:**
- Baud Rate: 115200
- Use UART2 on ESP32 (GPIO 16 = RX, GPIO 17 = TX)
- Connect A7670 TX to ESP32 RX (GPIO 16)
- Connect A7670 RX to ESP32 TX (GPIO 17)

### 3. IR Sensor Wiring

```
IR Sensor Module (e.g., HC-SR501):
├── VCC → 3.3V (or via MOSFET from GPIO 2)
├── GND → GND
└── OUT → ESP32 GPIO 13

Optional Power Control (for power saving):
├── ESP32 GPIO 2 → MOSFET Gate (N-channel)
├── MOSFET Drain → 3.3V
└── MOSFET Source → IR Sensor VCC
```

**IR Sensor Configuration:**
- Detection Range: 10-15cm (adjustable via potentiometer)
- Trigger Mode: Single trigger (not repeat trigger)
- Sensitivity: Adjust for mailbox environment
- Add focusing lens to narrow detection zone

### 4. Reed Switch Wiring

```
Reed Switch:
├── One terminal → ESP32 GPIO 12
├── Other terminal → GND
└── Internal pull-up enabled on GPIO 12

Operation:
- CLOSED (magnet near): GPIO 12 = LOW (door closed)
- OPEN (magnet away): GPIO 12 = HIGH (door open)
```

**Installation:**
- Mount reed switch on mailbox door frame
- Mount magnet on door
- Adjust gap for reliable operation (typically 5-10mm)

### 5. Light Sensor Wiring (Optional)

```
Light Sensor (LDR or Photodiode):
├── One terminal → ESP32 GPIO 14 (ADC)
├── Other terminal → GND
└── Pull-up resistor: 10kΩ to 3.3V (if needed)

Alternative (Voltage Divider):
├── 3.3V → LDR → GPIO 14 → 10kΩ resistor → GND
```

**Calibration:**
- Daytime: ADC reading > 100 (adjustable)
- Nighttime: ADC reading < 100
- Adjust threshold in firmware based on your environment

### 6. Battery Monitoring Circuit

```
Battery Voltage Divider:
├── Battery + → 10kΩ resistor → ESP32 GPIO 14
├── ESP32 GPIO 14 → 10kΩ resistor → GND
└── Battery - → GND

Calculation:
- Battery voltage = ADC_reading * (3.3V / 4095) * 2
- Divider ratio: 2:1 (two equal 10kΩ resistors)
- Max measurable: 6.6V (safe for 3.7V LiPo)
```

**Note:** GPIO 14 is shared between light sensor and battery monitoring. The firmware reads them at different times.

### 7. Solar Charging (Optional)

```
Solar Panel → Charge Controller → Battery
├── Charge Controller Status → ESP32 GPIO 15
└── Monitor charging state

Typical Setup:
- 5V solar panel (6V open circuit)
- TP4056 or similar charge controller
- Status pin indicates charging state
```

### 8. Power Supply System

```
Complete Power System:
├── Battery (3.7V LiPo or 18650)
│   ├── + → Voltage Divider (for monitoring)
│   └── - → GND
├── 5V Regulator (for A7670)
│   ├── Input: Battery voltage
│   ├── Output: 5V @ 2A
│   └── Add 1000µF capacitor on output
├── 3.3V Regulator (for ESP32-CAM)
│   ├── Input: Battery voltage
│   └── Output: 3.3V @ 1A
└── Solar Charger (optional)
    └── TP4056 or similar module
```

**Power Requirements:**
- ESP32-CAM: ~200mA active, ~10µA deep sleep
- A7670 Module: ~50mA idle, up to 2A peak during transmission
- IR Sensor: ~50µA (or 0µA if power-controlled)
- Total: ~250mA average, 2.2A peak

**Battery Sizing:**
- Minimum: 2000mAh for 8 hours operation
- Recommended: 5000mAh+ for 24+ hours
- With solar: 2000mAh sufficient for overnight

## Complete Wiring Diagram (Text)

```
                    ┌─────────────────┐
                    │   ESP32-CAM     │
                    │  (AI-Thinker)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        │                    │                    │
    ┌───▼───┐          ┌─────▼─────┐        ┌───▼───┐
    │Camera │          │  A7670    │        │  IR   │
    │Module │          │  4G Mod   │        │Sensor │
    │(Built)│          └─────┬─────┘        └───┬───┘
    └───────┘                │                  │
                             │                  │
        GPIO 33 ─────────────┼── PWR_KEY        │
        GPIO 16 ─────────────┼── RX             │
        GPIO 17 ─────────────┼── TX             │
        GPIO 13 ────────────────────────────────┼── OUT
        GPIO 12 ────────────────────────────────┐
        GPIO 14 ────────────────────────────────┼── ADC
        GPIO 15 ────────────────────────────────┐
        GPIO 4  ────────────────────────────────┐ (LED)
        GPIO 2  ────────────────────────────────┐ (IR Power)
                             │                  │
                             │                  │
                    ┌────────▼────────┐  ┌─────▼─────┐
                    │  Reed Switch    │  │  Light    │
                    │  (Door State)   │  │  Sensor   │
                    └─────────────────┘  └───────────┘
                             │
                    ┌────────▼────────┐
                    │   Battery       │
                    │   (3.7V LiPo)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  5V Regulator    │
                    │  (for A7670)     │
                    └──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Solar Charger  │
                    │   (Optional)    │
                    └─────────────────┘
```

## Power Distribution

### Recommended Power Setup

1. **Battery Pack**
   - 3.7V LiPo battery (2000mAh minimum, 5000mAh recommended)
   - Built-in protection circuit (overcharge/overdischarge)
   - JST connector for easy replacement

2. **Voltage Regulators**
   - **5V Regulator** (for A7670): LM2596 or similar, 2A capacity
   - **3.3V Regulator** (for ESP32): AMS1117 or similar, 1A capacity
   - Add capacitors: 100µF + 10µF on input, 100µF + 10µF on output

3. **Power Management**
   - Enable deep sleep mode for power saving
   - IR sensor power control via MOSFET (optional)
   - Monitor battery voltage and warn when low

## Antenna Connections

### A7670 Module Antennas
- **Main Antenna**: Connect to ANT1 connector (primary cellular antenna)
- **GPS Antenna** (if GPS enabled): Connect to ANT2 connector
- Use proper 50Ω coaxial cable
- Position antennas away from metal surfaces

### ESP32-CAM WiFi Antenna
- Built-in PCB antenna (default)
- Or external antenna via IPEX connector (if available)

## Safety Considerations

1. **Power Protection**
   - Use battery with protection circuit
   - Add fuse (1A) on battery positive
   - Reverse polarity protection diode

2. **Voltage Levels**
   - ESP32-CAM: 3.3V logic (NOT 5V tolerant on all pins)
   - A7670: 3.4V-4.4V (use proper regulator)
   - Never exceed 3.3V on ESP32 GPIO pins

3. **Current Limits**
   - ESP32 GPIO: Max 40mA per pin
   - Total GPIO current: Max 1.2A
   - Use MOSFETs for higher current loads

4. **ESD Protection**
   - Add TVS diodes on exposed connections
   - Use proper grounding

## Testing Checklist

Before final assembly, test each component:

- [ ] ESP32-CAM boots and camera initializes
- [ ] A7670 powers on and responds to AT commands
- [ ] IR sensor triggers correctly
- [ ] Reed switch reads door state
- [ ] Light sensor reads ambient light
- [ ] Battery voltage monitoring works
- [ ] LED status indicator blinks
- [ ] All power rails are correct voltage
- [ ] No short circuits or overheating

## Troubleshooting

### Common Issues

1. **ESP32 won't boot**
   - Check GPIO 0 is LOW (not HIGH)
   - Verify power supply (3.3V stable)
   - Check for short circuits

2. **A7670 not responding**
   - Verify power (5V, sufficient current)
   - Check UART connections (TX/RX swapped?)
   - Verify PWR_KEY timing (HIGH for 1s)

3. **IR sensor false triggers**
   - Adjust sensitivity potentiometer
   - Add focusing lens
   - Check for interference

4. **Battery drains quickly**
   - Verify deep sleep is working
   - Check for power leaks
   - Disable unnecessary components

## Next Steps

After wiring is complete:
1. Flash firmware to ESP32-CAM
2. Test each component individually
3. Run system integration tests
4. See `HARDWARE_TESTING_PROCEDURE.md` for detailed testing steps


