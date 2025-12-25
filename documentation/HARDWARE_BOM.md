# ESP32-CAM Smart Mailbox Camera - Bill of Materials (BOM)

## Complete Component List

### Core Components

| Qty | Part | Description | Part Number | Supplier | Price (Est.) |
|-----|------|-------------|-------------|----------|--------------|
| 1 | ESP32-CAM | ESP32 with camera module (AI-Thinker) | ESP32-CAM | AliExpress, Amazon | $8-12 |
| 1 | A7670 4G Module | 4G/LTE cellular module with antenna | A7670SA | AliExpress, Mouser | $15-25 |
| 1 | SIM Card | 4G/LTE SIM with data plan | - | Local carrier | $5-20/month |

### Sensors

| Qty | Part | Description | Part Number | Supplier | Price (Est.) |
|-----|------|-------------|-------------|----------|--------------|
| 1 | IR Motion Sensor | PIR motion sensor for mail detection | HC-SR501 | AliExpress, Amazon | $1-3 |
| 1 | Reed Switch | Magnetic door sensor | - | AliExpress, Amazon | $1-2 |
| 1 | Light Sensor | LDR or photodiode (optional) | LDR 5mm | AliExpress, Amazon | $0.50 |

### Power System

| Qty | Part | Description | Part Number | Supplier | Price (Est.) |
|-----|------|-------------|-------------|----------|--------------|
| 1 | LiPo Battery | 3.7V battery pack (2000-5000mAh) | 18650 or LiPo | AliExpress, Amazon | $5-15 |
| 1 | Battery Protection | Protection circuit module | TP4056 or similar | AliExpress | $1-2 |
| 1 | 5V Regulator | Step-up/step-down regulator (2A) | LM2596, XL6009 | AliExpress | $2-3 |
| 1 | 3.3V Regulator | LDO regulator (1A) | AMS1117-3.3 | AliExpress | $0.50 |
| 1 | Solar Panel | 5V solar panel (optional) | 5V 1W-5W | AliExpress | $5-10 |
| 1 | Solar Charger | Charge controller (optional) | TP4056 | AliExpress | $1-2 |

### Passive Components

| Qty | Part | Description | Value | Supplier | Price (Est.) |
|-----|------|-------------|-------|----------|--------------|
| 2 | Resistor | Voltage divider (battery monitoring) | 10kΩ 1/4W | AliExpress | $0.10 |
| 1 | Resistor | Pull-up for light sensor (if needed) | 10kΩ 1/4W | AliExpress | $0.10 |
| 1 | Capacitor | Power supply filtering | 1000µF 16V | AliExpress | $0.50 |
| 4 | Capacitor | Decoupling capacitors | 100µF, 10µF | AliExpress | $0.50 |
| 1 | MOSFET | N-channel for IR power control (optional) | 2N7000 or similar | AliExpress | $0.50 |
| 1 | Diode | Reverse polarity protection | 1N4007 | AliExpress | $0.10 |
| 1 | Fuse | Battery protection | 1A fast-blow | AliExpress | $0.50 |

### Connectors & Hardware

| Qty | Part | Description | Supplier | Price (Est.) |
|-----|------|-------------|----------|--------------|
| 1 | USB-to-Serial | FTDI or CP2102 adapter | AliExpress | $3-5 |
| 1 | JST Connector | Battery connector | AliExpress | $0.50 |
| 1 | Antenna | A7670 cellular antenna | Included with module | - |
| 1 | Enclosure | Weatherproof box | Local hardware store | $5-15 |
| 1 | Mounting Hardware | Screws, standoffs | Local hardware store | $2-5 |

### Tools & Supplies

| Qty | Part | Description | Supplier | Price (Est.) |
|-----|------|-------------|----------|--------------|
| 1 | Soldering Iron | Basic soldering station | Local store | $20-50 |
| 1 | Multimeter | Digital multimeter | Local store | $20-40 |
| 1 | Wire | Jumper wires, hookup wire | AliExpress | $5-10 |
| 1 | Breadboard | For testing (optional) | AliExpress | $3-5 |
| 1 | Heat Shrink | Wire protection | AliExpress | $2-5 |

## Detailed Component Specifications

### ESP32-CAM (AI-Thinker)
- **Microcontroller**: ESP32 (240MHz dual-core)
- **Camera**: OV2640 (2MP)
- **Memory**: 520KB SRAM, 4MB PSRAM (some models)
- **WiFi**: 802.11 b/g/n
- **GPIO**: Multiple GPIO pins available
- **Power**: 3.3V, ~200mA active, ~10µA deep sleep
- **Dimensions**: 27mm x 40.5mm

### A7670 4G Module
- **Technology**: 4G LTE Cat-1
- **Bands**: FDD-LTE B1/B3/B5/B7/B8/B20, TDD-LTE B38/B40/B41
- **Data Rate**: Up to 10Mbps down, 5Mbps up
- **Power**: 3.4V-4.4V (typical 3.8V), 50mA idle, up to 2A peak
- **Interface**: UART (115200 baud default)
- **Antenna**: External antenna required (included)
- **SIM**: Standard micro-SIM or nano-SIM (with adapter)

