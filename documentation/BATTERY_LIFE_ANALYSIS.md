# Battery Life Analysis - 1800mAh Battery

## Battery Specifications

- **Capacity**: 1800mAh @ 3.7V nominal
- **Energy**: 1800mAh × 3.7V = 6.66 Wh
- **Voltage Range**: 3.0V (min) to 4.2V (max)
- **Nominal Voltage**: 3.7V (for calculations)

## Power Consumption Analysis

### ESP32-CAM Power States

| State | Current | Voltage | Power | Duration per Cycle |
|-------|---------|---------|-------|-------------------|
| **Deep Sleep** | 10µA | 3.3V | 0.033mW | Most of time |
| **Boot/Init** | 80mA | 3.3V | 264mW | 2-3 seconds |
| **WiFi Connect** | 80mA | 3.3V | 264mW | 5-10 seconds |
| **WiFi Connected** | 200mA | 3.3V | 660mW | 1-2 seconds |
| **Camera Init** | 240mA | 3.3V | 792mW | 1 second |
| **Photo Capture** | 240mA | 3.3V | 792mW | 1-2 seconds |
| **Photo Upload** | 200mA | 3.3V | 660mW | 3-5 seconds |
| **Return to Sleep** | 80mA | 3.3V | 264mW | <1 second |

### Typical Wake Cycle (Automatic - Every 2 Hours)

| Phase | Current | Duration | Energy (mWh) |
|-------|---------|----------|--------------|
| Boot/Init | 80mA | 3s | 0.22 |
| WiFi Connect | 80mA | 8s | 0.59 |
| WiFi Connected | 200mA | 1.5s | 0.33 |
| Camera Init | 240mA | 1s | 0.26 |
| Photo Capture | 240mA | 1.5s | 0.40 |
| Photo Upload | 200mA | 4s | 0.88 |
| Return to Sleep | 80mA | 0.5s | 0.04 |
| **Total Active** | | **19.5s** | **2.72 mWh** |
| **Deep Sleep** | 10µA | 7199.5s | 0.02 mWh |
| **Total per Cycle** | | **7200s (2h)** | **2.74 mWh** |

### Manual Trigger Cycle (Additional)

Same as automatic cycle, but triggered by user:
- **Energy per manual trigger**: 2.72 mWh
- **Duration**: ~20 seconds

## Battery Life Calculations

### Scenario 1: Free User (Automatic Only)

