# MiniOS Timing Reference - Updated

## ⏰ New Boot Timing (More Exploration Time!)

### Timeline Overview

```
08:30 AM - Boot MiniOS (Start)
  ↓
  [20 minutes to explore]
  ↓
08:50 AM - First proactive suggestion triggers
  ↓
09:00 AM - Team Meeting starts
```

---

## 📊 Detailed Timeline

### What You'll Experience

**Real-time sequence (with ~100x time acceleration):**

| Real Time | Simulated Time | Event |
|-----------|----------------|-------|
| 0:00 | 08:30 | **Boot** - Home screen appears |
| 0:05 | 08:31 | Navigate around, explore apps |
| 0:10 | 08:32 | Open calendar, browse events |
| 0:30 | 08:35 | Still exploring... |
| 1:00 | 08:40 | Check memory stats, settings |
| 1:30 | 08:45 | Navigate back to home |
| **2:00** | **08:50** | **🔔 FIRST NOTIFICATION!** |
| 2:01 | 08:51 | "Silence phone for Team Meeting" |
| 2:30 | 09:00 | Team Meeting starts |

**Result: ~2 minutes of real time before first notification!**

---

## 🎯 Proactive Trigger Windows

### Updated Settings

**Trigger Range:** 8-10 minutes before event

**Old behavior:**
```
5-10 minutes before → Too wide
Could trigger at 08:55, 08:54, 08:53... 
Unpredictable timing
```

**New behavior:**
```
8-10 minutes before → Narrower window
Triggers at 08:50-08:52 range
More predictable
```

---

## 📅 Event Schedule

### All Events with Trigger Times

| Event | Time | Proactive Trigger | Real Time After Boot |
|-------|------|-------------------|---------------------|
| **Team Meeting** | 09:00 | 08:50-08:52 | ~2 min |
| **Lunch Break** | 11:30 | 11:20-11:22 | ~5 min |
| **Project Work** | 14:00 | 13:50-13:52 | ~8 min |
| **Coffee Break** | 16:30 | 16:20-16:22 | ~12 min |

---

## 🕐 Time Progression Speed

### Current Settings

**Simulation speed:** ~100x real time
- 1 million CPU cycles ≈ 1 simulated minute
- On modern CPU: ~1-2 real seconds = 1 simulated minute

**Example progression:**
```
Real time:  0s   10s   20s   30s   60s   120s
Simulated:  8:30 8:31  8:32  8:33  8:35  8:40
```

---

## 🎮 Exploration Time

### What You Can Do Before First Notification

**~2 minutes of real time = plenty of time to:**

✅ Navigate home screen (W/A/S/D)
✅ Open calendar (Enter)
✅ Browse events (Up/Down)
✅ Go back to home (B)
✅ Navigate to different apps
✅ See time advancing in corner
✅ Get familiar with interface

**Then at ~2:00 real time:**
🔔 First proactive notification appears!

---

## ⚙️ Customization Options

### Want Even More Time?

**Option 1: Start Earlier**
```c
// In kernel_carplay.c:
g_ml.current_hour = 8;
g_ml.current_minute = 0;     // Start at 8:00 AM
g_ml.cycles = 480000000;     // 480 minutes from midnight
```
**Result:** 1 hour before first event = ~5 min real time

**Option 2: Move First Event Later**
```c
// In init_calendar():
g_events[0] = (CalendarEvent){10, 0, 60, "Team Meeting", 0, 1};
//                            ^^^^^ 10:00 AM instead of 9:00
```
**Result:** Start 8:30, event 10:00 = ~7 min real time

**Option 3: Slow Down Time**
```c
// In ml_update_context():
uint32_t minutes = (g_ml.cycles / 5000000) % (24 * 60);
//                                ^^^^^^^^^ 5M instead of 1M
```
**Result:** 5x slower = ~10 min real time before first notification

---

## 📍 Quick Reference

### Current Configuration

```
Start Time:       08:30 AM
First Event:      09:00 AM (Team Meeting)
Trigger Window:   8-10 minutes before
First Trigger:    08:50 AM
Real Time Delay:  ~2 minutes
```

### Benefits

✅ **Not rushed** - Time to explore interface
✅ **Predictable** - Notification at consistent time
✅ **Demo-friendly** - Can show features before notification
✅ **Natural flow** - Enough time to open calendar, browse, return

---

## 🚀 Try It Now

```bash
make clean
make iso-carplay
make run-carplay
```

**Experience:**
1. **0:00** - Boot, see home screen (08:30)
2. **0:10** - Navigate around, explore
3. **0:30** - Open calendar, browse events
4. **1:00** - Check out different screens
5. **2:00** - Time hits 08:50
6. **2:01** - 🔔 **Proactive notification appears!**

**Perfect timing - enough exploration, not too long!** ⏰