### IR Motion Sensor (HC-SR501)
- **Detection Range**: 3-7 meters (adjustable)
- **Detection Angle**: 110°
- **Power**: 5V (or 3.3V with modification), ~50µA
- **Output**: Digital HIGH/LOW
- **Trigger Modes**: Single trigger, repeat trigger
- **Sensitivity**: Adjustable via potentiometer
- **Delay Time**: Adjustable via potentiometer

### Reed Switch
- **Type**: Normally open (NO)
- **Operating Voltage**: Up to 200V
- **Current Rating**: Up to 0.5A
- **Actuation Distance**: 5-10mm typical
- **Mounting**: Surface mount or through-hole

### Light Sensor (LDR)
- **Type**: Photoresistor
- **Resistance Range**: 10kΩ (dark) to 1kΩ (bright)
- **Response Time**: ~100ms
- **Spectral Response**: Visible light
- **Package**: 5mm or 10mm

### Battery (LiPo)
- **Voltage**: 3.7V nominal (4.2V fully charged, 3.0V minimum)
- **Capacity**: 2000-5000mAh recommended
- **Chemistry**: Lithium Polymer
- **Protection**: Built-in protection circuit required
- **Connector**: JST-XH or similar

### Voltage Regulators

**5V Regulator (for A7670)**
- **Input**: 3.0V-5.5V (from battery)
- **Output**: 5V @ 2A
- **Efficiency**: >85%
- **Options**: LM2596 (switching), XL6009 (boost)

**3.3V Regulator (for ESP32)**
- **Input**: 3.5V-5.5V (from battery)
- **Output**: 3.3V @ 1A
- **Type**: LDO (AMS1117) or switching
- **Efficiency**: >80%

### Solar Panel (Optional)
- **Voltage**: 5V (6V open circuit)
- **Power**: 1W-5W
- **Current**: 200mA-1A
- **Type**: Monocrystalline or polycrystalline
- **Weatherproof**: Required for outdoor use

## Recommended Suppliers

### Online Retailers
- **AliExpress**: Best prices, longer shipping
- **Amazon**: Faster shipping, higher prices
- **Mouser/Digikey**: Professional components, higher prices
- **SparkFun/Adafruit**: Quality components, good documentation

### Local Stores
- Electronics stores for basic components
- Hardware stores for enclosures and mounting
- Mobile carriers for SIM cards

## Cost Estimate

### Minimum Configuration (WiFi only, no cellular)
- ESP32-CAM: $10
- IR Sensor: $2
- Reed Switch: $1
- Battery: $8
- Regulators: $3
- Misc components: $5
- **Total: ~$30**

### Full Configuration (with cellular)
- ESP32-CAM: $10
- A7670 Module: $20
- SIM Card: $10/month
- IR Sensor: $2
- Reed Switch: $1
- Battery: $10
- Regulators: $5
- Solar Panel: $8
- Enclosure: $10
- Misc components: $10
- **Total: ~$86 + $10/month**

## Assembly Considerations

### PCB Design (Optional)
For production, consider designing a custom PCB:
- Reduces wiring complexity
- Improves reliability
- Better power distribution
- Professional appearance
- Cost: $50-200 for small batch

### Enclosure Requirements
- Weatherproof (IP65 or better)
- Ventilation for heat dissipation
- Antenna access
- Battery access
- Camera lens opening
- Mounting points

### Power Budget Analysis

**Active Mode:**
- ESP32-CAM: 200mA @ 3.3V = 660mW
- A7670 (idle): 50mA @ 3.8V = 190mW
- IR Sensor: 50µA @ 3.3V = 0.17mW
- Total: ~850mW

**Peak Mode (transmitting):**
- ESP32-CAM: 200mA @ 3.3V = 660mW
- A7670 (peak): 2000mA @ 3.8V = 7600mW
- Total: ~8.3W

**Deep Sleep:**
- ESP32-CAM: 10µA @ 3.3V = 0.033mW
- A7670 (off): 0mA
- IR Sensor (off): 0mA
- Total: ~0.033mW

**Battery Life Estimate (5000mAh @ 3.7V = 18.5Wh):**
- Active (1 hour/day): 0.85Wh/day
- Deep sleep (23 hours/day): 0.00076Wh/day
- Total: ~0.85Wh/day
- **Battery life: ~21 days** (without solar)
- **With solar (5W, 4 hours/day = 20Wh/day):** Indefinite operation

## Ordering Checklist

Before ordering, verify:
- [ ] All components are in stock
- [ ] Shipping times are acceptable
- [ ] Total cost is within budget
- [ ] Spare components for testing
- [ ] Tools are available
- [ ] SIM card plan is activated
- [ ] Enclosure size fits all components

## Alternative Components

### If A7670 is unavailable:
- **SIM800L**: 2G module (cheaper, but 2G being phased out)
- **SIM7600**: 4G module (similar to A7670)
- **ESP32 with external modem**: More flexible but complex

### If IR sensor is too sensitive:
- **Ultrasonic sensor**: HC-SR04 (more precise distance)
- **Laser break beam**: More accurate but complex
- **Weight sensor**: Detects mail weight

### If battery is too large:
- **Smaller battery**: 1000mAh (shorter runtime)
- **External power**: AC adapter (if available)
- **Solar only**: Requires larger panel

## Next Steps

1. Review BOM and select components
2. Order components from suppliers
3. While waiting, prepare tools and workspace
4. Review wiring guide
5. Prepare testing procedures
6. Begin assembly when components arrive