**Usage Pattern:**
- Automatic captures: 12 per day (every 2 hours)
- Manual triggers: 0 (free users don't use manual)

**Daily Energy Consumption:**
- 12 automatic cycles × 2.74 mWh = 32.88 mWh/day
- Deep sleep: 24 hours × 0.033mW = 0.79 mWh/day
- **Total**: 33.67 mWh/day

**Battery Life:**
- Battery capacity: 6660 mWh (1800mAh × 3.7V)
- Days: 6660 mWh ÷ 33.67 mWh/day = **197.8 days**
- **Approximately 6.6 months**

### Scenario 2: Free User (Automatic + 3 Manual Clicks/Day)

**Usage Pattern:**
- Automatic captures: 12 per day
- Manual triggers: 3 per day (maximum)

**Daily Energy Consumption:**
- 12 automatic cycles × 2.74 mWh = 32.88 mWh/day
- 3 manual triggers × 2.72 mWh = 8.16 mWh/day
- Deep sleep: 0.79 mWh/day
- **Total**: 41.83 mWh/day

**Battery Life:**
- Battery capacity: 6660 mWh
- Days: 6660 mWh ÷ 41.83 mWh/day = **159.1 days**
- **Approximately 5.3 months**

### Scenario 3: Premium User (Automatic + 10 Manual Clicks/Day)

**Usage Pattern:**
- Automatic captures: 12 per day
- Manual triggers: 10 per day (example)

**Daily Energy Consumption:**
- 12 automatic cycles × 2.74 mWh = 32.88 mWh/day
- 10 manual triggers × 2.72 mWh = 27.2 mWh/day
- Deep sleep: 0.79 mWh/day
- **Total**: 60.87 mWh/day

**Battery Life:**
- Battery capacity: 6660 mWh
- Days: 6660 mWh ÷ 60.87 mWh/day = **109.4 days**
- **Approximately 3.6 months**

### Scenario 4: Premium User (Automatic + 20 Manual Clicks/Day)

**Usage Pattern:**
- Automatic captures: 12 per day
- Manual triggers: 20 per day (heavy usage)

**Daily Energy Consumption:**
- 12 automatic cycles × 2.74 mWh = 32.88 mWh/day
- 20 manual triggers × 2.72 mWh = 54.4 mWh/day
- Deep sleep: 0.79 mWh/day
- **Total**: 88.07 mWh/day

**Battery Life:**
- Battery capacity: 6660 mWh
- Days: 6660 mWh ÷ 88.07 mWh/day = **75.6 days**
- **Approximately 2.5 months**

## Battery Life Summary Table

| User Type | Automatic/Day | Manual/Day | Energy/Day | Battery Life |
|-----------|---------------|------------|------------|--------------|
| **Free (auto only)** | 12 | 0 | 33.67 mWh | **6.6 months** |
| **Free (max manual)** | 12 | 3 | 41.83 mWh | **5.3 months** |
| **Premium (moderate)** | 12 | 10 | 60.87 mWh | **3.6 months** |
| **Premium (heavy)** | 12 | 20 | 88.07 mWh | **2.5 months** |

## Real-World Considerations

### Factors That Reduce Battery Life

1. **WiFi Connection Time**: Longer connection times increase energy
   - Poor signal: +5-10 seconds = +0.3-0.6 mWh per cycle
   - Impact: -10% to -20% battery life

2. **Upload Failures**: Retries consume extra energy
   - Each retry: +2.72 mWh
   - 10% failure rate: -5% battery life

3. **Temperature**: Cold reduces battery capacity
   - 0°C: -20% capacity
   - Impact: -20% battery life

4. **Battery Aging**: Capacity decreases over time
   - After 100 cycles: -10% capacity
   - Impact: Gradual reduction

5. **Voltage Drop**: Lower voltage at end of life
   - ESP32 may not function below 3.0V
   - Effective capacity: ~90% of rated

### Conservative Estimates (With Safety Margin)

| User Type | Theoretical | Conservative (80% efficiency) | Realistic Estimate |
|-----------|-------------|-------------------------------|-------------------|
| **Free (auto only)** | 6.6 months | 5.3 months | **4-5 months** |
| **Free (max manual)** | 5.3 months | 4.2 months | **3.5-4 months** |
| **Premium (moderate)** | 3.6 months | 2.9 months | **2.5-3 months** |
| **Premium (heavy)** | 2.5 months | 2.0 months | **1.5-2 months** |

## Optimization Strategies

### 1. Reduce WiFi Connection Time
- **Current**: 5-10 seconds
- **Optimized**: 3-5 seconds (better signal, saved credentials)
- **Savings**: ~0.3 mWh per cycle = +5% battery life

### 2. Disable Flash LED
- **Current**: LED on during capture (optional)
- **Optimized**: LED off
- **Savings**: ~0.05 mWh per cycle = +1% battery life

### 3. Reduce Photo Quality
- **Current**: High quality (50-100KB)
- **Optimized**: Medium quality (30-50KB)
- **Savings**: Faster upload = -1 second = +0.2 mWh per cycle = +3% battery life

### 4. Increase Sleep Interval
- **Current**: 2 hours
- **Optimized**: 3 hours (6 captures/day instead of 12)
- **Savings**: 50% fewer captures = **Double battery life**

### 5. Use Cellular Only When Needed
- **Current**: WiFi + Cellular fallback
- **Optimized**: WiFi only (cellular uses more power)
- **Savings**: If cellular not needed, significant savings

### 6. Solar Panel Integration
- **Panel**: 5V, 1W solar panel
- **Daily Energy**: 4 hours sun × 1W = 4 Wh/day
- **Battery Recharge**: 4 Wh ÷ 3.7V = 1081 mAh/day
- **Impact**: Can extend battery life indefinitely with adequate sun

## Recommended Configuration

### For Maximum Battery Life (Free Users)
- Automatic captures: Every 3 hours (8/day)
- Manual triggers: 3/day maximum
- WiFi only (no cellular)
- LED disabled
- Medium photo quality
- **Expected**: **6-7 months**

### For Balanced Usage (Premium Users)
- Automatic captures: Every 2 hours (12/day)
- Manual triggers: Unlimited
- WiFi with cellular fallback
- LED enabled for status
- High photo quality
- **Expected**: **3-4 months** (with moderate manual usage)

### With Solar Panel
- Any configuration above
- 5W solar panel (4+ hours sun/day)
- **Expected**: **Indefinite operation** (battery recharges daily)

## Battery Replacement Schedule

| User Type | Recommended Replacement |
|-----------|------------------------|
| **Free (auto only)** | Every 5 months |
| **Free (max manual)** | Every 4 months |
| **Premium (moderate)** | Every 3 months |
| **Premium (heavy)** | Every 2 months |
| **With Solar** | Check annually |

## Monitoring Recommendations

1. **Battery Voltage Monitoring**: Report voltage with each capture
2. **Low Battery Warning**: Alert when < 3.3V
3. **Usage Tracking**: Track manual clicks to estimate battery life
4. **User Notifications**: Warn users when battery is low

## Conclusion

With a **1800mAh battery**:
- **Free users** (automatic + 3 manual/day): **3.5-4 months**
- **Premium users** (automatic + 10 manual/day): **2.5-3 months**
- **With solar panel**: **Indefinite operation**

The system is highly efficient due to deep sleep mode, consuming minimal power between captures.


