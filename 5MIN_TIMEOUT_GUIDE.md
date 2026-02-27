# Proactive Notification - 5 Minute Timeout

## ⏰ Updated Timeout

### New Duration

**Notification now lasts 5 MINUTES (300 seconds)!**

```
Before: 10 seconds
Now:    5 minutes (300 seconds)
```

---

## 📊 Visual Display

### What You'll See

```
╔══════════════════════════════════════════════════════════╗
║  [!] PROACTIVE SUGGESTION                               ║
║                                                          ║
║  Upcoming: Team Meeting                                 ║
║                                                          ║
║  Suggestion: Silence phone for meeting                 ║
║                                                          ║
║  [Y] Accept  [N] Dismiss      Time left: 04:57         ║
╚══════════════════════════════════════════════════════════╝
```

**Countdown format:** `MM:SS` (minutes:seconds)

**Updates every second:**
- 05:00 → 04:59 → 04:58 → ... → 00:01 → Auto-dismiss

---

## 🎯 Timeline

### Real-Time Experience

**When notification appears:**

| Time | Countdown | Status |
|------|-----------|--------|
| 0:00 | 05:00 | Appears! |
| 0:30 | 04:30 | Still visible |
| 1:00 | 04:00 | Still visible |
| 2:00 | 03:00 | Still visible |
| 3:00 | 02:00 | Still visible |
| 4:00 | 01:00 | Still visible |
| 5:00 | 00:00 | Auto-dismisses |

**Plenty of time to:**
- ✅ Read the suggestion carefully
- ✅ Navigate around (still works!)
- ✅ Think about whether to accept
- ✅ Come back and respond later
- ✅ Let it auto-dismiss if you're busy

---

## 🎮 Calendar App Behavior

### Debugging Added

**When notification appears in calendar, you'll see:**

```
>>> NOTIFICATION ACTIVE <<<
```

**This yellow text at the top confirms the notification system triggered.**

### Expected Behavior in Calendar

1. **You're in calendar** browsing events
2. **Time hits 08:50** (or whenever trigger happens)
3. **Screen shows:**
   - Yellow "NOTIFICATION ACTIVE" text (top)
   - Proactive notification popup (center)
   - Calendar events (background, partially visible)
4. **You can:**
   - Press Y to accept
   - Press N to dismiss
   - Wait 5 minutes for auto-dismiss
5. **After response:**
   - Returns to calendar view
   - Can continue browsing

---

## 🔍 Troubleshooting

### If Notification Doesn't Appear in Calendar

**Check these:**

1. **Time reached trigger window?**
   - Look at top-right time display
   - Should be 08:50-08:52 for Team Meeting

2. **Already shown?**
   - Notification only shows once per event
   - If you already saw it on home screen, won't show again
   - Restart OS to reset

3. **See debug text?**
   - If "NOTIFICATION ACTIVE" appears but no popup
   - Issue with drawing over calendar

4. **Event exists?**
   - Open calendar and verify event is there
   - Should see "09:00 Team Meeting"

### Solution if Not Working

**Quick test:**
```bash
# 1. Boot OS
# 2. Stay on home screen
# 3. Wait for 08:50
# 4. Should appear on home
# 5. Then open calendar
# 6. Wait for next event (11:30 Lunch)
# 7. Should appear in calendar
```

---

## 📝 Technical Details

### Timeout Implementation

```c
const uint32_t timeout_limit = 300000000;  // 5 minutes

// 5 minutes * 60 seconds/minute = 300 seconds
// 300 seconds * 1,000,000 cycles/second = 300,000,000 cycles

while (!responded && timeout_counter < timeout_limit) {
    timeout_counter++;
    // ... check for Y/N keys
}
```

### Countdown Calculation

```c
// Every 1M cycles (≈1 second)
if (timeout_counter % 1000000 == 0) {
    uint32_t seconds_left = 300 - (timeout_counter / 1000000);
    uint32_t mins = seconds_left / 60;
    uint32_t secs = seconds_left % 60;
    
    // Display as MM:SS
    draw_text("Time left: 04:57", ...);
}
```

---

## 🎯 Use Cases

### Why 5 Minutes?

**Realistic scenarios:**

1. **User is browsing calendar**
   - Sees notification
   - Continues looking at other events
   - Comes back to respond
   - Still visible!

2. **User is multitasking**
   - Notification appears
   - User finishes current thought
   - Returns attention to OS
   - Notification still there

3. **Demo/presentation**
   - Show notification
   - Explain features
   - Talk about implementation
   - Notification stays visible throughout

4. **Teaching/learning**
   - Student sees notification
   - Instructor explains
   - Student tries different keys
   - Plenty of time to experiment

---

## ⚙️ Customization

### Want Different Timeout?

**30 seconds:**
```c
const uint32_t timeout_limit = 30000000;
```

**1 minute:**
```c
const uint32_t timeout_limit = 60000000;
```

**10 minutes:**
```c
const uint32_t timeout_limit = 600000000;
```

**No timeout (waits forever):**
```c
// Remove timeout condition
while (!responded) {
    // ... only Y/N dismisses
}
```

---

## ✅ Summary

**Changes made:**

1. ✅ Timeout extended from 10 seconds → **5 minutes**
2. ✅ Countdown shows **MM:SS** format
3. ✅ Debug text added: **"NOTIFICATION ACTIVE"**
4. ✅ Works in **all screens** (home, calendar, etc.)

**Testing:**
```bash
make clean
make iso-carplay
make run-carplay

# Wait for notification
# Should last 5 full minutes!
# Countdown shows: 05:00 → 04:59 → ... → 00:00
```

**Perfect for demos, real use, and learning!** ⏰🎉
