# ESP32-CAM Hardware - Quick Reference Card

## Pin Assignment Summary

| GPIO | Component | Direction | Notes |
|------|-----------|-----------|-------|
| 0 | Camera XCLK | Output | Keep LOW during boot |
| 2 | IR Power Control | Output | Optional MOSFET gate |
| 4 | LED Status | Output | Built-in flash LED |
| 5 | Camera Y2 | Input | Camera data |
| 12 | Reed Switch | Input | Pull-up enabled |
| 13 | IR Sensor | Input | Pull-down enabled |
| 14 | Light/Battery ADC | Input | Shared ADC pin |
| 15 | Solar Status | Input | Optional |
| 16 | A7670 RX (ESP32 TX) | Output | UART2 TX |
| 17 | A7670 TX (ESP32 RX) | Input | UART2 RX |
| 18 | Camera Y3 | Input | Camera data |
| 19 | Camera Y4 | Input | Camera data |
| 21 | Camera Y5 | Input | Camera data |
| 22 | Camera PCLK | Input | Camera pixel clock |
| 23 | Camera HREF | Input | Camera horizontal ref |
| 25 | Camera VSYNC | Input | Camera vertical sync |
| 26 | Camera SIOD | I2C | Camera I2C data |
| 27 | Camera SIOC | I2C | Camera I2C clock |
| 32 | Camera PWDN | Output | Camera power down |
| 33 | A7670 Power | Output | Power control (HIGH 1s to boot) |
| 34 | Camera Y8 | Input | Camera data (input only) |
| 35 | Camera Y9 | Input | Camera data (input only) |
| 36 | Camera Y6 | Input | Camera data (input only) |
| 39 | Camera Y7 | Input | Camera data (input only) |

## Power Connections

```
Battery (3.7V LiPo)
├── + → Voltage Divider → GPIO 14 (battery monitoring)
├── + → 5V Regulator → A7670 VCC
├── + → 3.3V Regulator → ESP32-CAM 5V
└── - → Common GND
```

## Component Connections

### A7670 Module
- **VCC**: 5V (via regulator)
- **GND**: Common ground
- **TX**: GPIO 16 (ESP32 RX)
- **RX**: GPIO 17 (ESP32 TX)
- **PWR_KEY**: GPIO 33

### IR Sensor
- **VCC**: 3.3V (or via MOSFET from GPIO 2)
- **GND**: Common ground
- **OUT**: GPIO 13

### Reed Switch
- **Terminal 1**: GPIO 12
- **Terminal 2**: GND

### Light Sensor
- **One terminal**: GPIO 14 (via voltage divider)
- **Other terminal**: GND

## Quick Test Commands

Via Serial Monitor (115200 baud):
- `help` - Show commands
- `status` - System status
- `capture` - Take photo
- `test_ir` - Test IR sensor
- `test_reed` - Test reed switch
- `test_cellular` - Test A7670

## Power Consumption

- **Active**: ~250mA @ 3.7V = 925mW
- **Deep Sleep**: ~10µA @ 3.7V = 0.037mW
- **Peak (A7670 TX)**: ~2200mA @ 3.7V = 8.14W

## Battery Life Estimate

**5000mAh Battery:**
- Active 1hr/day: ~21 days
- With 5W solar (4hrs/day): Indefinite

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| ESP32 won't boot | Check GPIO 0 is LOW |
| A7670 no response | Check power (5V, 2A), verify TX/RX |
| IR false triggers | Adjust sensitivity, add lens |
| Battery drains fast | Verify deep sleep, check for leaks |
| No network | Check SIM, verify APN settings |

## Critical Notes

⚠️ **GPIO 0**: Must be LOW during boot (HIGH = download mode)
⚠️ **GPIO 4**: Built-in LED, don't use for A7670 power
⚠️ **A7670 Power**: Needs 5V @ 2A peak, use proper regulator
⚠️ **Battery**: Use protected LiPo, monitor voltage
⚠️ **UART**: A7670 TX → ESP32 RX (GPIO 16), A7670 RX → ESP32 TX (GPIO 17)

## Serial Monitor Settings

- **Baud Rate**: 115200
- **Line Ending**: Both NL & CR
- **Auto-scroll**: Enabled

## Next Steps After Wiring

1. ✅ Verify all connections
2. ✅ Check power voltages
3. ✅ Flash firmware
4. ✅ Run component tests
5. ✅ Test integration
6. ✅ Deploy to mailbox


