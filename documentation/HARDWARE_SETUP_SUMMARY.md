# ESP32-CAM Hardware Setup - Complete Summary

## Overview
This document provides a complete overview of the hardware setup process for the ESP32-CAM Smart Mailbox Camera system.

## Documentation Structure

### 1. **HARDWARE_WIRING_GUIDE.md**
   - Complete wiring instructions
   - Pin assignments
   - Component connections
   - Power distribution
   - Safety considerations

### 2. **HARDWARE_TESTING_PROCEDURE.md**
   - Step-by-step component testing
   - Integration testing
   - Troubleshooting guides
   - Test results template

### 3. **HARDWARE_BOM.md**
   - Complete bill of materials
   - Component specifications
   - Supplier recommendations
   - Cost estimates

### 4. **HARDWARE_QUICK_REFERENCE.md**
   - Quick pin reference
   - Common commands
   - Troubleshooting quick fixes

## Setup Workflow

### Phase 1: Planning & Procurement
1. Review BOM and select components
2. Order components from suppliers
3. Prepare tools and workspace
4. Review wiring guide

### Phase 2: Initial Assembly
1. Set up breadboard for testing
2. Wire ESP32-CAM base connections
3. Connect serial monitor
4. Flash test firmware
5. Verify basic functionality

### Phase 3: Component Testing
1. Test each component individually:
   - ESP32-CAM boot
   - Camera module
   - A7670 power and UART
   - A7670 network registration
   - IR sensor
   - Reed switch
   - Light sensor
   - Battery monitoring
   - LED status
   - Power management

2. Document test results
3. Fix any issues found

### Phase 4: Integration
1. Connect all components together
2. Run integration tests
3. Test mail detection flow
4. Test photo capture and upload
5. Test deep sleep and wake-up
6. Monitor power consumption

### Phase 5: Final Assembly
1. Design or select enclosure
2. Mount components securely
3. Route wires neatly
4. Seal weatherproof enclosure
5. Install in mailbox
6. Final system test

### Phase 6: Deployment
1. Install in mailbox
2. Configure WiFi (if using)
3. Verify cellular connection
4. Test mail detection
5. Monitor for 24-48 hours
6. Verify remote access

## Key Pin Assignments

| Component | GPIO | Notes |
|-----------|------|-------|
| A7670 Power | 33 | Changed from GPIO 4 (conflict with LED) |
| A7670 RX | 16 | UART2 |
| A7670 TX | 17 | UART2 |
| IR Sensor | 13 | Pull-down |
| Reed Switch | 12 | Pull-up |
| Light/Battery ADC | 14 | Shared pin |
| LED Status | 4 | Built-in flash LED |
| IR Power Control | 2 | Optional MOSFET |

## Critical Fixes Applied

### GPIO Pin Conflict Resolution
- **Issue**: GPIO 4 was used for both LED status and A7670 power control
- **Fix**: Changed A7670_POWER_PIN from GPIO 4 to GPIO 33
- **Files Modified**:
  - `esp32-firmware/src/main.cpp`
  - `esp32-firmware/src/a7670_cellular.h`

### Shared ADC Pin
- **Issue**: GPIO 14 used for both light sensor and battery monitoring
- **Solution**: Firmware reads them at different times (acceptable)

## Power Requirements

### Component Power Needs
- **ESP32-CAM**: 3.3V @ 200mA (active), 10µA (sleep)
- **A7670 Module**: 5V @ 50mA (idle), 2A (peak TX)
- **IR Sensor**: 3.3V @ 50µA
- **Total Active**: ~250mA @ 3.7V
- **Total Sleep**: ~10µA @ 3.7V

### Battery Sizing
- **Minimum**: 2000mAh (8 hours active operation)
- **Recommended**: 5000mAh (24+ hours with solar)
- **With Solar**: 2000mAh sufficient (solar charges during day)

## Testing Checklist

Before deployment, verify:
- [ ] All components wired correctly
- [ ] All components tested individually
- [ ] Integration tests pass
- [ ] Power consumption acceptable
- [ ] Deep sleep works correctly
- [ ] Wake-up on IR trigger works
- [ ] Camera captures photos
- [ ] Photos upload to server
- [ ] Cellular connection stable
- [ ] Battery monitoring accurate
- [ ] Enclosure weatherproof
- [ ] All connections secure

## Common Issues & Solutions

### ESP32 Won't Boot
- **Cause**: GPIO 0 is HIGH (download mode)
- **Solution**: Ensure GPIO 0 is LOW during normal operation

### A7670 Not Responding
- **Cause**: Power supply insufficient or UART connections wrong
- **Solution**: Verify 5V @ 2A supply, check TX/RX connections

### IR Sensor False Triggers
- **Cause**: Too sensitive or interference
- **Solution**: Adjust sensitivity, add focusing lens, verify wiring

### Battery Drains Quickly
- **Cause**: Deep sleep not working or power leaks
- **Solution**: Verify deep sleep code, check for power leaks

### No Cellular Network
- **Cause**: SIM card issue or wrong APN
- **Solution**: Verify SIM card, check APN settings in firmware

## Next Steps

1. **Review Documentation**
   - Read HARDWARE_WIRING_GUIDE.md thoroughly
   - Understand pin assignments
   - Review power requirements

2. **Order Components**
   - Use HARDWARE_BOM.md as reference
   - Order from recommended suppliers
   - Get spare components for testing

3. **Prepare Workspace**
   - Set up soldering station
   - Prepare multimeter
   - Organize components

4. **Begin Assembly**
   - Start with breadboard testing
   - Test each component individually
   - Follow testing procedures

5. **Integration & Deployment**
   - Connect all components
   - Run integration tests
   - Deploy to mailbox

## Support Resources

- **Wiring Guide**: `documentation/HARDWARE_WIRING_GUIDE.md`
- **Testing**: `documentation/HARDWARE_TESTING_PROCEDURE.md`
- **Components**: `documentation/HARDWARE_BOM.md`
- **Quick Reference**: `documentation/HARDWARE_QUICK_REFERENCE.md`
- **Firmware Code**: `esp32-firmware/src/`

## Success Criteria

Your hardware setup is complete when:
- ✅ All components wired and tested
- ✅ System boots and initializes correctly
- ✅ Mail detection triggers photo capture
- ✅ Photos upload to server successfully
- ✅ Deep sleep and wake-up work reliably
- ✅ Battery life meets requirements
- ✅ System operates in mailbox environment

Good luck with your hardware setup! 🚀


