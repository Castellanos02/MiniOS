# Proactive Notifications - Behavior Guide

## 📍 Where Notifications Appear

### ✅ NEW: Appear Everywhere (Global Notifications)

**Proactive notifications now appear on ALL screens!**

### Scenarios

#### Scenario 1: On Home Screen
```
┌─────────────────────────────────────────┐
│  MiniOS CarPlay          08:52         │
├─────────────────────────────────────────┤
│                                         │
│     [CAL]       [AI]                   │
│   Calendar   Suggester                  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ [!] PROACTIVE SUGGESTION         │  │  ← Popup appears!
│  │                                   │  │
│  │ Upcoming: Team Meeting            │  │
│  │ Suggestion: Silence phone         │  │
│  │ [Y] Accept  [N] Dismiss          │  │
│  └──────────────────────────────────┘  │
│                                         │
│     [MEM]       [SET]                  │
│    Memory    Settings                   │
│                                         │
└─────────────────────────────────────────┘
```

**Result:** Notification overlays home screen

---

#### Scenario 2: In Calendar App
```
┌─────────────────────────────────────────┐
│  08:52  Calendar - Today's Schedule    │
├─────────────────────────────────────────┤
│                                         │
│  09:00  Team Meeting         60 min    │
│  [  ]                                   │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ [!] PROACTIVE SUGGESTION         │  │  ← Popup appears!
│  │                                   │  │
│  │ Upcoming: Team Meeting            │  │
│  │ Suggestion: Silence phone         │  │
│  │ [Y] Accept  [N] Dismiss          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  11:30  Lunch Break          30 min    │
│  [  ]                                   │
└─────────────────────────────────────────┘
```

**Result:** 
- Notification overlays calendar
- After Y/N → Returns to calendar view
- Can continue browsing schedule

---

#### Scenario 3: Browsing Calendar → Notification Appears
```
User viewing calendar:
  → 08:50: Looking at scheduled events
  → 08:52: Popup appears!
  → User presses 'Y'
  → Returns to calendar (can continue browsing)
```

---

## 🎯 Why This Design?

### Global Notifications are Better

**Proactive = Interrupts You (in a good way!)**

✅ **Don't miss important suggestions**
- If you're in calendar looking at lunch plans
- System still reminds you about upcoming meeting
- You get the notification regardless of what you're doing

✅ **Context preserved**
- Notification appears
- You respond (Y/N)
- Return to exactly what you were doing

✅ **Realistic behavior**
- Like phone notifications (appear everywhere)
- Like iOS/Android alerts (modal popups)
- Like CarPlay notifications (overlay current screen)

---

## 🔄 User Flow Examples

### Example 1: Home → Notification → Home
```
1. User on home screen
2. Notification appears (08:52)
3. User presses 'Y'
4. Confirmation shown
5. Returns to home screen
```

### Example 2: Calendar → Notification → Calendar
```
1. User browsing calendar
2. Notification appears (08:52)
3. User presses 'N' (dismisses)
4. Returns to calendar view
5. Continues browsing
```

### Example 3: Calendar → Add AI Suggestion → Notification
```
1. User in calendar
2. Presses 'A' (add AI suggestion)
3. New event added
4. Still in calendar
5. Time advances to 08:52
6. Proactive notification appears!
7. User responds
8. Returns to calendar (sees new event)
```

---

## ⏱️ Timing Example

### Real-Time Sequence
```
08:50:00 - Boot MiniOS, home screen
08:50:10 - User navigates to Calendar (Enter)
08:50:15 - User scrolling through events (Up/Down)
08:50:30 - Time advances to 08:52
08:50:30 - PROACTIVE NOTIFICATION APPEARS
           (overlays calendar view)
08:50:35 - User presses 'Y'
08:50:36 - "Suggestion accepted!"
08:50:38 - Returns to calendar view
08:50:40 - User continues scrolling
```

**Key point:** Notification appeared while in calendar, not just on home!

---

## 🎨 Visual Hierarchy

### Notification Priority

**Highest → Lowest:**
1. **Proactive Notification** (overlays everything)
2. Calendar/Home/Settings screen
3. Background

**Why?**
- Proactive suggestions are time-sensitive
- More important than what you're currently viewing
- Like urgent phone notifications

---

## 🛠️ Technical Implementation

### How It Works

```c
// Main loop checks ALWAYS (not just on home screen)
if (cycle_count % 10000 == 0) {
    // Check for proactive events
    event_idx = check_for_proactive_event(...);
    
    if (event_idx >= 0) {
        // Remember current screen
        previous_screen = current_screen;
        
        // Show notification (overlays)
        draw_proactive_notification(...);
        
        // Wait for response
        // ...
        
        // Restore previous screen
        if (previous_screen == SCREEN_HOME) {
            draw_home_screen(...);
        } else if (previous_screen == SCREEN_CALENDAR) {
            draw_calendar_app(...);
        }
    }
}
```

### Screen Restoration

**Smart return:**
- Remembers which screen you were on
- Redraws that screen after notification
- Preserves scroll position (calendar)
- Preserves app selection (home)

---

## 📊 Comparison: Old vs New

### OLD (Home Only)
```
User on home screen:
  ✅ Gets notification
  
User in calendar:
  ❌ Misses notification
  ❌ Has to go back to home to see it
  ❌ Might forget about upcoming event
```

### NEW (Global)
```
User on home screen:
  ✅ Gets notification
  
User in calendar:
  ✅ Gets notification
  ✅ Can respond immediately
  ✅ Returns to calendar after
  ✅ Won't miss important suggestions
```

---

## 💡 Future Enhancements

### Notification Queue
```
Multiple events approaching:
- Show notifications one at a time
- Queue additional notifications
- Don't spam user
```

### Smart Timing
```
If user is actively typing/interacting:
- Delay notification slightly
- Wait for pause in activity
- Then show notification
```

### Notification History
```
Missed a notification?
- Check notification center
- See past suggestions
- Re-accept if needed
```

---

## ✅ Summary

**Current Behavior:**

✅ Proactive notifications appear **everywhere**
✅ Home screen → notification → home screen
✅ Calendar → notification → calendar
✅ Any screen → notification → same screen
✅ Never miss time-sensitive suggestions
✅ Context preserved after response

**This matches real-world OS behavior (iOS, Android, Windows) where notifications are global and interrupt what you're doing!**

---

## 🚀 Try It Now

```bash
make clean
make iso-carplay
make run-carplay
```

**Test sequence:**
1. Boot → See home screen (08:50)
2. Press Enter → Open calendar
3. Wait ~10-20 seconds
4. **Notification appears IN calendar!**
5. Press Y or N
6. **Returns to calendar** (not home)

Perfect proactive behavior! 🎉
